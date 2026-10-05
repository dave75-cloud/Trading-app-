#!/usr/bin/env python3
"""Pure development-only kernel for RND-0060B."""
from __future__ import annotations

import math
from datetime import datetime, timezone

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
M5_SECONDS = 300
LOOKBACK_BARS = 6
DISPLACEMENT_THRESHOLD = 0.0020
HOLD_BARS = 3


class RND0060BError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060BError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060BError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _price(value, role):
    _req(not isinstance(value, bool), f"{role}: positive finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060BError(f"{role}: positive finite number required") from exc
    _req(math.isfinite(out) and out > 0, f"{role}: positive finite number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close"}
    parsed = []
    previous = None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(previous is None or dt > previous, "rows: timestamps must be unique and ordered")
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        _req(bid <= mid <= ask, "bid/mid/ask ordering invalid")
        parsed.append({"dt": dt, "bid": bid, "ask": ask, "mid": mid})
        previous = dt
    return parsed


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


def evaluate_symbol(symbol, rows):
    _req(symbol in SYMBOLS, "unsupported symbol")
    parsed = validate_rows(rows)
    start_hour, end_hour = SESSIONS[symbol]

    trades = []
    events = []
    marks = []
    signaled_days = set()
    pending = None
    active = None
    held = 0
    gap_count = 0
    previous_position_dt = None

    for i, bar in enumerate(parsed):
        dt = bar["dt"]
        day = dt.date()
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Pending signals must execute on the immediately following contiguous
        # eligible session bar; otherwise they are cancelled and not retried.
        if pending is not None:
            delta = int((dt - pending["signal_dt"]).total_seconds())
            eligible = dt.weekday() < 5 and start_hour <= dt.hour < end_hour
            if delta == M5_SECONDS and eligible:
                side = pending["side"]
                entry_exec = bar["ask"] if side == 1 else bar["bid"]
                active = {
                    "side": side,
                    "entry_dt": dt,
                    "entry_exec": entry_exec,
                    "entry_mid": bar["mid"],
                }
                held = 0
                gap_count = 0
                previous_position_dt = dt
                events.append({
                    "event_type": "ENTRY",
                    "timestamp": ts,
                    "side_value": side,
                    "execution_price": entry_exec,
                })
                marks.append({
                    "symbol": symbol,
                    "timestamp": ts,
                    "position": side,
                    "mark_return": 0.0,
                })
                pending = None
                continue
            events.append({
                "event_type": "PENDING_SIGNAL_CANCELLED",
                "timestamp": ts,
                "reason": "OBSERVATION_DISCONTINUITY_OR_INELIGIBLE_ENTRY",
            })
            pending = None

        # Existing economic positions survive gaps; only genuine observed bars
        # after the entry bar count toward the fixed three-bar hold.
        if active is not None:
            delta = int((dt - previous_position_dt).total_seconds())
            if delta != M5_SECONDS:
                gap_count += 1
                events.append({
                    "event_type": "GAP_DURING_POSITION",
                    "previous_timestamp": previous_position_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": ts,
                })
            held += 1
            previous_position_dt = dt
            mark_exec = bar["bid"] if active["side"] == 1 else bar["ask"]
            if active["side"] == 1:
                mark_return = (mark_exec - active["entry_exec"]) / active["entry_exec"]
            else:
                mark_return = (active["entry_exec"] - mark_exec) / active["entry_exec"]

            if held == HOLD_BARS:
                exit_exec = bar["bid"] if active["side"] == 1 else bar["ask"]
                gross, net = _trade_return(
                    active["side"], active["entry_exec"], exit_exec,
                    active["entry_mid"], bar["mid"],
                )
                trade = {
                    "symbol": symbol,
                    "side": "long" if active["side"] == 1 else "short",
                    "entry_timestamp": active["entry_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "exit_timestamp": ts,
                    "holding_bars": held,
                    "gap_exposure_count": gap_count,
                    "entry_execution_price": active["entry_exec"],
                    "exit_execution_price": exit_exec,
                    "entry_mid_price": active["entry_mid"],
                    "exit_mid_price": bar["mid"],
                    "gross_return": gross,
                    "net_return": net,
                    "execution_cost_drag": gross - net,
                    "exit_year": dt.year,
                }
                trades.append(trade)
                events.append({"event_type": "EXIT", "timestamp": ts, "net_return": net})
                active = None
                held = 0
                gap_count = 0
                previous_position_dt = None
                marks.append({"symbol": symbol, "timestamp": ts, "position": 0, "mark_return": None})
                continue

            marks.append({
                "symbol": symbol,
                "timestamp": ts,
                "position": active["side"],
                "mark_return": mark_return,
            })
            continue

        marks.append({"symbol": symbol, "timestamp": ts, "position": 0, "mark_return": None})

        if dt.weekday() >= 5 or not (start_hour <= dt.hour < end_hour):
            continue
        if day in signaled_days or i < LOOKBACK_BARS:
            continue

        anchor_index = i - LOOKBACK_BARS
        contiguous = all(
            int((parsed[j]["dt"] - parsed[j - 1]["dt"]).total_seconds()) == M5_SECONDS
            for j in range(anchor_index + 1, i + 1)
        )
        if not contiguous:
            continue

        anchor = parsed[anchor_index]
        displacement = bar["mid"] / anchor["mid"] - 1.0
        side = -1 if displacement >= DISPLACEMENT_THRESHOLD else (1 if displacement <= -DISPLACEMENT_THRESHOLD else 0)
        if side == 0:
            continue

        signaled_days.add(day)
        pending = {"side": side, "signal_dt": dt}
        events.append({
            "event_type": "DISPLACEMENT_SIGNAL",
            "timestamp": ts,
            "displacement": displacement,
            "side_value": side,
        })

    if active is not None:
        events.append({
            "event_type": "RIGHT_CENSORED",
            "timestamp": active["entry_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    if pending is not None:
        events.append({
            "event_type": "PENDING_SIGNAL_CENSORED_END_OF_SAMPLE",
            "timestamp": pending["signal_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    net_returns = [trade["net_return"] for trade in trades]
    gross_returns = [trade["gross_return"] for trade in trades]
    net_equity, max_dd = _max_drawdown(net_returns)
    gross_equity, _ = _max_drawdown(gross_returns)
    annual = {year: 0.0 for year in sorted(AUTHORIZED_YEARS)}
    for trade in trades:
        annual[trade["exit_year"]] += trade["net_return"]

    return {
        "symbol": symbol,
        "trades": trades,
        "events": events,
        "marks": marks,
        "completed_trade_count": len(trades),
        "trade_count": len(trades),
        "terminal_net_equity": net_equity,
        "terminal_gross_equity": gross_equity,
        "realized_net_sum": sum(net_returns),
        "max_drawdown": max_dd,
        "execution_cost_drag": sum(t["execution_cost_drag"] for t in trades),
        "annual_realized_net": annual,
        "development_only": True,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
