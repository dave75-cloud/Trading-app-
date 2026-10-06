#!/usr/bin/env python3
"""Predeclared structure classifier for RND-0060H."""
from rnd0060h_cross_sectional_dispersion_state import SYMBOLS, AUTHORIZED_YEARS, RND0060HError, spearman


def _req(ok, message):
    if not ok:
        raise RND0060HError(message)


def classify_observations(obs, exclusions=None):
    _req(isinstance(obs, list) and len(obs) >= 4, "at least four observations required")
    state=[r['cross_sectional_dispersion_state'] for r in obs]
    primary=[r['primary_mean_forward_relative_realized_range'] for r in obs]
    secondary=[r['secondary_forward_cross_sectional_return_dispersion'] for r in obs]
    per_symbol={s:spearman(state,[r['per_symbol_forward_relative_realized_range'][s] for r in obs]) for s in SYMBOLS}
    annual={}
    for year in sorted(AUTHORIZED_YEARS):
        rows=[r for r in obs if r['year']==year]
        _req(len(rows)>=2,f"{year}: insufficient annual observations")
        annual[year]=spearman([r['cross_sectional_dispersion_state'] for r in rows],[r['primary_mean_forward_relative_realized_range'] for r in rows])
    ordered=sorted(obs,key=lambda r:(r['cross_sectional_dispersion_state'],r['timestamp_utc']))
    q=len(ordered)//4
    bottom=ordered[:q]; top=ordered[-q:]
    quartile={
        'quartile_size':q,
        'bottom_quartile_mean_primary_response':sum(r['primary_mean_forward_relative_realized_range'] for r in bottom)/q,
        'top_quartile_mean_primary_response':sum(r['primary_mean_forward_relative_realized_range'] for r in top)/q,
    }
    aggregate=spearman(state,primary)
    positive_years=sum(v>0 for v in annual.values())
    positive_symbols=sum(v>0 for v in per_symbol.values())
    criteria={
        'aggregate_primary_spearman_gte_0_05':aggregate>=0.05,
        'at_least_4_of_6_annual_primary_spearman_positive':positive_years>=4,
        'at_least_3_of_4_symbol_forward_range_spearman_positive':positive_symbols>=3,
        'top_quartile_mean_primary_response_gt_bottom_quartile':quartile['top_quartile_mean_primary_response']>quartile['bottom_quartile_mean_primary_response'],
        'integrity_reconciliation_pass':True,
    }
    return {
        'classification':'CROSS_SECTIONAL_STRUCTURE_DETECTED' if all(criteria.values()) else 'NO_REPRODUCIBLE_STRUCTURE',
        'criteria':criteria,
        'eligible_observation_count':len(obs),
        'excluded_observation_count':len(exclusions or []),
        'aggregate_primary_spearman':aggregate,
        'aggregate_secondary_spearman':spearman(state,secondary),
        'annual_primary_spearman':annual,
        'positive_year_count':positive_years,
        'per_symbol_primary_spearman':per_symbol,
        'positive_symbol_count':positive_symbols,
        'quartile_diagnostic':quartile,
        'observations':obs,
        'exclusions':list(exclusions or []),
        'development_only':True,'trade_simulation':False,'pnl':False,'strategy_candidate':False,
        'validation_open':False,'final_test_open':False,'reserved_final_access':False,
        'broker_writes':False,'capital_authority':False,'automatic_promotion':False,
    }
