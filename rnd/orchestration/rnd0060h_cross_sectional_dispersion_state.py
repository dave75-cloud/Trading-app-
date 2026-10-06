#!/usr/bin/env python3
"""Pure development-only measurement kernel for RND-0060H."""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
ORIENTATION = {"AUDUSD": -1.0, "EURUSD": -1.0, "GBPUSD": -1.0, "USDJPY": 1.0}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
OBS_HOUR = 11
OBS_MINUTE = 30
M5_SECONDS = 300
LOOKBACK_BARS = 6
FORWARD_BARS = 6


class RND0060HError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060HError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060HError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _num(value, role, positive=False):
    _req(not isinstance(value, bool), f"{role}: finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060HError(f"{role}: finite number required") from exc
    _req(math.isfinite(out), f"{role}: finite number required")
    if positive:
        _req(out > 0.0, f"{role}: positive number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "mid_close", "mid_high", "mid_low"}
    out = []
    previous = None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(previous is None or dt > previous, "rows: timestamps must be unique and ordered")
        mid = _num(row["mid_close"], "mid_close", positive=True)
        high = _num(row["mid_high"], "mid_high", positive=True)
        low = _num(row["mid_low"], "mid_low", positive=True)
        _req(low <= mid <= high, "mid low/close/high ordering invalid")
        out.append({"dt": dt, "mid": mid, "high": high, "low": low})
        previous = dt
    return out


def _population_std(values):
    vals = [_num(v, "population std value") for v in values]
    _req(len(vals) >= 2, "population std requires at least two values")
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))


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
    return _pearson(_average_ranks(x), _average_ranks(y))


def extract_market_observations(rows_by_symbol):
    _req(isinstance(rows_by_symbol, dict) and set(rows_by_symbol) == set(SYMBOLS), "exact four-symbol row set required")
    parsed = {s: validate_rows(rows_by_symbol[s]) for s in SYMBOLS}
    by_symbol_dt = {s: {r["dt"]: r for r in parsed[s]} for s in SYMBOLS}
    candidate_days = sorted(set.intersection(*[
        {r["dt"].date() for r in parsed[s] if r["dt"].weekday() < 5 and r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE}
        for s in SYMBOLS
    ]))
    observations = []
    exclusions = []

    for day in candidate_days:
        obs_dt = datetime(day.year, day.month, day.day, OBS_HOUR, OBS_MINUTE, tzinfo=timezone.utc)
        start_dt = obs_dt - timedelta(minutes=5 * LOOKBACK_BARS)
        future_dts = [obs_dt + timedelta(minutes=5 * k) for k in range(1, FORWARD_BARS + 1)]
        required = [start_dt, obs_dt] + future_dts
        if any(any(dt not in by_symbol_dt[s] for dt in required) for s in SYMBOLS):
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING"})
            continue

        current_usd = {}
        forward_usd = {}
        forward_ranges = {}
        for s in SYMBOLS:
            start_mid = by_symbol_dt[s][start_dt]["mid"]
            obs_mid = by_symbol_dt[s][obs_dt]["mid"]
            current_usd[s] = ORIENTATION[s] * (obs_mid / start_mid - 1.0)
            future = [by_symbol_dt[s][dt] for dt in future_dts]
            final_mid = future[-1]["mid"]
            forward_usd[s] = ORIENTATION[s] * (final_mid / obs_mid - 1.0)
            forward_ranges[s] = (max(r["high"] for r in future) - min(r["low"] for r in future)) / obs_mid
            _req(forward_ranges[s] >= 0.0, "forward relative range must be non-negative")

        state = _population_std([current_usd[s] for s in SYMBOLS])
        primary = sum(forward_ranges[s] for s in SYMBOLS) / len(SYMBOLS)
        secondary = _population_std([forward_usd[s] for s in SYMBOLS])
        observations.append({
            "timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": obs_dt.year,
            "cross_sectional_dispersion_state": state,
            "primary_mean_forward_relative_realized_range": primary,
            "secondary_forward_cross_sectional_return_dispersion": secondary,
            "current_usd_oriented_returns": current_usd,
            "forward_usd_oriented_returns": forward_usd,
            "per_symbol_forward_relative_realized_range": forward_ranges,
        })

    return {"observations": observations, "exclusions": exclusions}


def _quartile_means(records):
    _req(len(records) >= 4, "quartile diagnostic requires at least four observations")
    ordered = sorted(records, key=lambda r: (r["cross_sectional_dispersion_state"], r["timestamp_utc"]))
    q = len(ordered) // 4
    bottom = ordered[:q]
    top = ordered[-q:]
    return {
        "quartile_size": q,
        "bottom_quartile_mean_primary_response": sum(r["primary_mean_forward_relative_realized_range"] for r in bottom) / q,
        "top_quartile_mean_primary_response": sum(r["primary_mean_forward_relative_realized_range"] for r in top) / q,
    }


def summarize(rows_by_symbol):
    extracted = extract_market_observations(rows_by_symbol)
    obs = extracted["observations"]
    _req(len(obs) >= 4, "insufficient eligible market observations")
    state = [r["cross_sectional_dispersion_state"] for r in obs]
    primary = [r["primary_mean_forward_relative_realized_range"] for r in obs]
    secondary = [r["secondary_forward_cross_sectional_return_dispersion"] for r in obs]
    per_symbol = {
        s: spearman(state, [r["per_symbol_forward_relative_realized_range"][s] for r in obs])
        for s in SYMBOLS
    }
    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in obs if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient annual observations")
        annual[year] = spearman(
            [r["cross_sectional_dispersion_state"] for r in rows],
            [r["primary_mean_forward_relative_realized_range"] for r in rows],
        )
    q = _quartile_means(obs)
    positive_symbols = sum(1 for v in per_symbol.values() if v > 0.0)
    positive_years = sum(1 for v in annual.values() if v > 0.0)
    aggregate_primary = spearman(state, primary)
    criteria = {
        "aggregate_primary_spearman_gte_0_05": aggregate_primary >= 0.05,
        "at_least_4_of_6_annual_primary_spearman_positive": positive_years >= 4,
        "at_least_3_of_4_symbol_forward_range_spearman_positive": positive_symbols >= 3,
        "top_quartile_mean_primary_response_gt_bottom_quartile": q["top_quartile_mean_primary_response"] > q["bottom_quartile_mean_primary_response"],
        "integrity_reconciliation_pass": True,
    }
    return {
        "classification": "CROSS_SECTIONAL_STRUCTURE_DETECTED" if all(criteria.values()) else "NO_REPRODUCIBLE_STRUCTURE",
        "criteria": criteria,
        "eligible_observation_count": len(obs),
        "excluded_observation_count": len(extracted["exclusions"]),
        "aggregate_primary_spearman": aggregate_primary,
        "aggregate_secondary_spearman": spearman(state, secondary),
        "annual_primary_spearman": annual,
        "positive_year_count": positive_years,
        "per_symbol_primary_spearman": per_symbol,
        "positive_symbol_count": positive_symbols,
        "quartile_diagnostic": q,
        "observations": obs,
        "exclusions": extracted["exclusions"],
        "development_only": True,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
