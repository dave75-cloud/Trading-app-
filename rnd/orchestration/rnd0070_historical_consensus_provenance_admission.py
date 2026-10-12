from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

PROHIBITED_MARKET_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}

AUTHORITY_FALSE = {
    'consensus_acquisition_authority': False,
    'provider_purchase_authority': False,
    'strategy_outcome_open': False,
    'validation_open': False,
    'reserved_final_open': False,
    'prospective_outcomes_open': False,
    'promotion_authority': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'automatic_merge': False,
}


class RND0070Error(ValueError):
    pass


@dataclass(frozen=True)
class ConsensusCandidate:
    provider: str
    field_name: str
    semantic: str
    historical_point_in_time: bool
    provider_event_id: str
    link_key: str
    economy: str
    currency: str
    reference_period: str
    consensus: Optional[float]
    source_identity: str
    raw_hash: str
    coverage_start_year: int
    coverage_end_year: int
    captured_at_utc: Optional[str] = None
    point_in_time_mechanism: str = ''


def _required(value: Any, label: str) -> str:
    s = str(value or '').strip()
    if not s:
        raise RND0070Error(f'missing {label}')
    return s


def _utc(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception as exc:
        raise RND0070Error('invalid timestamp') from exc
    if dt.tzinfo is None:
        raise RND0070Error('timestamp must be timezone-aware')
    return dt.astimezone(timezone.utc)


def validate_no_market_outcomes(payload: Any) -> None:
    if isinstance(payload, dict):
        lowered = {str(k).lower() for k in payload}
        if lowered.intersection(PROHIBITED_MARKET_FIELDS):
            raise RND0070Error('market outcome contamination prohibited')
        for value in payload.values():
            validate_no_market_outcomes(value)
    elif isinstance(payload, list):
        for value in payload:
            validate_no_market_outcomes(value)


def validate_candidate(c: ConsensusCandidate) -> None:
    for value, label in (
        (c.provider, 'provider'),
        (c.field_name, 'field name'),
        (c.semantic, 'semantic'),
        (c.provider_event_id, 'provider event id'),
        (c.link_key, 'link key'),
        (c.economy, 'economy'),
        (c.currency, 'currency'),
        (c.reference_period, 'reference period'),
        (c.source_identity, 'source identity'),
        (c.raw_hash, 'raw hash'),
    ):
        _required(value, label)
    if c.consensus is None:
        raise RND0070Error('missing consensus remains ineligible')
    if c.semantic != 'MARKET_CONSENSUS':
        raise RND0070Error('market-consensus semantic required')
    if not c.historical_point_in_time:
        raise RND0070Error('historical point-in-time proof required')
    if c.coverage_start_year > c.coverage_end_year:
        raise RND0070Error('invalid coverage interval')
    if c.captured_at_utc:
        _utc(c.captured_at_utc)
    elif not c.point_in_time_mechanism.strip():
        raise RND0070Error('capture timestamp or deterministic point-in-time mechanism required')


def classify_source(c: ConsensusCandidate, *, release_timestamp_utc: Optional[str] = None,
                    require_full_development: bool = False) -> str:
    try:
        validate_candidate(c)
    except RND0070Error as exc:
        msg = str(exc)
        if 'semantic' in msg:
            return 'REJECT_SEMANTIC_MISMATCH'
        if 'point-in-time' in msg:
            return 'REJECT_NOT_POINT_IN_TIME'
        if 'capture timestamp' in msg:
            return 'REJECT_CHRONOLOGY_UNPROVEN'
        raise

    if release_timestamp_utc:
        release = _utc(release_timestamp_utc)
        if c.captured_at_utc:
            captured = _utc(c.captured_at_utc)
            if captured >= release:
                return 'REJECT_CHRONOLOGY_UNPROVEN'
        elif not c.point_in_time_mechanism.strip():
            return 'REJECT_CHRONOLOGY_UNPROVEN'

    if require_full_development:
        if c.coverage_start_year > 2015 or c.coverage_end_year < 2020:
            return 'REJECT_DEVELOPMENT_COVERAGE'
        return 'FULL_DEVELOPMENT_CONSENSUS_SOURCE_ELIGIBLE'

    return 'PILOT_ELIGIBLE_CONSENSUS_SOURCE'


def trading_economics_semantic(field_name: str) -> str:
    name = (field_name or '').strip()
    if name == 'Forecast':
        return 'MARKET_CONSENSUS'
    if name == 'TEForecast':
        return 'MODEL_FORECAST'
    return 'UNKNOWN'


def admission_receipt(c: ConsensusCandidate, *, release_timestamp_utc: Optional[str] = None,
                      require_full_development: bool = False) -> Dict[str, Any]:
    status = classify_source(
        c,
        release_timestamp_utc=release_timestamp_utc,
        require_full_development=require_full_development,
    )
    out = {
        'provider': c.provider,
        'field_name': c.field_name,
        'semantic': c.semantic,
        'historical_point_in_time': c.historical_point_in_time,
        'provider_event_id': c.provider_event_id,
        'link_key': c.link_key,
        'economy': c.economy,
        'currency': c.currency,
        'reference_period': c.reference_period,
        'coverage_start_year': c.coverage_start_year,
        'coverage_end_year': c.coverage_end_year,
        'classification': status,
        'outcome_blind': True,
    }
    out.update(AUTHORITY_FALSE)
    return out


def architecture_status() -> Dict[str, Any]:
    out = {
        'timing_dependency_status': 'SOLVED_BY_RND0069_FOR_FROZEN_US_CPI_SAMPLE',
        'consensus_dependency_status': 'UNRESOLVED_PENDING_PROVIDER_PILOT',
        'preferred_pilot_candidate': 'TRADING_ECONOMICS',
        'preferred_candidate_is_architecture_dependency': False,
        'te_forecast_semantic': 'MARKET_CONSENSUS',
        'te_teforecast_semantic': 'MODEL_FORECAST',
        'development_partition': 'DEVELOPMENT_2015_2020',
    }
    out.update(AUTHORITY_FALSE)
    return out
