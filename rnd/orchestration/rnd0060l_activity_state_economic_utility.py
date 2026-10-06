#!/usr/bin/env python3
"""Pure development-only economic-utility kernel for RND-0060L."""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import (
    SYMBOLS, ORIENTATION, AUTHORIZED_YEARS, OBS_HOUR, OBS_MINUTE,
    LOOKBACK_BARS, FORWARD_BARS, _population_std, spearman,
)


class RND0060LError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060LError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060LError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _num(value, role, positive=False, nonnegative=False):
    _req(not isinstance(value, bool), f"{role}: finite number required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060LError(f"{role}: finite number required") from exc
    _req(math.isfinite(x), f"{role}: finite number required")
    if positive:
        _req(x > 0.0, f"{role}: positive number required")
    if nonnegative:
        _req(x >= 0.0, f"{role}: non-negative number required")
    return x


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


def extract_utility_observations(rows_by_symbol):
    _req(isinstance(rows_by_symbol, dict) and set(rows_by_symbol) == set(SYMBOLS), "exact four-symbol row set required")
    parsed = {s: validate_rows(rows_by_symbol[s]) for s in SYMBOLS}
    by_dt = {s: {r["dt"]: r for r in parsed[s]} for s in SYMBOLS}
    candidate_days = sorted(set.intersection(*[
        {r["dt"].date() for r in parsed[s] if r["dt"].weekday() < 5 and r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE}
        for s in SYMBOLS
    ]))

    observations, exclusions = [], []
    for day in candidate_days:
        obs_dt = datetime(day.year, day.month, day.day, OBS_HOUR, OBS_MINUTE, tzinfo=timezone.utc)
        start_dt = obs_dt - timedelta(minutes=5 * LOOKBACK_BARS)
        future_dts = [obs_dt + timedelta(minutes=5 * k) for k in range(1, FORWARD_BARS + 1)]
        required = [start_dt, obs_dt] + future_dts
        if any(any(dt not in by_dt[s] for dt in required) for s in SYMBOLS):
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING"})
            continue

        current_usd = {}
        ratios = {}
        spreads = {}
        movements = {}
        invalid_spread = False
        for s in SYMBOLS:
            start_mid = by_dt[s][start_dt]["mid"]
            obs = by_dt[s][obs_dt]
            current_usd[s] = ORIENTATION[s] * (obs["mid"] / start_mid - 1.0)
            rel_spread = (obs["ask"] - obs["bid"]) / obs["mid"]
            if not rel_spread > 0.0:
                invalid_spread = True
                break
            future = [by_dt[s][dt] for dt in future_dts]
            rel_move = (max(r["high"] for r in future) - min(r["low"] for r in future)) / obs["mid"]
            _req(rel_move >= 0.0, "forward relative movement must be non-negative")
            spreads[s] = rel_spread
            movements[s] = rel_move
            ratios[s] = rel_move / rel_spread
        if invalid_spread:
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "NON_POSITIVE_CONTEMPORANEOUS_RELATIVE_SPREAD"})
            continue

        state = _population_std([current_usd[s] for s in SYMBOLS])
        primary = sum(ratios[s] for s in SYMBOLS) / len(SYMBOLS)
        observations.append({
            "timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": obs_dt.year,
            "cross_sectional_dispersion_state": state,
            "market_wide_movement_to_friction_ratio": primary,
            "per_symbol_movement_to_friction_ratio": dict(ratios),
            "per_symbol_contemporaneous_relative_spread": dict(spreads),
            "per_symbol_forward_relative_realized_movement": dict(movements),
        })
    return {"observations": observations, "exclusions": exclusions}


def _quartile_means(records):
    _req(len(records) >= 4, "quartile diagnostic requires at least four observations")
    ordered = sorted(records, key=lambda r: (r["cross_sectional_dispersion_state"], r["timestamp_utc"]))
    q = len(ordered) // 4
    _req(q >= 1, "quartile diagnostic requires non-empty quartiles")
    bottom, top = ordered[:q], ordered[-q:]
    return {
        "quartile_size": q,
        "bottom_quartile_mean_market_wide_movement_to_friction_ratio": sum(r["market_wide_movement_to_friction_ratio"] for r in bottom) / q,
        "top_quartile_mean_market_wide_movement_to_friction_ratio": sum(r["market_wide_movement_to_friction_ratio"] for r in top) / q,
    }


def classify_observations(observations, exclusions=None):
    _req(isinstance(observations, list) and len(observations) >= 4, "observations required")
    state = [r["cross_sectional_dispersion_state"] for r in observations]
    primary = [r["market_wide_movement_to_friction_ratio"] for r in observations]
    aggregate = spearman(state, primary)

    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in observations if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient annual observations")
        annual[year] = spearman(
            [r["cross_sectional_dispersion_state"] for r in rows],
            [r["market_wide_movement_to_friction_ratio"] for r in rows],
        )

    per_symbol = {}
    for s in SYMBOLS:
        per_symbol[s] = spearman(
            state,
            [r["per_symbol_movement_to_friction_ratio"][s] for r in observations],
        )

    positive_years = sum(v > 0.0 for v in annual.values())
    positive_symbols = sum(v > 0.0 for v in per_symbol.values())
    q = _quartile_means(observations)
    criteria = {
        "aggregate_primary_spearman_gte_0_05": aggregate >= 0.05,
        "at_least_4_of_6_annual_primary_spearman_positive": positive_years >= 4,
        "at_least_3_of_4_symbol_primary_spearman_positive": positive_symbols >= 3,
        "top_quartile_mean_primary_response_gt_bottom_quartile": q["top_quartile_mean_market_wide_movement_to_friction_ratio"] > q["bottom_quartile_mean_market_wide_movement_to_friction_ratio"],
        "integrity_reconciliation_pass": True,
    }
    return {
        "classification": "ACTIVITY_STATE_ECONOMIC_UTILITY_DETECTED" if all(criteria.values()) else "NO_REPRODUCIBLE_ACTIVITY_STATE_ECONOMIC_UTILITY",
        "criteria": criteria,
        "eligible_observation_count": len(observations),
        "excluded_market_day_count": len(exclusions or []),
        "aggregate_primary_spearman": aggregate,
        "annual_primary_spearman": annual,
        "positive_year_count": positive_years,
        "per_symbol_primary_spearman": per_symbol,
        "positive_symbol_count": positive_symbols,
        "quartile_diagnostic": q,
        "observations": observations,
        "exclusions": list(exclusions or []),
        "development_only": True,
        "declared_trial_count": 1,
        "parameter_search": False,
        "threshold_search": False,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "prospective_candidate_outcomes_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def summarize(rows_by_symbol):
    d = extract_utility_observations(rows_by_symbol)
    return classify_observations(d["observations"], d["exclusions"])
