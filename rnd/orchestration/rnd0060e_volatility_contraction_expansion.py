#!/usr/bin/env python3
"""Pure development-only kernel for RND-0060E."""
from __future__ import annotations

import math
from datetime import datetime, timezone

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
SESSIONS = {"AUDUSD": (11, 14), "EURUSD": (11, 13), "GBPUSD": (11, 13), "USDJPY": (11, 13)}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
M5_SECONDS = 300
OBS_HOUR = 11
OBS_MINUTE = 30
BASELINE_BARS = 18
SHORT_BARS = 6
TOTAL_BARS = 24
CONTRACTION_DIVISOR = 3.0
HOLD_BARS = 3

class RND0060EError(ValueError):
    pass

def _req(ok, msg):
    if not ok:
        raise RND0060EError(msg)

def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060EError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt

def _price(v, role):
    _req(not isinstance(v, bool), f"{role}: positive finite number required")
    try:
        x = float(v)
    except (TypeError, ValueError) as exc:
        raise RND0060EError(f"{role}: positive finite number required") from exc
    _req(math.isfinite(x) and x > 0, f"{role}: positive finite number required")
    return x

def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close", "mid_high", "mid_low"}
    out, prev = [], None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(prev is None or dt > prev, "rows: timestamps must be unique and ordered")
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        high = _price(row["mid_high"], "mid_high")
        low = _price(row["mid_low"], "mid_low")
        _req(bid <= mid <= ask, "bid/mid/ask ordering invalid")
        _req(low <= mid <= high, "mid low/close/high ordering invalid")
        out.append({"dt": dt, "bid": bid, "ask": ask, "mid": mid, "high": high, "low": low})
        prev = dt
    return out

def _in_session(dt, start_hour, end_hour):
    return dt.weekday() < 5 and start_hour <= dt.hour < end_hour

def _trade_return(side, entry_exec, exit_exec, entry_mid, exit_mid):
    if side == 1:
        gross = (exit_mid - entry_mid) / entry_mid
        net = (exit_exec - entry_exec) / entry_exec
    else:
        gross = (entry_mid - exit_mid) / entry_mid
        net = (entry_exec - exit_exec) / entry_exec
    return gross, net

def _mark_return(side, entry_exec, bar):
    mark_exec = bar["bid"] if side == 1 else bar["ask"]
    return ((mark_exec - entry_exec) / entry_exec) if side == 1 else ((entry_exec - mark_exec) / entry_exec)

def _max_drawdown(returns):
    equity = peak = 1.0
    max_dd = 0.0
    for r in returns:
        equity *= 1.0 + r
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
    return equity, max_dd

