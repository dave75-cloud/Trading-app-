from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Optional

from rnd0064_macro_event_provenance_guard import RawEvent, normalize_event, RND0064Error

COMPOSITE_PROVIDER = 'COMPOSITE_FRED_ALFRED'
FRED_FAMILY = {'FRED', 'ALFRED', 'FRED_ALFRED'}
PROHIBITED_MARKET_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}


class RND0066Error(ValueError):
    pass


@dataclass(frozen=True)
class FredVintageEvidence:
    series_id: str
    link_key: str
    observation_date: str
    vintage_date: str
    value: Optional[float]
    unit: str
    reference_period: str
    economy: str
    currency: str
    raw_hash: str
    source_identity: str
    initial_release: bool


@dataclass(frozen=True)
class TimingEvidence:
    provider: str
    provider_event_id: str
    link_key: str
    event_series: str
    economy: str
    currency: str
    reference_period: str
    scheduled_timestamp: str
    timestamp_precision: str
    raw_hash: str
    source_identity: str
    cancelled: bool = False
    rescheduled_from: str = ''


@dataclass(frozen=True)
class ConsensusEvidence:
    provider: str
    provider_event_id: str
    link_key: str
    economy: str
    currency: str
    reference_period: str
    consensus: Optional[float]
    captured_at_utc: str
    semantic: str
    historical_point_in_time: bool
    raw_hash: str
    source_identity: str


def _utc(s: str) -> datetime:
    if not s:
        raise RND0066Error('missing timestamp')
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise RND0066Error('timestamp must be timezone-aware')
    return d.astimezone(timezone.utc)


def _date_only(s: str) -> date:
    if not s or 'T' in s or ' ' in s:
        raise RND0066Error('FRED vintage must remain date-level evidence')
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise RND0066Error('invalid FRED vintage date') from exc


def _required(value: str, label: str) -> str:
    if not str(value).strip():
        raise RND0066Error(f'missing {label}')
    return str(value).strip()


def validate_fred_evidence(e: FredVintageEvidence) -> None:
    for value, label in (
        (e.series_id, 'FRED series id'), (e.link_key, 'link key'),
        (e.observation_date, 'observation date'), (e.vintage_date, 'vintage date'),
        (e.unit, 'unit'), (e.reference_period, 'reference period'),
        (e.economy, 'economy'), (e.currency, 'currency'),
        (e.raw_hash, 'raw hash'), (e.source_identity, 'source identity'),
    ):
        _required(value, label)
    _date_only(e.observation_date)
    _date_only(e.vintage_date)


def backbone_record(e: FredVintageEvidence) -> Dict[str, Any]:
    validate_fred_evidence(e)
    return {
        'provider_role': 'OFFICIAL_VALUE_REVISION_BACKBONE',
        'provider': 'FRED_ALFRED',
        'series_id': e.series_id,
        'link_key': e.link_key,
        'observation_date': e.observation_date,
        'vintage_date': e.vintage_date,
        'value': e.value,
        'initial_release': e.initial_release,
        'actual_as_released_candidate': e.value if e.initial_release else None,
        'timestamp_precision': 'DATE_ONLY',
        'exact_time_eligible': False,
        'consensus_available': False,
        'surprise_eligible_inputs_present': False,
        'eligibility_state': 'BACKBONE_ONLY',
        'raw_hash': e.raw_hash,
        'source_identity': e.source_identity,
    }


def _validate_join(actual: FredVintageEvidence, timing: TimingEvidence, consensus: ConsensusEvidence) -> None:
    validate_fred_evidence(actual)
    if not actual.initial_release or actual.value is None:
        raise RND0066Error('initial-release actual required')
    if timing.provider.strip().upper() in FRED_FAMILY:
        raise RND0066Error('FRED/ALFRED date evidence cannot supply exact M5 timing')
    if timing.timestamp_precision != 'EXACT':
        raise RND0066Error('independently proven exact timing required')
    if timing.cancelled:
        raise RND0066Error('cancelled event not surprise eligible')
    if consensus.provider.strip().upper() in FRED_FAMILY:
        raise RND0066Error('FRED/ALFRED cannot supply market consensus')
    if consensus.semantic != 'MARKET_CONSENSUS':
        raise RND0066Error('market-consensus semantic required')
    if not consensus.historical_point_in_time:
        raise RND0066Error('historical point-in-time consensus required')
    if consensus.consensus is None:
        raise RND0066Error('missing consensus stays ineligible')

    for obj, label in ((timing, 'timing'), (consensus, 'consensus')):
        for name in ('provider','provider_event_id','link_key','economy','currency','reference_period','raw_hash','source_identity'):
            _required(getattr(obj, name), f'{label} {name}')

    if not timing.event_series:
        raise RND0066Error('missing timing event series')
    if actual.link_key != timing.link_key or actual.link_key != consensus.link_key:
        raise RND0066Error('cross-source link-key mismatch')
    if actual.economy != timing.economy or actual.economy != consensus.economy:
        raise RND0066Error('cross-source economy mismatch')
    if actual.currency != timing.currency or actual.currency != consensus.currency:
        raise RND0066Error('cross-source currency mismatch')
    if actual.reference_period != timing.reference_period or actual.reference_period != consensus.reference_period:
        raise RND0066Error('cross-source reference-period mismatch')

    scheduled = _utc(timing.scheduled_timestamp)
    captured = _utc(consensus.captured_at_utc)
    if captured >= scheduled:
        raise RND0066Error('consensus must be captured strictly before release')


