#!/usr/bin/env python3
"""Pure development-only measurement kernel for RND-0060F.

No trading rule, P&L, validation/final access, broker write, capital authority,
or automatic promotion exists in this module.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
M5_SECONDS = 300
OBS_HOUR = 11
OBS_MINUTE = 30
BASELINE_BARS = 12
FORWARD_BARS = 6


class RND0060FError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060FError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060FError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _num(value, role, positive=False):
    _req(not isinstance(value, bool), f"{role}: finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060FError(f"{role}: finite number required") from exc
    _req(math.isfinite(out), f"{role}: finite number required")
    if positive:
        _req(out > 0.0, f"{role}: positive number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {
        "timestamp_utc", "complete", "bid_close", "ask_close", "mid_close",
        "mid_high", "mid_low",
    }
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
        rel_spread = (ask - bid) / mid
        _req(math.isfinite(rel_spread) and rel_spread > 0.0, "relative spread must be positive")
        out.append({
            "dt": dt,
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "high": high,
            "low": low,
            "relative_spread": rel_spread,
        })
        previous = dt
    return out


def _median(values):
    vals = sorted(_num(x, "median value") for x in values)
    _req(vals, "median requires values")
    n = len(vals)
    if n % 2:
        return vals[n // 2]
    return (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def _average_ranks(values):
    pairs = sorted((float(v), i) for i, v in enumerate(values))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        rank = ((i + 1) + j) / 2.0
        for k in range(i, j):
            ranks[pairs[k][1]] = rank
        i = j
    return ranks


def _pearson(x, y):
    _req(len(x) == len(y) and len(x) >= 2, "correlation requires matched observations")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    sx = sum(v * v for v in dx)
    sy = sum(v * v for v in dy)
    _req(sx > 0.0 and sy > 0.0, "correlation undefined for constant input")
    return sum(a * b for a, b in zip(dx, dy)) / math.sqrt(sx * sy)


def spearman(x, y):
    _req(len(x) == len(y) and len(x) >= 2, "spearman requires matched observations")
    return _pearson(_average_ranks(x), _average_ranks(y))


def _quartile_means(records):
    _req(isinstance(records, list) and len(records) >= 4, "quartile diagnostic requires at least four observations")
    ordered = sorted(records, key=lambda r: (r["spread_state_ratio"], r["timestamp_utc"]))
    q = len(ordered) // 4
    _req(q >= 1, "quartile diagnostic requires non-empty quartiles")
    bottom = ordered[:q]
    top = ordered[-q:]
    return {
        "quartile_size": q,
        "bottom_quartile_mean_forward_realized_mid_range": sum(r["forward_realized_mid_range"] for r in bottom) / q,
        "top_quartile_mean_forward_realized_mid_range": sum(r["forward_realized_mid_range"] for r in top) / q,
    }


def extract_symbol_observations(symbol, rows):
    _req(symbol in SYMBOLS, "unsupported symbol")
    parsed = validate_rows(rows)
    by_dt = {r["dt"]: r for r in parsed}
    days = sorted({r["dt"].date() for r in parsed if r["dt"].weekday() < 5 and r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE})
    observations = []
    exclusions = []

    for day in days:
        obs_dt = datetime(day.year, day.month, day.day, OBS_HOUR, OBS_MINUTE, tzinfo=timezone.utc)
        required_pre = [obs_dt - timedelta(minutes=5 * k) for k in range(BASELINE_BARS, 0, -1)]
        required_forward = [obs_dt + timedelta(minutes=5 * k) for k in range(1, FORWARD_BARS + 1)]
        all_required = required_pre + [obs_dt] + required_forward
        if any(dt not in by_dt for dt in all_required):
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "REQUIRED_OBSERVATION_MISSING"})
            continue

        baseline = [by_dt[dt]["relative_spread"] for dt in required_pre]
        baseline_median = _median(baseline)
        _req(baseline_median > 0.0, "baseline median relative spread must be positive")
        current = by_dt[obs_dt]
        state_ratio = current["relative_spread"] / baseline_median
        future = [by_dt[dt] for dt in required_forward]
        final_mid = future[-1]["mid"]
        absolute_close_return = abs(final_mid / current["mid"] - 1.0)
        realized_range = (max(r["high"] for r in future) - min(r["low"] for r in future)) / current["mid"]
        _req(realized_range >= 0.0 and absolute_close_return >= 0.0, "forward response must be non-negative")
        observations.append({
            "symbol": symbol,
            "timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": obs_dt.year,
            "current_relative_spread": current["relative_spread"],
            "baseline_median_relative_spread": baseline_median,
            "spread_state_ratio": state_ratio,
            "forward_absolute_close_return": absolute_close_return,
            "forward_realized_mid_range": realized_range,
        })

    return {"symbol": symbol, "observations": observations, "exclusions": exclusions}


def summarize_symbol(symbol, rows):
    extracted = extract_symbol_observations(symbol, rows)
    obs = extracted["observations"]
    _req(len(obs) >= 4, f"{symbol}: insufficient eligible observations")
    state = [r["spread_state_ratio"] for r in obs]
    ranges = [r["forward_realized_mid_range"] for r in obs]
    abs_returns = [r["forward_absolute_close_return"] for r in obs]
    q = _quartile_means(obs)
    return {
        "symbol": symbol,
        "eligible_observation_count": len(obs),
        "excluded_observation_count": len(extracted["exclusions"]),
        "primary_spearman_spread_state_vs_forward_range": spearman(state, ranges),
        "secondary_spearman_spread_state_vs_forward_absolute_close_return": spearman(state, abs_returns),
        "quartile_diagnostic": q,
        "observations": obs,
        "exclusions": extracted["exclusions"],
        "development_only": True,
        "trade_simulation": False,
        "pnl": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def classify(per_symbol):
    _req(isinstance(per_symbol, dict) and set(per_symbol) == set(SYMBOLS), "exact four-symbol result set required")
    symbol_positive = sum(1 for s in SYMBOLS if per_symbol[s]["primary_spearman_spread_state_vs_forward_range"] > 0.0)
    quartile_positive = sum(
        1 for s in SYMBOLS
        if per_symbol[s]["quartile_diagnostic"]["top_quartile_mean_forward_realized_mid_range"]
        > per_symbol[s]["quartile_diagnostic"]["bottom_quartile_mean_forward_realized_mid_range"]
    )
    pooled = []
    for s in SYMBOLS:
        pooled.extend(per_symbol[s]["observations"])
    aggregate_primary = spearman(
        [r["spread_state_ratio"] for r in pooled],
        [r["forward_realized_mid_range"] for r in pooled],
    )
    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in pooled if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient pooled observations")
        annual[year] = spearman(
            [r["spread_state_ratio"] for r in rows],
            [r["forward_realized_mid_range"] for r in rows],
        )
    positive_years = sum(1 for v in annual.values() if v > 0.0)
    criteria = {
        "at_least_3_of_4_symbol_primary_spearman_positive": symbol_positive >= 3,
        "at_least_4_of_6_annual_pooled_primary_spearman_positive": positive_years >= 4,
        "aggregate_primary_spearman_gte_0_05": aggregate_primary >= 0.05,
        "at_least_3_of_4_symbol_top_quartile_mean_range_gt_bottom_quartile": quartile_positive >= 3,
        "integrity_reconciliation_pass": True,
    }
    passed = all(criteria.values())
    return {
        "classification": "MARKET_STATE_STRUCTURE_DETECTED" if passed else "NO_REPRODUCIBLE_STRUCTURE",
        "criteria": criteria,
        "aggregate_primary_spearman": aggregate_primary,
        "symbol_primary_positive_count": symbol_positive,
        "quartile_positive_count": quartile_positive,
        "annual_pooled_primary_spearman": annual,
        "positive_year_count": positive_years,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
