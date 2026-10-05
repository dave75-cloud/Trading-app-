#!/usr/bin/env python3
"""RND-0045 cross-pair heterogeneity diagnostics.

Pure diagnostic layer for the frozen RND-0044 Q003 mechanism versus Q000.
No strategy mechanics are changed here. Development outcomes remain closed
until separately authorized by a human gate.
"""
from __future__ import annotations

import math
import statistics

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
YEARS = tuple(str(y) for y in range(2015, 2021))


class RND0045DiagnosticError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0045DiagnosticError(message)


def _finite(value, role):
    _req(not isinstance(value, bool), f"{role}: finite numeric value required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0045DiagnosticError(f"{role}: finite numeric value required") from exc
    _req(math.isfinite(x), f"{role}: finite numeric value required")
    return x


def validate_arm(arm, role):
    _req(isinstance(arm, dict), f"{role}: mapping required")
    per_symbol = arm.get("per_symbol")
    yearly = arm.get("year_pair_net_return_sum")
    _req(isinstance(per_symbol, dict) and tuple(sorted(per_symbol)) == tuple(sorted(SYMBOLS)), f"{role}: symbol set changed")
    _req(isinstance(yearly, dict) and tuple(sorted(yearly)) == tuple(sorted(YEARS)), f"{role}: year set changed")
    for year in YEARS:
        _req(isinstance(yearly[year], dict) and tuple(sorted(yearly[year])) == tuple(sorted(SYMBOLS)), f"{role}: yearly symbol set changed")
        for symbol in SYMBOLS:
            _finite(yearly[year][symbol], f"{role}.{year}.{symbol}")
    required_pair_fields = (
        "net_return_sum", "net_equity_index", "net_max_drawdown",
        "execution_cost_drag", "trades",
    )
    for symbol in SYMBOLS:
        row = per_symbol[symbol]
        _req(isinstance(row, dict), f"{role}.{symbol}: mapping required")
        for field in required_pair_fields:
            _req(field in row, f"{role}.{symbol}: missing {field}")
            _finite(row[field], f"{role}.{symbol}.{field}")
    return arm


def _rank(values):
    """Average ranks, descending: strongest effect gets rank 1."""
    ordered = sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))
    ranks = {}
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][1] == ordered[i][1]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[ordered[k][0]] = avg
        i = j
    return ranks


def _spearman_rank_correlation(a, b):
    ra, rb = _rank(a), _rank(b)
    xs = [ra[s] for s in SYMBOLS]
    ys = [rb[s] for s in SYMBOLS]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def classify(pair_effects, aggregate_effect, loo_pair, year_aggregate, yearly_pair_effects):
    positive_pairs = sum(v > 0 for v in pair_effects.values())
    total_positive = sum(v for v in pair_effects.values() if v > 0)
    negative_floor_ok = all(v >= -0.35 * total_positive for v in pair_effects.values() if v < 0) if total_positive > 0 else False
    loo_all_positive = all(v > 0 for v in loo_pair.values())
    positive_years = sum(v > 0 for v in year_aggregate.values())
    years_3_of_4 = sum(sum(yearly_pair_effects[y][s] > 0 for s in SYMBOLS) >= 3 for y in YEARS)
    max_pair_share = max((v / total_positive for v in pair_effects.values() if v > 0), default=0.0)

    candidate = (
        positive_pairs >= 3
        and negative_floor_ok
        and loo_all_positive
        and positive_years >= 4
        and years_3_of_4 >= 4
        and max_pair_share <= 0.70
    )
    if aggregate_effect <= 0:
        label = "COMMON_MECHANISM_FALSIFIED"
    elif candidate:
        label = "COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW"
    elif positive_pairs >= 3 and loo_all_positive and max_pair_share <= 0.70:
        label = "COMMON_MECHANISM_SUPPORTED_WITH_MATERIAL_HETEROGENEITY"
    else:
        label = "PAIR_DEPENDENT_MECHANISM"
    return label, {
        "positive_full_period_pair_count": positive_pairs,
        "negative_pair_bound_ok": negative_floor_ok,
        "leave_one_pair_out_all_positive": loo_all_positive,
        "positive_aggregate_year_count": positive_years,
        "years_with_at_least_3_positive_pairs": years_3_of_4,
        "max_positive_pair_share": max_pair_share,
    }