def _composite_event_id(actual: FredVintageEvidence, timing: TimingEvidence) -> str:
    material = '|'.join([
        actual.link_key, actual.series_id, actual.observation_date,
        timing.provider, timing.provider_event_id,
        _utc(timing.scheduled_timestamp).isoformat(),
    ])
    return sha256(material.encode('utf-8')).hexdigest()[:24]


def compose_event(actual: FredVintageEvidence, timing: TimingEvidence, consensus: ConsensusEvidence,
                  *, seen_ids: Optional[set] = None,
                  extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _validate_join(actual, timing, consensus)
    if extra_fields and any(k in PROHIBITED_MARKET_FIELDS for k in extra_fields):
        raise RND0066Error('market outcome field prohibited')

    combined_raw_hash = sha256('|'.join([
        actual.raw_hash, timing.raw_hash, consensus.raw_hash
    ]).encode('utf-8')).hexdigest()
    composite_source = ' || '.join([
        f'ACTUAL={actual.source_identity}',
        f'TIMING={timing.provider}:{timing.source_identity}',
        f'CONSENSUS={consensus.provider}:{consensus.source_identity}',
    ])

    raw = RawEvent(
        provider=COMPOSITE_PROVIDER,
        provider_event_id=_composite_event_id(actual, timing),
        event_series=actual.link_key,
        economy=actual.economy,
        currency=actual.currency,
        scheduled_timestamp=_utc(timing.scheduled_timestamp).isoformat().replace('+00:00', 'Z'),
        timestamp_precision='EXACT',
        actual_as_released=actual.value,
        consensus=consensus.consensus,
        previous=None,
        revised_previous=None,
        unit=actual.unit,
        reference_period=actual.reference_period,
        raw_hash=combined_raw_hash,
        source_identity=composite_source,
        cancelled=False,
        rescheduled_from=timing.rescheduled_from,
        partition='DEVELOPMENT_2015_2020',
    )
    try:
        out = normalize_event(raw, seen_ids=seen_ids, extra_fields=extra_fields)
    except RND0064Error as exc:
        raise RND0066Error(str(exc)) from exc

    out['fred_series_id'] = actual.series_id
    out['fred_observation_date'] = actual.observation_date
    out['fred_initial_vintage_date'] = actual.vintage_date
    out['timing_provider'] = timing.provider
    out['timing_provider_event_id'] = timing.provider_event_id
    out['consensus_provider'] = consensus.provider
    out['consensus_provider_event_id'] = consensus.provider_event_id
    out['consensus_captured_at_utc'] = _utc(consensus.captured_at_utc).isoformat().replace('+00:00', 'Z')
    out['field_provenance'] = {
        'actual_as_released': 'FRED_ALFRED_INITIAL_RELEASE',
        'revision_lineage': 'FRED_ALFRED',
        'scheduled_timestamp_utc': timing.provider,
        'consensus': consensus.provider,
    }
    out['eligibility_state'] = 'SURPRISE_INPUT_ELIGIBLE'
    out['surprise_eligible_inputs_present'] = True
    if extra_fields:
        out.update(extra_fields)
    return out


def preserve_initial_actual(initial: FredVintageEvidence, later: FredVintageEvidence) -> float:
    validate_fred_evidence(initial)
    validate_fred_evidence(later)
    if not initial.initial_release:
        raise RND0066Error('first evidence is not initial release')
    if initial.series_id != later.series_id or initial.observation_date != later.observation_date:
        raise RND0066Error('revision lineage identity mismatch')
    if initial.value is None:
        raise RND0066Error('initial actual missing')
    return initial.value


def architecture_status() -> Dict[str, Any]:
    return {
        'fred_alfred_role': 'OFFICIAL_VALUE_REVISION_BACKBONE',
        'fred_exact_intraday_timing_authority': False,
        'fred_market_consensus_authority': False,
        'independent_exact_timing_required': True,
        'independent_point_in_time_consensus_required': True,
        'canonical_schema': 'RND0064',
        'development_partition': 'DEVELOPMENT_2015_2020',
        'acquisition_authority': False,
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
