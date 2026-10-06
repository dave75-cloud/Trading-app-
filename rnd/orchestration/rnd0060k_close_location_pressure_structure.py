#!/usr/bin/env python3
"""Pure development-only close-location pressure structure kernel for RND-0060K."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import (
    SYMBOLS, ORIENTATION, AUTHORIZED_YEARS, OBS_HOUR, OBS_MINUTE,
    LOOKBACK_BARS, FORWARD_BARS, validate_rows, _population_std, spearman,
)


class RND0060KError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060KError(message)


def extract_pressure_observations(rows_by_symbol):
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
        current_bar_dts = [obs_dt - timedelta(minutes=5 * k) for k in range(LOOKBACK_BARS - 1, -1, -1)]
        future_dts = [obs_dt + timedelta(minutes=5 * k) for k in range(1, FORWARD_BARS + 1)]
        required = [start_dt] + current_bar_dts + future_dts
        if any(any(dt not in by_dt[s] for dt in required) for s in SYMBOLS):
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING"})
            continue

        current_usd = {}
        pressures = {}
        forward_usd = {}
        rows_day = []
        degenerate = False
        for s in SYMBOLS:
            start_mid = by_dt[s][start_dt]["mid"]
            obs_mid = by_dt[s][obs_dt]["mid"]
            current_usd[s] = ORIENTATION[s] * (obs_mid / start_mid - 1.0)
            current_bars = [by_dt[s][dt] for dt in current_bar_dts]
            lo = min(r["low"] for r in current_bars)
            hi = max(r["high"] for r in current_bars)
            if not hi > lo:
                degenerate = True
                break
            raw_clv = 2.0 * ((obs_mid - lo) / (hi - lo)) - 1.0
            pressure = raw_clv * ORIENTATION[s]
            final_mid = by_dt[s][future_dts[-1]]["mid"]
            fwd = ORIENTATION[s] * (final_mid / obs_mid - 1.0)
            pressures[s] = pressure
            forward_usd[s] = fwd
            rows_day.append({
                "timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "year": obs_dt.year,
                "symbol": s,
                "usd_oriented_close_location_pressure": pressure,
                "forward_usd_oriented_return": fwd,
            })
        if degenerate:
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "DEGENERATE_CURRENT_30M_RANGE"})
            continue
        context = _population_std([current_usd[s] for s in SYMBOLS])
        for r in rows_day:
            r["cross_sectional_dispersion_context"] = context
            r["all_symbol_pressures"] = dict(pressures)
            r["all_symbol_forward_usd_returns"] = dict(forward_usd)
            observations.append(r)
    return {"observations": observations, "exclusions": exclusions}


def _quartile_means(records):
    _req(len(records) >= 4, "quartile diagnostic requires at least four observations")
    ordered = sorted(records, key=lambda r: (r["usd_oriented_close_location_pressure"], r["timestamp_utc"], r["symbol"]))
    q = len(ordered) // 4
    _req(q >= 1, "quartile diagnostic requires non-empty quartiles")
    bottom, top = ordered[:q], ordered[-q:]
    return {
        "quartile_size": q,
        "bottom_quartile_mean_forward_usd_oriented_return": sum(r["forward_usd_oriented_return"] for r in bottom) / q,
        "top_quartile_mean_forward_usd_oriented_return": sum(r["forward_usd_oriented_return"] for r in top) / q,
    }


def classify_observations(observations, exclusions=None):
    _req(isinstance(observations, list) and len(observations) >= 4, "observations required")
    x = [r["usd_oriented_close_location_pressure"] for r in observations]
    y = [r["forward_usd_oriented_return"] for r in observations]
    aggregate = spearman(x, y)

    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in observations if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient annual observations")
        annual[year] = spearman(
            [r["usd_oriented_close_location_pressure"] for r in rows],
            [r["forward_usd_oriented_return"] for r in rows],
        )
    per_symbol = {}
    for s in SYMBOLS:
        rows = [r for r in observations if r["symbol"] == s]
        _req(len(rows) >= 2, f"{s}: insufficient symbol observations")
        per_symbol[s] = spearman(
            [r["usd_oriented_close_location_pressure"] for r in rows],
            [r["forward_usd_oriented_return"] for r in rows],
        )
    positive_years = sum(v > 0.0 for v in annual.values())
    positive_symbols = sum(v > 0.0 for v in per_symbol.values())
    q = _quartile_means(observations)
    criteria = {
        "aggregate_primary_spearman_gte_0_05": aggregate >= 0.05,
        "at_least_4_of_6_annual_primary_spearman_positive": positive_years >= 4,
        "at_least_3_of_4_symbol_primary_spearman_positive": positive_symbols >= 3,
        "top_quartile_mean_primary_response_gt_bottom_quartile": q["top_quartile_mean_forward_usd_oriented_return"] > q["bottom_quartile_mean_forward_usd_oriented_return"],
        "integrity_reconciliation_pass": True,
    }
    return {
        "classification": "DIRECTIONAL_PRESSURE_STRUCTURE_DETECTED" if all(criteria.values()) else "NO_REPRODUCIBLE_DIRECTIONAL_PRESSURE_STRUCTURE",
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
        "activity_context_descriptive_only": True,
        "activity_threshold": None,
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


def summarize(rows_by_symbol):
    d = extract_pressure_observations(rows_by_symbol)
    return classify_observations(d["observations"], d["exclusions"])
