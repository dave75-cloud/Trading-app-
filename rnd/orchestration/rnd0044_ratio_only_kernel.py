#!/usr/bin/env python3
"""RND-0044 isolated ratio-only development research kernel.

Preserves frozen M005 mechanics while replacing the legacy absolute-volatility
entry floor with the already-predeclared signal-to-friction ratio ladder.
Pure local computation only. Full 2015-2020 development outcomes remain
unauthorized until a separate human authorization exists.
"""
from __future__ import annotations

import math
from datetime import datetime

import gap_aware_m005_reconstruction as frozen

SYMBOLS = frozen.SYMBOLS
SESSIONS = frozen.SESSIONS
FAST = frozen.FAST
SLOW = frozen.SLOW
VOL_WINDOW = frozen.VOL_WINDOW
MIN_HOLD_BARS = frozen.MIN_HOLD_BARS
M5_SECONDS = frozen.M5_SECONDS
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
AUTHORIZED_ARMS = {"Q001": 3.0, "Q002": 5.0, "Q003": 8.0}


class RND0044KernelError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0044KernelError(message)


def _utc(value):
    _require(isinstance(value, str) and value.endswith("Z"), "timestamp must be UTC ending Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0044KernelError("invalid timestamp") from exc
    _require(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _require(dt.year in AUTHORIZED_YEARS, "RND-0044 evaluation outside development years prohibited")
    return dt


def _price(value, role):
    _require(not isinstance(value, bool), f"{role}: positive finite price required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0044KernelError(f"{role}: positive finite price required") from exc
    _require(math.isfinite(x) and x > 0, f"{role}: positive finite price required")
    return x


def validate_rows(rows):
    _require(isinstance(rows, list) and rows, "rows: non-empty list required")
    out, seen, previous = [], set(), None
    for i, row in enumerate(rows):
        _require(isinstance(row, dict), f"rows[{i}]: mapping required")
        required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close"}
        _require(required.issubset(row), f"rows[{i}]: execution fields missing")
        _require(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _require(dt not in seen, "rows: duplicate timestamp")
        _require(previous is None or dt > previous, "rows: timestamps out of order")
        seen.add(dt)
        previous = dt
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        _require(bid <= mid <= ask, "rows: bid/mid/ask ordering invalid")
        out.append((dt, bid, ask, mid))
    return out


def signal_to_friction_ratio(returns, bid, ask, mid):
    _require(isinstance(returns, list) and len(returns) >= VOL_WINDOW, "ratio: 12 contiguous returns required")
    relative_spread = (ask - bid) / mid
    _require(math.isfinite(relative_spread) and relative_spread > 0, "ratio: positive relative spread required")
    sigma = frozen.population_std(returns[-VOL_WINDOW:])
    ratio = sigma / relative_spread
    _require(math.isfinite(ratio) and ratio >= 0, "ratio: finite nonnegative value required")
    return {"sigma12_mid_return": sigma, "relative_spread": relative_spread, "signal_to_friction": ratio}


def raw_signal(symbol, closes, returns, dt, bid, ask, mid, arm):
    """Return frozen MA/session signal plus ratio-only entry eligibility.

    Unlike RND-0043, there is deliberately no absolute volatility floor.
    Ratio eligibility applies only to opening a new position after the frozen
    one-observation delay; it never manufactures an exit.
    """
    _require(symbol in SYMBOLS, "unsupported symbol")
    _require(arm in AUTHORIZED_ARMS, "arm outside predeclared RND-0044 set")
    if len(closes) < SLOW or len(returns) < VOL_WINDOW:
        return None, True, None
    start, end = SESSIONS[symbol]
    in_session = dt.weekday() < 5 and start <= dt.hour < end
    if not in_session:
        return 0, True, None
    fast = sum(closes[-FAST:]) / FAST
    slow = sum(closes[-SLOW:]) / SLOW
    ratio = signal_to_friction_ratio(returns, bid, ask, mid)
    eligible = ratio["signal_to_friction"] >= AUTHORIZED_ARMS[arm]
    if fast > slow:
        return 1, eligible, ratio
    if fast < slow:
        return -1, eligible, ratio
    return 0, True, ratio


def reconstruct_pair(symbol, rows, arm):
    _require(symbol in SYMBOLS, "unsupported symbol")
    _require(arm in AUTHORIZED_ARMS, "arm outside predeclared RND-0044 set")
    parsed = validate_rows(rows)
    closes, returns, gaps, trades, censored, marks = [], [], [], [], [], []
    previous_dt = previous_mid = previous_raw = None
    previous_entry_eligible = True
    previous_ratio = None
    episode = 0
    position = 0
    bars_held = 0
    entry = None
    rejected_entry_signal_count = 0
    actual_entry_ratios = []

    def reset_state():
        nonlocal closes, returns, previous_mid, previous_raw, previous_entry_eligible, previous_ratio, episode
        closes = []
        returns = []
        previous_mid = None
        previous_raw = None
        previous_entry_eligible = True
        previous_ratio = None
        episode += 1

    def open_trade(side, dt, bid, ask, mid, entry_ratio):
        if entry_ratio is not None:
            actual_entry_ratios.append(float(entry_ratio["signal_to_friction"]))
        return {
            "symbol": symbol,
            "side": "long" if side == 1 else "short",
            "side_value": side,
            "entry_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": ask if side == 1 else bid,
            "entry_mid_price": mid,
            "entry_signal_to_friction": None if entry_ratio is None else float(entry_ratio["signal_to_friction"]),
            "episode": episode,
            "gap_exposure_count": 0,
            "gap_elapsed_seconds": 0,
        }

    def complete_trade(current, dt, bid, ask, mid, held):
        side = current["side_value"]
        exit_exec = bid if side == 1 else ask
        gross, net = frozen._trade_return(side, current["entry_execution_price"], exit_exec, current["entry_mid_price"], mid)
        return {
            "symbol": symbol,
            "side": current["side"],
            "entry_timestamp": current["entry_timestamp"],
            "exit_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": current["entry_execution_price"],
            "exit_execution_price": exit_exec,
            "entry_mid_price": current["entry_mid_price"],
            "exit_mid_price": mid,
            "entry_signal_to_friction": current["entry_signal_to_friction"],
            "gross_return": gross,
            "net_return": net,
            "execution_cost_drag": gross - net,
            "holding_bars": held,
            "gap_exposure_count": current.get("gap_exposure_count", 0),
            "gap_elapsed_seconds": current.get("gap_elapsed_seconds", 0),
            "gap_exposed": current.get("gap_exposure_count", 0) > 0,
            "exit_year": dt.year,
            "episode": current["episode"],
            "status": "COMPLETE",
        }

    reset_state()
    for dt, bid, ask, mid in parsed:
        if previous_dt is not None:
            delta = int((dt - previous_dt).total_seconds())
            if delta != M5_SECONDS:
                gaps.append({
                    "symbol": symbol,
                    "previous_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "elapsed_seconds": delta,
                    "position_was_open": position != 0,
                })
                if position != 0 and entry is not None:
                    entry["gap_exposure_count"] += 1
                    entry["gap_elapsed_seconds"] += delta
                reset_state()

        if previous_mid is not None:
            returns.append(mid / previous_mid - 1.0)
        closes.append(mid)

        raw, entry_eligible, ratio = raw_signal(symbol, closes, returns, dt, bid, ask, mid, arm)
        desired = previous_raw
        desired_entry_eligible = previous_entry_eligible
        desired_ratio = previous_ratio
        previous_raw = raw
        previous_entry_eligible = entry_eligible
        previous_ratio = ratio

        if raw is not None and raw != 0 and not entry_eligible:
            rejected_entry_signal_count += 1

        if position != 0:
            bars_held += 1

        if position == 0 and desired is not None and desired != 0 and desired_entry_eligible:
            position = desired
            bars_held = 0
            entry = open_trade(position, dt, bid, ask, mid, desired_ratio)
        elif position != 0 and desired is not None and desired == 0 and bars_held >= MIN_HOLD_BARS:
            trades.append(complete_trade(entry, dt, bid, ask, mid, bars_held))
            position = 0
            bars_held = 0
            entry = None
        elif position != 0 and desired is not None and desired == -position and bars_held >= MIN_HOLD_BARS:
            trades.append(complete_trade(entry, dt, bid, ask, mid, bars_held))
            position = 0
            bars_held = 0
            entry = None
            if desired_entry_eligible:
                position = desired
                entry = open_trade(position, dt, bid, ask, mid, desired_ratio)

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
        })
        previous_dt = dt
        previous_mid = mid

    if position != 0 and entry is not None:
        censored.append({
            "symbol": symbol,
            "entry_timestamp": entry["entry_timestamp"],
            "status": "RIGHT_CENSORED_END_OF_SAMPLE",
        })

    net = [x["net_return"] for x in trades]
    gross = [x["gross_return"] for x in trades]
    net_eq, net_dd = frozen._max_drawdown(net)
    gross_eq, gross_dd = frozen._max_drawdown(gross)
    return {
        "contract_version": "RND0044-ratio-only-kernel-v1",
        "symbol": symbol,
        "arm": arm,
        "ratio_threshold": AUTHORIZED_ARMS[arm],
        "absolute_volatility_floor_enabled": False,
        "authorized_years": sorted(AUTHORIZED_YEARS),
        "row_count": len(parsed),
        "contiguous_episode_count": episode,
        "gap_count": len(gaps),
        "completed_trade_count": len(trades),
        "censored_trade_count": len(censored),
        "net_hit_rate": sum(1 for x in net if x > 0) / len(net) if net else None,
        "completed_trade_net_equity_index": net_eq,
        "completed_trade_net_max_drawdown": net_dd,
        "completed_trade_gross_equity_index": gross_eq,
        "completed_trade_gross_max_drawdown": gross_dd,
        "total_execution_cost_drag": sum(x["execution_cost_drag"] for x in trades),
        "completed_trade_net_return_sum": sum(net),
        "rejected_entry_signal_count": rejected_entry_signal_count,
        "actual_entry_signal_to_friction_ratios": actual_entry_ratios,
        "trades": trades,
        "gaps": gaps,
        "marks": marks,
        "authority": {
            "development_outcomes": False,
            "new_ratio_thresholds": False,
            "strategy_selection": False,
            "validation_access": False,
            "reserved_final_open": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
        },
    }
