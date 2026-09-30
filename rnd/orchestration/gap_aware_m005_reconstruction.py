#!/usr/bin/env python3
"""Pure-local gap-aware fixed-M005 reconstruction for RND-0034.

No network access, file writes, strategy search, portfolio sizing, broker
access, promotion authority or capital authority.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019})
SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}
FAST = 20
SLOW = 50
VOL_WINDOW = 12
VOL_THRESHOLD = 0.0005
MIN_HOLD_BARS = 3
M5_SECONDS = 300


class GapAwareM005Error(ValueError):
    pass


def _utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GapAwareM005Error("timestamp must be UTC ending Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GapAwareM005Error("invalid timestamp") from exc
    if int(dt.timestamp()) % M5_SECONDS:
        raise GapAwareM005Error("timestamp off M5 grid")
    if dt.year not in AUTHORIZED_YEARS:
        raise GapAwareM005Error("strategy evaluation outside 2015-2019 prohibited")
    return dt


def _price(value, role):
    if isinstance(value, bool):
        raise GapAwareM005Error(f"{role}: positive finite price required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise GapAwareM005Error(f"{role}: positive finite price required") from exc
    if not math.isfinite(x) or x <= 0:
        raise GapAwareM005Error(f"{role}: positive finite price required")
    return x


def validate_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise GapAwareM005Error("rows: non-empty list required")
    out = []
    seen = set()
    previous = None
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise GapAwareM005Error(f"rows[{i}]: mapping required")
        required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close"}
        if not required.issubset(row):
            raise GapAwareM005Error(f"rows[{i}]: execution fields missing")
        if row["complete"] is not True:
            raise GapAwareM005Error(f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        if dt in seen:
            raise GapAwareM005Error("rows: duplicate timestamp")
        if previous is not None and dt <= previous:
            raise GapAwareM005Error("rows: timestamps out of order")
        seen.add(dt)
        previous = dt
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        if bid > ask or not (bid <= mid <= ask):
            raise GapAwareM005Error("rows: bid/mid/ask ordering invalid")
        out.append((dt, bid, ask, mid))
    return out


def population_std(values):
    if not isinstance(values, list) or not values:
        raise GapAwareM005Error("population_std: non-empty list required")
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _signal(symbol, closes, returns, dt):
    if len(closes) < SLOW or len(returns) < VOL_WINDOW:
        return None
    fast = sum(closes[-FAST:]) / FAST
    slow = sum(closes[-SLOW:]) / SLOW
    vol = population_std(returns[-VOL_WINDOW:])
    start, end = SESSIONS[symbol]
    in_session = dt.weekday() < 5 and start <= dt.hour < end
    if not in_session or vol < VOL_THRESHOLD:
        return 0
    if fast > slow:
        return 1
    if fast < slow:
        return -1
    return 0


def _trade_return(side, entry_exec, exit_exec, entry_mid, exit_mid):
    if side == 1:
        gross = (exit_mid - entry_mid) / entry_mid
        net = (exit_exec - entry_exec) / entry_exec
    else:
        gross = (entry_mid - exit_mid) / entry_mid
        net = (entry_exec - exit_exec) / entry_exec
    return gross, net


def _max_drawdown(returns):
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
    return equity, max_dd



def concurrent_unit_normalized_marks(per_symbol):
    """Time-align per-pair percentage marks without capital sizing.

    Each active pair contributes its own executable return since entry with
    fixed unit weight 1.0. The aggregate is the arithmetic sum, an accounting
    diagnostic only; it is not account-currency P&L or an allocation rule.
    """
    if set(per_symbol) != set(SYMBOLS):
        raise GapAwareM005Error("concurrent marks require exactly the four M005 symbols")
    by_ts = {}
    for symbol in SYMBOLS:
        value = per_symbol[symbol]
        for mark in value.get("marks", []):
            ts = mark["timestamp"]
            slot = by_ts.setdefault(ts, {})
            if symbol in slot:
                raise GapAwareM005Error("duplicate symbol mark at timestamp")
            slot[symbol] = mark

    out = []
    latest = {symbol: None for symbol in SYMBOLS}
    for ts in sorted(by_ts):
        for symbol, mark in by_ts[ts].items():
            latest[symbol] = mark
        active = {}
        aggregate = 0.0
        for symbol in SYMBOLS:
            mark = latest[symbol]
            if mark is None or mark["position"] == 0 or mark["mark_return"] is None:
                continue
            active[symbol] = {
                "position": mark["position"],
                "mark_return": mark["mark_return"],
                "source_timestamp": mark["timestamp"],
            }
            aggregate += mark["mark_return"]
        out.append({
            "timestamp": ts,
            "active_pair_count": len(active),
            "active_pairs": active,
            "unit_normalized_return_sum": aggregate,
        })
    return {
        "normalization": "FIXED_ONE_UNIT_RETURN_PER_ACTIVE_PAIR",
        "account_currency_pnl": False,
        "capital_allocation": False,
        "portfolio_sizing": False,
        "marks": out,
    }

def reconstruct_pair(symbol, rows):
    if symbol not in SYMBOLS:
        raise GapAwareM005Error("unsupported symbol")
    parsed = validate_rows(rows)

    closes = []
    returns = []
    previous_dt = None
    previous_mid = None
    previous_raw = None
    episode = 0
    gaps = []
    trades = []
    censored = []
    events = []
    marks = []

    position = 0
    bars_held = 0
    entry = None

    def reset_strategy_state():
        """Reset observation-dependent strategy state, never economic exposure."""
        nonlocal closes, returns, previous_mid, previous_raw, episode
        closes = []
        returns = []
        previous_mid = None
        previous_raw = None
        episode += 1

    def open_trade(side, dt, bid, ask, mid):
        return {
            "symbol": symbol,
            "side": "long" if side == 1 else "short",
            "side_value": side,
            "entry_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": ask if side == 1 else bid,
            "entry_mid_price": mid,
            "episode": episode,
            "gap_exposure_count": 0,
            "gap_elapsed_seconds": 0,
        }

    def complete_trade(current, dt, bid, ask, mid, held):
        side = current["side_value"]
        exit_exec = bid if side == 1 else ask
        gross, net = _trade_return(
            side,
            current["entry_execution_price"],
            exit_exec,
            current["entry_mid_price"],
            mid,
        )
        return {
            "symbol": symbol,
            "side": current["side"],
            "entry_timestamp": current["entry_timestamp"],
            "exit_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": current["entry_execution_price"],
            "exit_execution_price": exit_exec,
            "entry_mid_price": current["entry_mid_price"],
            "exit_mid_price": mid,
            "gross_return": gross,
            "net_return": net,
            "execution_cost_drag": gross - net,
            "holding_bars": held,
            "elapsed_seconds": int((dt - datetime.fromisoformat(current["entry_timestamp"][:-1] + "+00:00")).total_seconds()),
            "gap_exposure_count": current.get("gap_exposure_count", 0),
            "gap_elapsed_seconds": current.get("gap_elapsed_seconds", 0),
            "gap_exposed": current.get("gap_exposure_count", 0) > 0,
            "exit_year": dt.year,
            "episode": current["episode"],
            "status": "COMPLETE",
        }

    reset_strategy_state()

    for dt, bid, ask, mid in parsed:
        if previous_dt is not None:
            delta = int((dt - previous_dt).total_seconds())
            if delta != M5_SECONDS:
                gap_event = {
                    "symbol": symbol,
                    "previous_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "elapsed_seconds": delta,
                    "position_was_open": position != 0,
                }
                gaps.append(gap_event)
                events.append({"event_type": "GAP", **gap_event})
                if previous_raw is not None:
                    events.append({
                        "event_type": "PENDING_SIGNAL_CANCELLED",
                        "symbol": symbol,
                        "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "pending_signal": previous_raw,
                        "reason": "OBSERVATION_DISCONTINUITY",
                    })
                if position != 0 and entry is not None:
                    entry["gap_exposure_count"] = entry.get("gap_exposure_count", 0) + 1
                    entry["gap_elapsed_seconds"] = entry.get("gap_elapsed_seconds", 0) + delta
                reset_strategy_state()
                events.append({
                    "event_type": "STRATEGY_RESET",
                    "symbol": symbol,
                    "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "reason": "OBSERVATION_DISCONTINUITY",
                    "portfolio_position": position,
                })

        if previous_mid is not None:
            returns.append(mid / previous_mid - 1.0)
        closes.append(mid)

        raw = _signal(symbol, closes, returns, dt)
        desired = previous_raw
        previous_raw = raw

        if raw is not None:
            events.append({
                "event_type": "RAW_SIGNAL",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal": raw,
            })
        if desired is not None:
            events.append({
                "event_type": "DELAYED_SIGNAL",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal": desired,
            })

        # Missing nominal bars never count. A surviving position accrues one
        # holding bar only for each genuine observed candle.
        if position != 0:
            bars_held += 1

        if position == 0 and desired is not None and desired != 0:
            position = desired
            bars_held = 0
            entry = open_trade(position, dt, bid, ask, mid)
            events.append({
                "event_type": "ENTRY",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "side_value": position,
                "execution_price": entry["entry_execution_price"],
            })
        elif position != 0 and desired is not None and desired == 0 and bars_held >= MIN_HOLD_BARS:
            completed = complete_trade(entry, dt, bid, ask, mid, bars_held)
            trades.append(completed)
            events.append({
                "event_type": "EXIT",
                "symbol": symbol,
                "timestamp": completed["exit_timestamp"],
                "side_value": entry["side_value"],
                "execution_price": completed["exit_execution_price"],
                "net_return": completed["net_return"],
            })
            position = 0
            bars_held = 0
            entry = None
        elif position != 0 and desired is not None and desired == -position and bars_held >= MIN_HOLD_BARS:
            completed = complete_trade(entry, dt, bid, ask, mid, bars_held)
            trades.append(completed)
            events.append({
                "event_type": "EXIT",
                "symbol": symbol,
                "timestamp": completed["exit_timestamp"],
                "side_value": entry["side_value"],
                "execution_price": completed["exit_execution_price"],
                "net_return": completed["net_return"],
            })
            position = desired
            bars_held = 0
            entry = open_trade(position, dt, bid, ask, mid)
            events.append({
                "event_type": "ENTRY",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "side_value": position,
                "execution_price": entry["entry_execution_price"],
            })

        mark_return = None
        if position != 0 and entry is not None:
            mark_exec = bid if position == 1 else ask
            if position == 1:
                mark_return = (mark_exec - entry["entry_execution_price"]) / entry["entry_execution_price"]
            else:
                mark_return = (entry["entry_execution_price"] - mark_exec) / entry["entry_execution_price"]
        marks.append({
            "symbol": symbol,
            "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "position": position,
            "mark_return": mark_return,
            "strategy_signal_available": raw is not None,
        })

        previous_dt = dt
        previous_mid = mid

    if position != 0 and entry is not None:
        censored.append({
            "symbol": symbol,
            "side": entry["side"],
            "entry_timestamp": entry["entry_timestamp"],
            "last_observed_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "next_observed_timestamp": None,
            "status": "RIGHT_CENSORED_END_OF_SAMPLE",
            "episode": entry["episode"],
            "gap_exposure_count": entry.get("gap_exposure_count", 0),
            "gap_elapsed_seconds": entry.get("gap_elapsed_seconds", 0),
        })

    net_returns = [x["net_return"] for x in trades]
    gross_returns = [x["gross_return"] for x in trades]
    net_equity, net_dd = _max_drawdown(net_returns)
    gross_equity, gross_dd = _max_drawdown(gross_returns)
    wins = sum(1 for x in net_returns if x > 0)
    by_year = {}
    for trade in trades:
        key = str(trade["exit_year"])
        y = by_year.setdefault(key, {"trades": 0, "net_return_sum": 0.0, "cost_drag_sum": 0.0})
        y["trades"] += 1
        y["net_return_sum"] += trade["net_return"]
        y["cost_drag_sum"] += trade["execution_cost_drag"]

    return {
        "contract_version": "RND-0034-gap-aware-m005-v0.1",
        "symbol": symbol,
        "authorized_years": sorted(AUTHORIZED_YEARS),
        "fixed_trial_count": 1,
        "row_count": len(parsed),
        "contiguous_episode_count": episode,
        "gap_count": len(gaps),
        "completed_trade_count": len(trades),
        "censored_trade_count": len(censored),
        "censoring_rate": (
            len(censored) / (len(trades) + len(censored))
            if trades or censored else 0.0
        ),
        "net_hit_rate": wins / len(trades) if trades else None,
        "completed_trade_net_equity_index": net_equity,
        "completed_trade_net_max_drawdown": net_dd,
        "completed_trade_gross_equity_index": gross_equity,
        "completed_trade_gross_max_drawdown": gross_dd,
        "total_execution_cost_drag": sum(x["execution_cost_drag"] for x in trades),
        "trades": trades,
        "censored_trades": censored,
        "gaps": gaps,
        "events": events,
        "marks": marks,
        "event_reconciliation": {
            "entry_events": sum(1 for x in events if x["event_type"] == "ENTRY"),
            "exit_events": sum(1 for x in events if x["event_type"] == "EXIT"),
            "gap_events": sum(1 for x in events if x["event_type"] == "GAP"),
            "strategy_reset_events": sum(1 for x in events if x["event_type"] == "STRATEGY_RESET"),
            "raw_signal_events": sum(1 for x in events if x["event_type"] == "RAW_SIGNAL"),
            "delayed_signal_events": sum(1 for x in events if x["event_type"] == "DELAYED_SIGNAL"),
            "pending_signal_cancel_events": sum(
                1 for x in events if x["event_type"] == "PENDING_SIGNAL_CANCELLED"
            ),
        },
        "by_exit_year": by_year,
        "authority": {
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_review_required": True,
        },
    }
