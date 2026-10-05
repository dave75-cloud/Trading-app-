#!/usr/bin/env python3
"""Pure development-only kernel for RND-0060A.

Single predeclared opening-range breakout trial. No parameter search, validation
access, reserved-final access, broker writes, promotion, or capital authority.
Execution accounting inherits RND-0034 close-price, one-bar delay and gap rules.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
M5 = timedelta(minutes=5)
LOOKBACK_BARS = 12
HOLD_BARS = 3


class RND0060AError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060AError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0060AError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _price(value, role):
    _req(not isinstance(value, bool), f"{role}: positive finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060AError(f"{role}: positive finite number required") from exc
    _req(math.isfinite(out) and out > 0, f"{role}: positive finite number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {
        "timestamp_utc", "complete", "bid_close", "ask_close", "mid_close",
        "mid_high", "mid_low",
    }
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
        high = _price(row["mid_high"], "mid_high")
        low = _price(row["mid_low"], "mid_low")
        _req(bid <= mid <= ask, "bid/mid/ask ordering invalid")
        _req(low <= mid <= high, "mid OHLC ordering invalid")
        parsed.append({"dt": dt, "bid": bid, "ask": ask, "mid": mid, "high": high, "low": low})
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


def _build_marks(symbol, parsed, intervals):
    entries = {x["entry_dt"]: x for x in intervals}
    exits = {x["exit_dt"] for x in intervals if x["exit_dt"] is not None}
    marks = []
    active = None
    for bar in parsed:
        dt = bar["dt"]
        if dt in entries:
            _req(active is None, "overlapping same-symbol positions prohibited")
            active = entries[dt]
        if active is not None and dt in exits and active.get("exit_dt") == dt:
            marks.append({
                "symbol": symbol,
                "timestamp": _z(dt),
                "position": 0,
                "mark_return": None,
            })
            active = None
            continue
        if active is None:
            marks.append({
                "symbol": symbol,
                "timestamp": _z(dt),
                "position": 0,
                "mark_return": None,
            })
            continue
        side = active["side"]
        if side == 1:
            mark_return = (bar["bid"] - active["entry_exec"]) / active["entry_exec"]
        else:
            mark_return = (active["entry_exec"] - bar["ask"]) / active["entry_exec"]
        marks.append({
            "symbol": symbol,
            "timestamp": _z(dt),
            "position": side,
            "mark_return": mark_return,
        })
    return marks


def evaluate_symbol(symbol, rows):
    _req(symbol in SYMBOLS, "unsupported symbol")
    parsed = validate_rows(rows)
    by_dt = {x["dt"]: x for x in parsed}
    index_by_dt = {x["dt"]: i for i, x in enumerate(parsed)}
    start_hour, end_hour = SESSIONS[symbol]

    trades = []
    events = []
    intervals = []
    dates = sorted({x["dt"].date() for x in parsed if x["dt"].weekday() < 5})

    for day in dates:
        session_start = datetime(day.year, day.month, day.day, start_hour, tzinfo=timezone.utc)
        first = by_dt.get(session_start)
        if first is None:
            continue

        lookback_times = [session_start - M5 * n for n in range(LOOKBACK_BARS, 0, -1)]
        if any(ts not in by_dt for ts in lookback_times):
            events.append({"event_type": "NO_SIGNAL_LOOKBACK_GAP", "timestamp": _z(session_start)})
            continue
        lookback = [by_dt[ts] for ts in lookback_times]
        pre_high = max(x["high"] for x in lookback)
        pre_low = min(x["low"] for x in lookback)

        side = 1 if first["mid"] > pre_high else (-1 if first["mid"] < pre_low else 0)
        events.append({
            "event_type": "FIRST_SESSION_SIGNAL",
            "timestamp": _z(session_start),
            "signal": side,
            "pre_session_high": pre_high,
            "pre_session_low": pre_low,
        })
        if side == 0:
            continue

        entry_dt = session_start + M5
        entry = by_dt.get(entry_dt)
        if entry is None:
            events.append({
                "event_type": "PENDING_SIGNAL_CANCELLED",
                "timestamp": _z(entry_dt),
                "reason": "OBSERVATION_DISCONTINUITY",
            })
            continue
        _req(entry_dt.hour < end_hour or (entry_dt.hour == end_hour and entry_dt.minute == 0), "entry outside frozen session")

        entry_exec = entry["ask"] if side == 1 else entry["bid"]
        entry_mid = entry["mid"]
        events.append({
            "event_type": "ENTRY",
            "timestamp": _z(entry_dt),
            "side_value": side,
            "execution_price": entry_exec,
        })

        held = 0
        cursor_index = index_by_dt[entry_dt] + 1
        exit_bar = None
        gap_count = 0
        previous_dt = entry_dt
        while cursor_index < len(parsed) and held < HOLD_BARS:
            bar = parsed[cursor_index]
            if bar["dt"].date() != day:
                break
            delta = bar["dt"] - previous_dt
            if delta != M5:
                gap_count += 1
                events.append({
                    "event_type": "GAP_DURING_POSITION",
                    "previous_timestamp": _z(previous_dt),
                    "next_timestamp": _z(bar["dt"]),
                })
            held += 1
            exit_bar = bar
            previous_dt = bar["dt"]
            cursor_index += 1

        if held != HOLD_BARS or exit_bar is None:
            intervals.append({
                "side": side,
                "entry_dt": entry_dt,
                "exit_dt": None,
                "entry_exec": entry_exec,
            })
            events.append({"event_type": "RIGHT_CENSORED", "timestamp": _z(entry_dt)})
            continue

        exit_exec = exit_bar["bid"] if side == 1 else exit_bar["ask"]
        gross, net = _trade_return(side, entry_exec, exit_exec, entry_mid, exit_bar["mid"])
        trade = {
            "symbol": symbol,
            "side": "long" if side == 1 else "short",
            "entry_timestamp": _z(entry_dt),
            "exit_timestamp": _z(exit_bar["dt"]),
            "holding_bars": held,
            "gap_exposure_count": gap_count,
            "entry_execution_price": entry_exec,
            "exit_execution_price": exit_exec,
            "entry_mid_price": entry_mid,
            "exit_mid_price": exit_bar["mid"],
            "gross_return": gross,
            "net_return": net,
            "execution_cost_drag": gross - net,
            "exit_year": exit_bar["dt"].year,
        }
        trades.append(trade)
        intervals.append({
            "side": side,
            "entry_dt": entry_dt,
            "exit_dt": exit_bar["dt"],
            "entry_exec": entry_exec,
        })
        events.append({"event_type": "EXIT", "timestamp": trade["exit_timestamp"], "net_return": net})

    marks = _build_marks(symbol, parsed, intervals)
    net_returns = [x["net_return"] for x in trades]
    gross_returns = [x["gross_return"] for x in trades]
    net_equity, max_dd = _max_drawdown(net_returns)
    gross_equity, _ = _max_drawdown(gross_returns)
    annual = {year: 0.0 for year in sorted(AUTHORIZED_YEARS)}
    for trade in trades:
        annual[trade["exit_year"]] += trade["net_return"]
    return {
        "symbol": symbol,
        "row_count": len(parsed),
        "trades": trades,
        "marks": marks,
        "events": events,
        "trade_count": len(trades),
        "completed_trade_count": len(trades),
        "censored_trade_count": sum(1 for x in intervals if x["exit_dt"] is None),
        "terminal_net_equity": net_equity,
        "terminal_gross_equity": gross_equity,
        "realized_net_sum": sum(net_returns),
        "max_drawdown": max_dd,
        "execution_cost_drag": sum(x["execution_cost_drag"] for x in trades),
        "annual_realized_net": annual,
        "strategy_evaluation": True,
        "development_only": True,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
