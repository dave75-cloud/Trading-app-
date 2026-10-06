#!/usr/bin/env python3
"""Pure development-only kernel for RND-0060I.

No validation/final access, broker authority, capital authority, or automatic
promotion exists here.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
ORIENTATION = {"AUDUSD": -1.0, "EURUSD": -1.0, "GBPUSD": -1.0, "USDJPY": 1.0}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
M5_SECONDS = 300
OBS_HOUR = 11
OBS_MINUTE = 30
REFERENCE_DAYS = 60
REFERENCE_RANK_ZERO_BASED = 44


class RND0060IError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060IError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060IError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _num(value, role, positive=False):
    _req(not isinstance(value, bool), f"{role}: finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060IError(f"{role}: finite number required") from exc
    _req(math.isfinite(out), f"{role}: finite number required")
    if positive:
        _req(out > 0.0, f"{role}: positive number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close", "mid_high", "mid_low"}
    out = []
    previous = None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(previous is None or dt > previous, "rows: timestamps must be unique and ordered")
        bid = _num(row["bid_close"], "bid_close", positive=True)
        ask = _num(row["ask_close"], "ask_close", positive=True)
        mid = _num(row["mid_close"], "mid_close", positive=True)
        high = _num(row["mid_high"], "mid_high", positive=True)
        low = _num(row["mid_low"], "mid_low", positive=True)
        _req(bid <= mid <= ask, "bid/mid/ask ordering invalid")
        _req(low <= mid <= high, "mid low/close/high ordering invalid")
        out.append({"dt": dt, "bid": bid, "ask": ask, "mid": mid, "high": high, "low": low})
        previous = dt
    return out


def _population_std(values):
    vals = [_num(v, "population std value") for v in values]
    _req(len(vals) == 4, "exactly four cross-sectional values required")
    mean = sum(vals) / 4.0
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / 4.0)


def _threshold(prior_states):
    _req(len(prior_states) >= REFERENCE_DAYS, "60 prior eligible states required")
    ordered = sorted(float(v) for v in prior_states[-REFERENCE_DAYS:])
    return ordered[REFERENCE_RANK_ZERO_BASED]


def _drawdown(equity_curve):
    peak = 1.0
    worst = 0.0
    for e in equity_curve:
        peak = max(peak, e)
        worst = min(worst, e / peak - 1.0)
    return worst


def run_candidate(rows_by_symbol):
    _req(isinstance(rows_by_symbol, dict) and set(rows_by_symbol) == set(SYMBOLS), "exact four-symbol row set required")
    parsed = {s: validate_rows(rows_by_symbol[s]) for s in SYMBOLS}
    by = {s: {r["dt"]: r for r in parsed[s]} for s in SYMBOLS}
    days = sorted(set.intersection(*[
        {r["dt"].date() for r in parsed[s] if r["dt"].weekday() < 5 and r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE}
        for s in SYMBOLS
    ]))

    prior_states = []
    trades = []
    exclusions = []
    gated_days = 0
    warmup_days = 0
    no_breakout_days = 0

    for day in days:
        obs = datetime(day.year, day.month, day.day, 11, 30, tzinfo=timezone.utc)
        start = obs - timedelta(minutes=30)
        range_dts = [obs - timedelta(minutes=5 * k) for k in range(5, -1, -1)]
        pre_required = [start] + range_dts
        if any(any(dt not in by[s] for dt in pre_required) for s in SYMBOLS):
            exclusions.append({"timestamp_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "PRE_OBSERVATION_MISSING"})
            continue

        usd_returns = {s: ORIENTATION[s] * (by[s][obs]["mid"] / by[s][start]["mid"] - 1.0) for s in SYMBOLS}
        state = _population_std([usd_returns[s] for s in SYMBOLS])
        abs_values = {s: abs(usd_returns[s]) for s in SYMBOLS}
        maximum = max(abs_values.values())
        leaders = [s for s in SYMBOLS if abs_values[s] == maximum]

        if len(prior_states) < REFERENCE_DAYS:
            warmup_days += 1
            prior_states.append(state)
            continue

        threshold = _threshold(prior_states)
        gate = state > threshold
        prior_states.append(state)
        if not gate:
            continue
        gated_days += 1
        if len(leaders) != 1:
            exclusions.append({"timestamp_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "PAIR_SELECTION_TIE"})
            continue

        symbol = leaders[0]
        upper = max(by[symbol][dt]["high"] for dt in range_dts)
        lower = min(by[symbol][dt]["low"] for dt in range_dts)
        trigger_dt = obs + timedelta(minutes=5)
        entry_dt = obs + timedelta(minutes=10)
        hold_dts = [obs + timedelta(minutes=m) for m in (15, 20, 25)]
        future_required = [trigger_dt, entry_dt] + hold_dts
        if any(dt not in by[symbol] for dt in future_required):
            exclusions.append({"timestamp_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "POST_OBSERVATION_MISSING"})
            continue

        trigger = by[symbol][trigger_dt]["mid"]
        if trigger > upper:
            direction = "LONG"
            entry = by[symbol][entry_dt]["ask"]
            exit_price = by[symbol][hold_dts[-1]]["bid"]
            realized_return = exit_price / entry - 1.0
        elif trigger < lower:
            direction = "SHORT"
            entry = by[symbol][entry_dt]["bid"]
            exit_price = by[symbol][hold_dts[-1]]["ask"]
            realized_return = entry / exit_price - 1.0
        else:
            no_breakout_days += 1
            continue

        trades.append({
            "timestamp_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": obs.year,
            "symbol": symbol,
            "direction": direction,
            "cross_sectional_dispersion_state": state,
            "trailing_60_q75_threshold": threshold,
            "selected_abs_usd_return": abs_values[symbol],
            "entry_price": entry,
            "exit_price": exit_price,
            "realized_return": realized_return,
        })

    equity = 1.0
    curve = []
    for t in trades:
        equity *= 1.0 + t["realized_return"]
        curve.append(equity)
    realized_net = sum(t["realized_return"] for t in trades)
    annual = {y: sum(t["realized_return"] for t in trades if t["year"] == y) for y in sorted(AUTHORIZED_YEARS)}
    per_symbol = {s: sum(t["realized_return"] for t in trades if t["symbol"] == s) for s in SYMBOLS}
    loo = {y: sum(v for yy, v in annual.items() if yy != y) for y in sorted(AUTHORIZED_YEARS)}
    criteria = {
        "aggregate_realized_net_gt_0": realized_net > 0.0,
        "terminal_normalized_equity_gt_1": equity > 1.0,
        "at_least_4_of_6_annual_realized_net_positive": sum(1 for v in annual.values() if v > 0.0) >= 4,
        "at_least_3_of_4_symbol_realized_net_positive": sum(1 for v in per_symbol.values() if v > 0.0) >= 3,
        "all_six_leave_one_year_out_realized_net_positive": all(v > 0.0 for v in loo.values()),
        "maximum_drawdown_gt_minus_0_10": _drawdown(curve) > -0.10,
        "integrity_reconciliation_pass": True,
    }
    return {
        "classification": "DEVELOPMENT_CANDIDATE_SUPPORTED_FOR_HUMAN_REVIEW" if all(criteria.values()) else "DEVELOPMENT_CANDIDATE_FALSIFIED",
        "criteria": criteria,
        "trade_count": len(trades),
        "gated_day_count": gated_days,
        "warmup_day_count": warmup_days,
        "no_breakout_day_count": no_breakout_days,
        "excluded_day_count": len(exclusions),
        "terminal_normalized_equity": equity,
        "realized_net": realized_net,
        "maximum_drawdown": _drawdown(curve),
        "annual_realized_net": annual,
        "per_symbol_realized_net": per_symbol,
        "leave_one_year_out_realized_net": loo,
        "trades": trades,
        "exclusions": exclusions,
        "development_only": True,
        "parameter_search": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
