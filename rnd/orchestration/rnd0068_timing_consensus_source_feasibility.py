from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


class RND0068Error(ValueError):
    pass


@dataclass(frozen=True)
class SourceEvidence:
    provider: str
    role: str
    primary_source: bool
    exact_historical_time: bool
    timezone_context: bool
    historical_start_year: int | None
    historical_end_year: int | None
    consensus_is_market_survey: bool
    point_in_time_consensus: bool
    distinct_model_forecast_field: bool
    deterministic_event_identity: bool
    reference_period_available: bool
    pre_release_proof_available: bool
    purchase_required: bool


AUTHORITY_FALSE = {
    'strategy_outcome_open': False,
    'validation_open': False,
    'reserved_final_open': False,
    'prospective_outcomes_open': False,
    'promotion_authority': False,
    'provider_purchase_authority': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'automatic_merge': False,
}


def timing_classification(e: SourceEvidence) -> str:
    if e.role != 'TIMING':
        raise RND0068Error('timing classifier requires TIMING role')
    if not e.deterministic_event_identity:
        return 'TIMING_REJECT_IDENTITY_INSUFFICIENT'
    if not e.exact_historical_time:
        return 'TIMING_REJECT_NOT_EXACT'
    if not e.timezone_context:
        return 'TIMING_REJECT_TIMEZONE_CONTEXT_MISSING'
    if e.primary_source:
        return 'TIMING_ADMISSIBLE_PRIMARY_SOURCE'
    return 'TIMING_ADMISSIBLE_SECONDARY_SOURCE_REQUIRES_PROVENANCE_REVIEW'


def consensus_classification(e: SourceEvidence, *, required_start_year: int = 2015,
                             required_end_year: int = 2020) -> str:
    if e.role != 'CONSENSUS':
        raise RND0068Error('consensus classifier requires CONSENSUS role')
    if e.historical_start_year is None or e.historical_end_year is None:
        return 'CONSENSUS_UNRESOLVED_COVERAGE'
    if e.historical_start_year > required_start_year or e.historical_end_year < required_end_year:
        return 'CONSENSUS_REJECT_PRIMARY_COVERAGE_INSUFFICIENT'
    if not e.consensus_is_market_survey:
        return 'CONSENSUS_REJECT_NOT_MARKET_SURVEY'
    if not e.point_in_time_consensus:
        return 'CONSENSUS_UNRESOLVED_POINT_IN_TIME'
    if not e.deterministic_event_identity or not e.reference_period_available:
        return 'CONSENSUS_REJECT_IDENTITY_INSUFFICIENT'
    if not e.pre_release_proof_available:
        return 'CONSENSUS_REJECT_PRE_RELEASE_PROOF_MISSING'
    return 'CONSENSUS_PILOT_ADMISSIBLE'


def provider_registry() -> Dict[str, SourceEvidence]:
    return {
        'BLS_HISTORICAL_SCHEDULE': SourceEvidence(
            provider='BLS_HISTORICAL_SCHEDULE', role='TIMING', primary_source=True,
            exact_historical_time=True, timezone_context=True,
            historical_start_year=2015, historical_end_year=2020,
            consensus_is_market_survey=False, point_in_time_consensus=False,
            distinct_model_forecast_field=False, deterministic_event_identity=True,
            reference_period_available=True, pre_release_proof_available=True,
            purchase_required=False,
        ),
        'TRADING_ECONOMICS': SourceEvidence(
            provider='TRADING_ECONOMICS', role='CONSENSUS', primary_source=False,
            exact_historical_time=True, timezone_context=True,
            historical_start_year=2015, historical_end_year=2020,
            consensus_is_market_survey=True, point_in_time_consensus=True,
            distinct_model_forecast_field=True, deterministic_event_identity=True,
            reference_period_available=True, pre_release_proof_available=True,
            purchase_required=True,
        ),
        'EODHD': SourceEvidence(
            provider='EODHD', role='CONSENSUS', primary_source=False,
            exact_historical_time=True, timezone_context=True,
            historical_start_year=2020, historical_end_year=2026,
            consensus_is_market_survey=True, point_in_time_consensus=False,
            distinct_model_forecast_field=False, deterministic_event_identity=False,
            reference_period_available=True, pre_release_proof_available=False,
            purchase_required=True,
        ),
        'FMP': SourceEvidence(
            provider='FMP', role='CONSENSUS', primary_source=False,
            exact_historical_time=True, timezone_context=True,
            historical_start_year=2015, historical_end_year=2020,
            consensus_is_market_survey=True, point_in_time_consensus=False,
            distinct_model_forecast_field=False, deterministic_event_identity=False,
            reference_period_available=False, pre_release_proof_available=False,
            purchase_required=False,
        ),
        'FINNHUB': SourceEvidence(
            provider='FINNHUB', role='CONSENSUS', primary_source=False,
            exact_historical_time=True, timezone_context=True,
            historical_start_year=None, historical_end_year=None,
            consensus_is_market_survey=True, point_in_time_consensus=False,
            distinct_model_forecast_field=False, deterministic_event_identity=False,
            reference_period_available=False, pre_release_proof_available=False,
            purchase_required=True,
        ),
    }


def preferred_timing_source(registry: Dict[str, SourceEvidence] | None = None) -> str:
    r = registry or provider_registry()
    candidates = [e for e in r.values() if e.role == 'TIMING' and timing_classification(e) == 'TIMING_ADMISSIBLE_PRIMARY_SOURCE']
    if not candidates:
        raise RND0068Error('no admissible primary timing source')
    free = [e for e in candidates if not e.purchase_required]
    if free:
        return sorted(e.provider for e in free)[0]
    return sorted(e.provider for e in candidates)[0]


def consensus_pilot_candidates(registry: Dict[str, SourceEvidence] | None = None) -> tuple[str, ...]:
    r = registry or provider_registry()
    out = []
    for e in r.values():
        if e.role == 'CONSENSUS' and consensus_classification(e) == 'CONSENSUS_PILOT_ADMISSIBLE':
            out.append(e.provider)
    return tuple(sorted(out))


def selection_firewall(provider: str, *, based_on_fx_outcomes: bool,
                       purchase_authorized: bool = False) -> Dict[str, object]:
    if based_on_fx_outcomes:
        raise RND0068Error('provider selection may not use FX outcomes')
    if purchase_authorized:
        raise RND0068Error('RND-0068 does not authorize provider purchase')
    return {
        'provider': provider,
        'selection_basis': 'PROVENANCE_COVERAGE_POINT_IN_TIME_COST_ONLY',
        **AUTHORITY_FALSE,
    }


def assert_no_outcome_fields(fields: Iterable[str]) -> None:
    prohibited = {'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank','strategy_signal','strategy_outcome'}
    lowered = {str(x).lower() for x in fields}
    if lowered.intersection(prohibited):
        raise RND0068Error('market outcome field prohibited')


def architecture_status() -> Dict[str, object]:
    return {
        'preferred_us_timing_source': preferred_timing_source(),
        'consensus_pilot_candidates': consensus_pilot_candidates(),
        'development_interval': '2015-2020',
        'official_timing_first': True,
        'commercial_consensus_only_if_needed': True,
        **AUTHORITY_FALSE,
    }
