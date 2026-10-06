#!/usr/bin/env python3
"""Pure development-only directional structure kernel for RND-0060J."""
from __future__ import annotations

from rnd0060h_cross_sectional_dispersion_state import (
    SYMBOLS,
    AUTHORIZED_YEARS,
    RND0060HError,
    extract_market_observations,
    spearman,
)


class RND0060JError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060JError(message)


def derive_directional_observations(rows_by_symbol):
    extracted = extract_market_observations(rows_by_symbol)
    out = []
    for row in extracted["observations"]:
        current = row["current_usd_oriented_returns"]
        forward = row["forward_usd_oriented_returns"]
        current_mean = sum(current[s] for s in SYMBOLS) / len(SYMBOLS)
        sign = 1.0 if current_mean > 0.0 else (-1.0 if current_mean < 0.0 else 0.0)
        state = row["cross_sectional_dispersion_state"] * sign
        forward_mean = sum(forward[s] for s in SYMBOLS) / len(SYMBOLS)
        out.append({
            "timestamp_utc": row["timestamp_utc"],
            "year": row["year"],
            "cross_sectional_dispersion_state": row["cross_sectional_dispersion_state"],
            "current_equal_weight_usd_oriented_return": current_mean,
            "directional_sign": sign,
            "signed_dispersion_state": state,
            "forward_equal_weight_usd_oriented_return": forward_mean,
            "per_symbol_forward_usd_oriented_return": dict(forward),
        })
    return {"observations": out, "exclusions": extracted["exclusions"]}


def _quartile_means(records):
    _req(len(records) >= 4, "quartile diagnostic requires at least four observations")
    ordered = sorted(records, key=lambda r: (r["signed_dispersion_state"], r["timestamp_utc"]))
    q = len(ordered) // 4
    _req(q >= 1, "quartile diagnostic requires non-empty quartiles")
    bottom = ordered[:q]
    top = ordered[-q:]
    return {
        "quartile_size": q,
        "bottom_quartile_mean_forward_equal_weight_usd_oriented_return": sum(r["forward_equal_weight_usd_oriented_return"] for r in bottom) / q,
        "top_quartile_mean_forward_equal_weight_usd_oriented_return": sum(r["forward_equal_weight_usd_oriented_return"] for r in top) / q,
    }


def classify_observations(observations, exclusions=None):
    _req(isinstance(observations, list) and len(observations) >= 4, "observations required")
    state = [r["signed_dispersion_state"] for r in observations]
    primary = [r["forward_equal_weight_usd_oriented_return"] for r in observations]
    aggregate = spearman(state, primary)

    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in observations if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient annual observations")
        annual[year] = spearman(
            [r["signed_dispersion_state"] for r in rows],
            [r["forward_equal_weight_usd_oriented_return"] for r in rows],
        )
    positive_years = sum(v > 0.0 for v in annual.values())

    per_symbol = {
        s: spearman(state, [r["per_symbol_forward_usd_oriented_return"][s] for r in observations])
        for s in SYMBOLS
    }
    positive_symbols = sum(v > 0.0 for v in per_symbol.values())
    q = _quartile_means(observations)

    criteria = {
        "aggregate_primary_spearman_gte_0_05": aggregate >= 0.05,
        "at_least_4_of_6_annual_primary_spearman_positive": positive_years >= 4,
        "at_least_3_of_4_symbol_primary_spearman_positive": positive_symbols >= 3,
        "top_quartile_mean_primary_response_gt_bottom_quartile": q["top_quartile_mean_forward_equal_weight_usd_oriented_return"] > q["bottom_quartile_mean_forward_equal_weight_usd_oriented_return"],
        "integrity_reconciliation_pass": True,
    }
    passed = all(criteria.values())
    return {
        "classification": "DIRECTIONAL_STRUCTURE_DETECTED" if passed else "NO_REPRODUCIBLE_DIRECTIONAL_STRUCTURE",
        "criteria": criteria,
        "eligible_observation_count": len(observations),
        "excluded_observation_count": len(exclusions or []),
        "aggregate_primary_spearman": aggregate,
        "annual_primary_spearman": annual,
        "positive_year_count": positive_years,
        "per_symbol_primary_spearman": per_symbol,
        "positive_symbol_count": positive_symbols,
        "quartile_diagnostic": q,
        "observations": observations,
        "exclusions": list(exclusions or []),
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


def summarize(rows_by_symbol):
    d = derive_directional_observations(rows_by_symbol)
    return classify_observations(d["observations"], d["exclusions"])