def analyze(q000, q003):
    validate_arm(q000, "Q000")
    validate_arm(q003, "Q003")

    pair_metrics = {}
    pair_effects = {}
    yearly_pair_effects = {y: {} for y in YEARS}
    for symbol in SYMBOLS:
        b = q000["per_symbol"][symbol]
        t = q003["per_symbol"][symbol]
        net_effect = _finite(t["net_return_sum"], "Q003 net") - _finite(b["net_return_sum"], "Q000 net")
        pair_effects[symbol] = net_effect
        pair_metrics[symbol] = {
            "net_return_sum_treatment_effect": net_effect,
            "net_equity_index_change": _finite(t["net_equity_index"], "Q003 equity") - _finite(b["net_equity_index"], "Q000 equity"),
            "max_drawdown_change": _finite(t["net_max_drawdown"], "Q003 drawdown") - _finite(b["net_max_drawdown"], "Q000 drawdown"),
            "execution_cost_drag_change": _finite(t["execution_cost_drag"], "Q003 cost") - _finite(b["execution_cost_drag"], "Q000 cost"),
            "trade_count_change": int(round(_finite(t["trades"], "Q003 trades") - _finite(b["trades"], "Q000 trades"))),
            "positive_year_count": 0,
            "yearly_net_return_sum_treatment_effect": {},
        }
        for year in YEARS:
            effect = _finite(q003["year_pair_net_return_sum"][year][symbol], "Q003 yearly") - _finite(q000["year_pair_net_return_sum"][year][symbol], "Q000 yearly")
            yearly_pair_effects[year][symbol] = effect
            pair_metrics[symbol]["yearly_net_return_sum_treatment_effect"][year] = effect
            pair_metrics[symbol]["positive_year_count"] += int(effect > 0)

    aggregate_effect = sum(pair_effects.values())
    year_aggregate = {y: sum(yearly_pair_effects[y].values()) for y in YEARS}
    pair_positive_counts_by_year = {y: sum(yearly_pair_effects[y][s] > 0 for s in SYMBOLS) for y in YEARS}

    loo_pair = {excluded: aggregate_effect - pair_effects[excluded] for excluded in SYMBOLS}
    for symbol in SYMBOLS:
        pair_metrics[symbol]["leave_one_year_out_treatment_effect"] = {
            excluded: pair_effects[symbol] - yearly_pair_effects[excluded][symbol] for excluded in YEARS
        }

    positive_total = sum(v for v in pair_effects.values() if v > 0)
    positive_shares = {
        s: (pair_effects[s] / positive_total if pair_effects[s] > 0 and positive_total > 0 else 0.0)
        for s in SYMBOLS
    }

    annual_rank_correlations = {}
    for i, y1 in enumerate(YEARS):
        for y2 in YEARS[i + 1:]:
            annual_rank_correlations[f"{y1}_vs_{y2}"] = _spearman_rank_correlation(yearly_pair_effects[y1], yearly_pair_effects[y2])
    finite_corr = [v for v in annual_rank_correlations.values() if v is not None]

    label, details = classify(pair_effects, aggregate_effect, loo_pair, year_aggregate, yearly_pair_effects)
    return {
        "contract_version": "RND0045-cross-pair-heterogeneity-v1",
        "frozen_mechanism": "RND0044_Q003_RATIO_ONLY_8_0",
        "pair_metrics": pair_metrics,
        "full_period_pair_treatment_effect": pair_effects,
        "aggregate_treatment_effect": aggregate_effect,
        "sign_coherence_positive_pair_count": sum(v > 0 for v in pair_effects.values()),
        "pair_effect_dispersion_population_std": statistics.pstdev(pair_effects.values()),
        "minimum_pair_treatment_effect": min(pair_effects.values()),
        "median_pair_treatment_effect": statistics.median(pair_effects.values()),
        "positive_pair_treatment_share": positive_shares,
        "max_positive_pair_share": max(positive_shares.values()),
        "yearly_pair_treatment_effect": yearly_pair_effects,
        "yearly_aggregate_treatment_effect": year_aggregate,
        "positive_pair_count_by_year": pair_positive_counts_by_year,
        "leave_one_pair_out_aggregate_treatment_effect": loo_pair,
        "annual_pair_rank_correlations": annual_rank_correlations,
        "median_annual_pair_rank_correlation": statistics.median(finite_corr) if finite_corr else None,
        "classification": label,
        "classification_details": details,
        "authority": {
            "development_outcomes": False,
            "new_ratio_thresholds": False,
            "pair_dropping": False,
            "pair_specific_rules": False,
            "pair_weighting": False,
            "strategy_selection": False,
            "validation_access": False,
            "reserved_final_open": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
        },
    }