def evaluate_symbol(symbol, rows):
    _req(symbol in SYMBOLS, "unsupported symbol")
    parsed = validate_rows(rows)
    by_dt = {r["dt"]: r for r in parsed}
    index = {r["dt"]: i for i, r in enumerate(parsed)}
    start_hour, end_hour = SESSIONS[symbol]
    days = sorted({r["dt"].date() for r in parsed if r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE and r["dt"].weekday() < 5})

    trades, events, marks = [], [], []
    contraction_count = breakout_count = 0
    blocked_until = None

    for day in days:
        obs = datetime(day.year, day.month, day.day, OBS_HOUR, OBS_MINUTE, tzinfo=timezone.utc)
        if blocked_until is not None and obs <= blocked_until:
            events.append({"event_type": "DAY_SKIPPED_OPEN_POSITION", "timestamp": obs.strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue
        if obs not in by_dt:
            continue
        i = index[obs]
        if i < TOTAL_BARS - 1:
            events.append({"event_type": "DAY_SKIPPED_INCOMPLETE_STATE", "timestamp": obs.strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue
        window = parsed[i - (TOTAL_BARS - 1): i + 1]
        if any(x["dt"].date() != day for x in window) or not all(int((window[j]["dt"] - window[j-1]["dt"]).total_seconds()) == M5_SECONDS for j in range(1, len(window))):
            events.append({"event_type": "DAY_SKIPPED_INCOMPLETE_STATE", "timestamp": obs.strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue
        baseline = window[:BASELINE_BARS]
        short = window[BASELINE_BARS:]
        baseline_range = max(x["high"] for x in baseline) - min(x["low"] for x in baseline)
        short_high = max(x["high"] for x in short)
        short_low = min(x["low"] for x in short)
        short_range = short_high - short_low
        if not (baseline_range > 0 and short_range > 0 and short_range <= baseline_range / CONTRACTION_DIVISOR):
            continue
        contraction_count += 1
        events.append({"event_type": "CONTRACTION_EVENT", "timestamp": obs.strftime("%Y-%m-%dT%H:%M:%SZ"), "baseline_range": baseline_range, "short_range": short_range, "contraction_high": short_high, "contraction_low": short_low})

        signal = None
        j = i + 1
        while j < len(parsed):
            bar = parsed[j]
            dt = bar["dt"]
            if dt.date() != day or not _in_session(dt, start_hour, end_hour):
                break
            if int((dt - parsed[j-1]["dt"]).total_seconds()) != M5_SECONDS:
                events.append({"event_type": "BREAKOUT_SCAN_CANCELLED", "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "OBSERVATION_DISCONTINUITY"})
                break
            if bar["mid"] > short_high:
                signal = (j, 1); break
            if bar["mid"] < short_low:
                signal = (j, -1); break
            j += 1
        if signal is None:
            continue
        breakout_count += 1
        signal_i, side = signal
        signal_bar = parsed[signal_i]
        events.append({"event_type": "BREAKOUT_SIGNAL", "timestamp": signal_bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "side_value": side})
        entry_i = signal_i + 1
        if entry_i >= len(parsed):
            events.append({"event_type": "PENDING_SIGNAL_CANCELLED", "timestamp": signal_bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "NO_ENTRY_OBSERVATION"})
            continue
        entry = parsed[entry_i]
        if int((entry["dt"] - signal_bar["dt"]).total_seconds()) != M5_SECONDS or entry["dt"].date() != day or not _in_session(entry["dt"], start_hour, end_hour):
            events.append({"event_type": "PENDING_SIGNAL_CANCELLED", "timestamp": entry["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "ENTRY_NOT_ELIGIBLE"})
            continue
        entry_exec = entry["ask"] if side == 1 else entry["bid"]
        marks.append({"symbol": symbol, "timestamp": entry["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "position": side, "mark_return": _mark_return(side, entry_exec, entry)})
        held = 0
        gap_count = 0
        prev_dt = entry["dt"]
        exit_bar = None
        k = entry_i + 1
        while k < len(parsed) and held < HOLD_BARS:
            bar = parsed[k]
            delta = int((bar["dt"] - prev_dt).total_seconds())
            if delta != M5_SECONDS:
                gap_count += 1
                events.append({"event_type": "GAP_DURING_POSITION", "previous_timestamp": prev_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "next_timestamp": bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ")})
            held += 1
            prev_dt = bar["dt"]
            exit_bar = bar
            if held < HOLD_BARS:
                marks.append({"symbol": symbol, "timestamp": bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "position": side, "mark_return": _mark_return(side, entry_exec, bar)})
            k += 1
        if held < HOLD_BARS:
            blocked_until = parsed[-1]["dt"]
            events.append({"event_type": "RIGHT_CENSORED", "timestamp": entry["dt"].strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue
        blocked_until = exit_bar["dt"]
        exit_exec = exit_bar["bid"] if side == 1 else exit_bar["ask"]
        gross, net = _trade_return(side, entry_exec, exit_exec, entry["mid"], exit_bar["mid"])
        trade = {"symbol": symbol, "side": "long" if side == 1 else "short", "entry_timestamp": entry["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "exit_timestamp": exit_bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"), "holding_bars": held, "gap_exposure_count": gap_count, "entry_execution_price": entry_exec, "exit_execution_price": exit_exec, "entry_mid_price": entry["mid"], "exit_mid_price": exit_bar["mid"], "gross_return": gross, "net_return": net, "execution_cost_drag": gross - net, "exit_year": exit_bar["dt"].year}
        trades.append(trade)
        marks.append({"symbol": symbol, "timestamp": trade["exit_timestamp"], "position": 0, "mark_return": None})
        events.append({"event_type": "EXIT", "timestamp": trade["exit_timestamp"], "net_return": net})

    net_returns = [t["net_return"] for t in trades]
    gross_returns = [t["gross_return"] for t in trades]
    net_equity, max_dd = _max_drawdown(net_returns)
    gross_equity, _ = _max_drawdown(gross_returns)
    annual = {y: 0.0 for y in sorted(AUTHORIZED_YEARS)}
    for t in trades:
        annual[t["exit_year"]] += t["net_return"]
    return {"symbol": symbol, "trades": trades, "events": events, "marks": marks, "contraction_event_count": contraction_count, "breakout_signal_count": breakout_count, "completed_trade_count": len(trades), "trade_count": len(trades), "terminal_net_equity": net_equity, "terminal_gross_equity": gross_equity, "realized_net_sum": sum(net_returns), "max_drawdown": max_dd, "execution_cost_drag": sum(t["execution_cost_drag"] for t in trades), "annual_realized_net": annual, "development_only": True, "reserved_final_access": False, "broker_writes": False, "capital_authority": False, "automatic_promotion": False}
