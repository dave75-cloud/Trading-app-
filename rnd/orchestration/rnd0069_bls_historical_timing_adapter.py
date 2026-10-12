from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo

BLS_TZ = 'America/New_York'
UTC_TZ = 'UTC'
PILOT_LINK_KEY = 'US_CPI_HEADLINE'
PILOT_EVENT_SERIES = 'Consumer Price Index'
PILOT_ECONOMY = 'United States'
PILOT_CURRENCY = 'USD'
PILOT_SCOPE_ID = 'RND0069_US_CPI_2019Q1_BLS_TIMING_ONLY'
EXPECTED_LOCAL_TIME = '08:30'
EXPECTED_OBSERVATION_PERIODS = ('2019-01', '2019-02', '2019-03')

PROHIBITED_FIELDS = {
    'actual_as_released','consensus','fx_return','pnl','equity','drawdown',
    'hit_rate','win_rate','pair_rank','directional_response','strategy_signal',
    'strategy_outcome'
}

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


class RND0069Error(ValueError):
    pass


@dataclass(frozen=True)
class BLSScheduleEvidence:
    provider: str
    provider_event_id: str
    link_key: str
    event_series: str
    economy: str
    currency: str
    reference_period: str
    release_date: str
    local_time: str
    timezone_name: str
    scheduled_timestamp_utc: str
    timestamp_precision: str
    source_identity: str
    raw_hash: str
    pilot_scope_id: str = PILOT_SCOPE_ID


def _required(value: Any, label: str) -> str:
    s = str(value or '').strip()
    if not s:
        raise RND0069Error(f'missing {label}')
    return s


def _date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except Exception as exc:
        raise RND0069Error('release date must be YYYY-MM-DD') from exc


def _time(s: str) -> time:
    try:
        return time.fromisoformat(s)
    except Exception as exc:
        raise RND0069Error('local time must be HH:MM or HH:MM:SS') from exc


def eastern_to_utc(release_date: str, local_time: str) -> str:
    d = _date(release_date)
    t = _time(local_time)
    local = datetime.combine(d, t, tzinfo=ZoneInfo(BLS_TZ))
    return local.astimezone(ZoneInfo(UTC_TZ)).isoformat().replace('+00:00', 'Z')


def expected_utc_offset_hours(release_date: str, local_time: str = EXPECTED_LOCAL_TIME) -> int:
    d = _date(release_date)
    t = _time(local_time)
    local = datetime.combine(d, t, tzinfo=ZoneInfo(BLS_TZ))
    offset = local.utcoffset()
    if offset is None:
        raise RND0069Error('cannot determine Eastern offset')
    return int(offset.total_seconds() // 3600)


def validate_no_prohibited_fields(payload: Any) -> None:
    if isinstance(payload, dict):
        lowered = {str(k).lower() for k in payload}
        if lowered.intersection(PROHIBITED_FIELDS):
            raise RND0069Error('prohibited non-timing field present')
        for v in payload.values():
            validate_no_prohibited_fields(v)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            validate_no_prohibited_fields(v)


def normalize_schedule_row(row: Dict[str, Any], *, raw_hash: str, source_identity: str) -> BLSScheduleEvidence:
    validate_no_prohibited_fields(row)
    release = _required(row.get('release'), 'release')
    if release != PILOT_EVENT_SERIES:
        raise RND0069Error('unexpected BLS release family')

    release_date = _required(row.get('release_date'), 'release date')
    local_time = _required(row.get('local_time'), 'local time')
    reference_period = _required(row.get('reference_period'), 'reference period')
    if reference_period not in EXPECTED_OBSERVATION_PERIODS:
        raise RND0069Error('reference period outside frozen pilot')
    if local_time != EXPECTED_LOCAL_TIME:
        raise RND0069Error('frozen CPI pilot expects 08:30 Eastern')

    provider_event_id = _required(row.get('provider_event_id'), 'provider event id')
    raw_hash = _required(raw_hash, 'raw hash')
    source_identity = _required(source_identity, 'source identity')
    utc = eastern_to_utc(release_date, local_time)

    return BLSScheduleEvidence(
        provider='BLS_HISTORICAL_SCHEDULE',
        provider_event_id=provider_event_id,
        link_key=PILOT_LINK_KEY,
        event_series=PILOT_EVENT_SERIES,
        economy=PILOT_ECONOMY,
        currency=PILOT_CURRENCY,
        reference_period=reference_period,
        release_date=release_date,
        local_time=local_time,
        timezone_name=BLS_TZ,
        scheduled_timestamp_utc=utc,
        timestamp_precision='EXACT',
        source_identity=source_identity,
        raw_hash=raw_hash,
    )


def validate_frozen_triplet(records: Iterable[BLSScheduleEvidence]) -> List[BLSScheduleEvidence]:
    rows = list(records)
    if len(rows) != 3:
        raise RND0069Error('frozen pilot requires exactly three CPI timing records')
    if [r.reference_period for r in rows] != list(EXPECTED_OBSERVATION_PERIODS):
        raise RND0069Error('reference periods must be complete and ordered')
    ids = [r.provider_event_id for r in rows]
    if len(set(ids)) != len(ids):
        raise RND0069Error('duplicate provider event id')
    stamps = [r.scheduled_timestamp_utc for r in rows]
    if stamps != sorted(stamps):
        raise RND0069Error('release timestamps must be ascending')
    for r in rows:
        validate_record(r)
    return rows


def validate_record(r: BLSScheduleEvidence) -> None:
    if r.provider != 'BLS_HISTORICAL_SCHEDULE':
        raise RND0069Error('provider mismatch')
    if r.timestamp_precision != 'EXACT':
        raise RND0069Error('timestamp precision must be EXACT')
    if r.timezone_name != BLS_TZ:
        raise RND0069Error('timezone must remain America/New_York')
    if eastern_to_utc(r.release_date, r.local_time) != r.scheduled_timestamp_utc:
        raise RND0069Error('UTC conversion mismatch')
    if not r.raw_hash or not r.source_identity:
        raise RND0069Error('provenance required')


def timing_receipt(records: Iterable[BLSScheduleEvidence]) -> Dict[str, Any]:
    rows = validate_frozen_triplet(records)
    material = '|'.join(
        f'{r.provider_event_id}:{r.reference_period}:{r.scheduled_timestamp_utc}:{r.raw_hash}'
        for r in rows
    )
    out = {
        'pilot_scope_id': PILOT_SCOPE_ID,
        'record_count': len(rows),
        'reference_periods': [r.reference_period for r in rows],
        'scheduled_timestamps_utc': [r.scheduled_timestamp_utc for r in rows],
        'bundle_sha256': sha256(material.encode('utf-8')).hexdigest(),
        'timing_source': 'BLS_HISTORICAL_SCHEDULE',
        'timing_source_primary_official': True,
        'timestamp_precision': 'EXACT',
        'timezone_semantics': BLS_TZ,
        'consensus_present': False,
        'actual_present': False,
        'fx_outcomes_present': False,
        'surprise_input_eligible': False,
    }
    out.update(AUTHORITY_FALSE)
    return out


def authority_firewall() -> Dict[str, bool]:
    return dict(AUTHORITY_FALSE)


def evidence_dict(r: BLSScheduleEvidence) -> Dict[str, Any]:
    return asdict(r)
