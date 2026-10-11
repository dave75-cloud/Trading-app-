from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rnd0066_fred_alfred_macro_provenance_backbone import FredVintageEvidence

API_ROOT = 'https://api.stlouisfed.org/fred'
PILOT_SERIES_ID = 'CPIAUCSL'
PILOT_LINK_KEY = 'US_CPI_HEADLINE'
PILOT_ECONOMY = 'United States'
PILOT_CURRENCY = 'USD'
PILOT_OBSERVATION_START = '2019-01-01'
PILOT_OBSERVATION_END = '2019-03-01'
PILOT_REALTIME_START = '2019-01-01'
PILOT_REALTIME_END = '2019-12-31'
PILOT_SCOPE_ID = 'RND0067_US_CPI_2019Q1_STRUCTURE_ONLY'
KEY_RE = re.compile(r'^[a-z0-9]{32}$')

PROHIBITED_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
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


class RND0067Error(ValueError):
    pass


@dataclass(frozen=True)
class AcquisitionReceipt:
    endpoint_role: str
    series_id: str
    pilot_scope_id: str
    request_identity: str
    request_url_redacted: str
    acquisition_timestamp_utc: str
    raw_sha256: str
    raw_record_count: int
    parser_version: str = 'RND0067_V1'


@dataclass(frozen=True)
class PilotBundle:
    metadata: Dict[str, Any]
    initial_release_records: Tuple[FredVintageEvidence, ...]
    vintage_dates: Tuple[str, ...]
    receipts: Tuple[AcquisitionReceipt, ...]
    classification: str


def _utc(s: str) -> str:
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise RND0067Error('acquisition timestamp must be timezone-aware')
    return d.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def validate_api_key(api_key: str) -> str:
    key = (api_key or '').strip()
    if not KEY_RE.fullmatch(key):
        raise RND0067Error('explicit 32-character lowercase alphanumeric FRED API key required')
    return key


def _build_url(path: str, api_key: str, **params: Any) -> str:
    key = validate_api_key(api_key)
    q = {'api_key': key, 'file_type': 'json'}
    q.update(params)
    return f'{API_ROOT}/{path}?{urlencode(q)}'


def build_metadata_url(api_key: str) -> str:
    return _build_url('series', api_key, series_id=PILOT_SERIES_ID)


def build_initial_release_url(api_key: str) -> str:
    return _build_url(
        'series/observations', api_key,
        series_id=PILOT_SERIES_ID,
        observation_start=PILOT_OBSERVATION_START,
        observation_end=PILOT_OBSERVATION_END,
        realtime_start=PILOT_REALTIME_START,
        realtime_end=PILOT_REALTIME_END,
        output_type='4',
        sort_order='asc',
    )


def build_vintage_dates_url(api_key: str) -> str:
    return _build_url(
        'series/vintagedates', api_key,
        series_id=PILOT_SERIES_ID,
        realtime_start=PILOT_REALTIME_START,
        realtime_end=PILOT_REALTIME_END,
        sort_order='asc',
    )


def redact_url(url: str) -> str:
    parts = url.split('?', 1)
    if len(parts) != 2:
        return url
    base, query = parts
    pairs = []
    for item in query.split('&'):
        if item.startswith('api_key='):
            pairs.append('api_key=REDACTED')
        else:
            pairs.append(item)
    return base + '?' + '&'.join(pairs)


def request_identity(url: str) -> str:
    return sha256(redact_url(url).encode('utf-8')).hexdigest()


def _raw_hash(payload: Any) -> str:
    b = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return sha256(b).hexdigest()


def validate_no_market_outcomes(payload: Any) -> None:
    if isinstance(payload, dict):
        lowered = {str(k).lower() for k in payload}
        if lowered.intersection(PROHIBITED_FIELDS):
            raise RND0067Error('market outcome contamination in FRED payload')
        for v in payload.values():
            validate_no_market_outcomes(v)
    elif isinstance(payload, list):
        for v in payload:
            validate_no_market_outcomes(v)


def _receipt(role: str, payload: Any, request_url: str, acquisition_timestamp_utc: str, count: int) -> AcquisitionReceipt:
    return AcquisitionReceipt(
        endpoint_role=role,
        series_id=PILOT_SERIES_ID,
        pilot_scope_id=PILOT_SCOPE_ID,
        request_identity=request_identity(request_url),
        request_url_redacted=redact_url(request_url),
        acquisition_timestamp_utc=_utc(acquisition_timestamp_utc),
        raw_sha256=_raw_hash(payload),
        raw_record_count=count,
    )


def process_metadata_payload(payload: Any, *, request_url: str, acquisition_timestamp_utc: str) -> Tuple[Dict[str, Any], AcquisitionReceipt]:
    validate_no_market_outcomes(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get('seriess'), list):
        raise RND0067Error('invalid FRED series metadata payload')
    rows = payload['seriess']
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise RND0067Error('pilot requires exactly one metadata record')
    row = rows[0]
    if str(row.get('id') or '') != PILOT_SERIES_ID:
        raise RND0067Error('metadata series identity mismatch')
    units = str(row.get('units') or '').strip()
    frequency = str(row.get('frequency') or '').strip()
    title = str(row.get('title') or '').strip()
    if not units or not frequency or not title:
        raise RND0067Error('metadata missing title/frequency/units')
    out = {
        'series_id': PILOT_SERIES_ID,
        'title': title,
        'frequency': frequency,
        'units': units,
        'seasonal_adjustment': str(row.get('seasonal_adjustment') or '').strip(),
        'source_identity': f'FRED_SERIES:{PILOT_SERIES_ID}',
        'pilot_scope_id': PILOT_SCOPE_ID,
    }
    return out, _receipt('SERIES_METADATA', payload, request_url, acquisition_timestamp_utc, 1)


def _parse_value(value: Any) -> Optional[float]:
    s = str(value).strip()
    if s in {'', '.'}:
        return None
    try:
        return float(s)
    except ValueError as exc:
        raise RND0067Error(f'unparseable FRED value: {value!r}') from exc


def process_initial_release_payload(payload: Any, *, metadata: Dict[str, Any], request_url: str,
                                    acquisition_timestamp_utc: str) -> Tuple[List[FredVintageEvidence], AcquisitionReceipt]:
    validate_no_market_outcomes(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get('observations'), list):
        raise RND0067Error('invalid FRED observations payload')
    if metadata.get('series_id') != PILOT_SERIES_ID or not metadata.get('units'):
        raise RND0067Error('validated pilot metadata required before observations')
    rows = payload['observations']
    out: List[FredVintageEvidence] = []
    raw_hash = _raw_hash(payload)
    for row in rows:
        if not isinstance(row, dict):
            raise RND0067Error('non-object observation record')
        obs_date = str(row.get('date') or '').strip()
        vintage_date = str(row.get('realtime_start') or '').strip()
        if not obs_date or not vintage_date:
            raise RND0067Error('observation missing date or initial-release realtime_start')
        if not (PILOT_OBSERVATION_START <= obs_date <= PILOT_OBSERVATION_END):
            raise RND0067Error('observation outside frozen pilot window')
        value = _parse_value(row.get('value'))
        if value is None:
            raise RND0067Error('missing initial-release value in frozen pilot')
        out.append(FredVintageEvidence(
            series_id=PILOT_SERIES_ID,
            link_key=PILOT_LINK_KEY,
            observation_date=obs_date,
            vintage_date=vintage_date,
            value=value,
            unit=str(metadata['units']),
            reference_period=obs_date[:7],
            economy=PILOT_ECONOMY,
            currency=PILOT_CURRENCY,
            raw_hash=raw_hash,
            source_identity=f'FRED:{PILOT_SERIES_ID}:output_type=4',
            initial_release=True,
        ))
    return out, _receipt('INITIAL_RELEASE_OBSERVATIONS', payload, request_url, acquisition_timestamp_utc, len(rows))


def process_vintage_dates_payload(payload: Any, *, request_url: str,
                                  acquisition_timestamp_utc: str) -> Tuple[List[str], AcquisitionReceipt]:
    validate_no_market_outcomes(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get('vintage_dates'), list):
        raise RND0067Error('invalid FRED vintage-date payload')
    dates = [str(x).strip() for x in payload['vintage_dates']]
    if not dates or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) for d in dates):
        raise RND0067Error('vintage-date evidence missing or malformed')
    if dates != sorted(dates):
        raise RND0067Error('vintage dates must be ascending')
    if len(set(dates)) != len(dates):
        raise RND0067Error('duplicate vintage dates prohibited')
    return dates, _receipt('VINTAGE_DATES', payload, request_url, acquisition_timestamp_utc, len(dates))


def classify_bundle(metadata: Dict[str, Any], initial_records: List[FredVintageEvidence], vintage_dates: List[str]) -> str:
    if metadata.get('series_id') != PILOT_SERIES_ID:
        return 'PILOT_FAIL_SERIES_IDENTITY'
    if not initial_records:
        return 'PILOT_INCONCLUSIVE_NO_INITIAL_RELEASE_ROWS'
    if not vintage_dates:
        return 'PILOT_INCONCLUSIVE_NO_VINTAGE_LINEAGE'
    if any(not r.initial_release for r in initial_records):
        return 'PILOT_FAIL_INITIAL_RELEASE_SEMANTICS'
    return 'PILOT_STRUCTURAL_FEASIBILITY_CONFIRMED'


def build_bundle(metadata: Dict[str, Any], initial_records: List[FredVintageEvidence], vintage_dates: List[str],
                 receipts: List[AcquisitionReceipt]) -> PilotBundle:
    if len(receipts) != 3:
        raise RND0067Error('exactly three acquisition receipts required')
    identities = {r.request_identity for r in receipts}
    if len(identities) != 3:
        raise RND0067Error('request identities must be distinct by endpoint role')
    return PilotBundle(
        metadata=dict(metadata),
        initial_release_records=tuple(initial_records),
        vintage_dates=tuple(vintage_dates),
        receipts=tuple(receipts),
        classification=classify_bundle(metadata, initial_records, vintage_dates),
    )


def fetch_json(url: str, *, timeout_seconds: int = 30) -> Any:
    req = Request(url, headers={'User-Agent': 'Trading-RND0067/1.0', 'Accept': 'application/json'})
    with urlopen(req, timeout=timeout_seconds) as response:
        status = getattr(response, 'status', 200)
        if status != 200:
            raise RND0067Error(f'FRED HTTP status {status}')
        body = response.read()
    try:
        return json.loads(body.decode('utf-8'))
    except Exception as exc:
        raise RND0067Error('invalid FRED JSON response') from exc


def fetch_live_bundle(*, api_key: Optional[str] = None, acquisition_timestamp_utc: Optional[str] = None) -> PilotBundle:
    key = api_key or os.environ.get('FRED_API_KEY', '')
    validate_api_key(key)
    ts = acquisition_timestamp_utc or datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    metadata_url = build_metadata_url(key)
    initial_url = build_initial_release_url(key)
    vintage_url = build_vintage_dates_url(key)
    metadata_payload = fetch_json(metadata_url)
    metadata, r1 = process_metadata_payload(metadata_payload, request_url=metadata_url, acquisition_timestamp_utc=ts)
    initial_payload = fetch_json(initial_url)
    initial, r2 = process_initial_release_payload(initial_payload, metadata=metadata, request_url=initial_url, acquisition_timestamp_utc=ts)
    vintage_payload = fetch_json(vintage_url)
    vintages, r3 = process_vintage_dates_payload(vintage_payload, request_url=vintage_url, acquisition_timestamp_utc=ts)
    return build_bundle(metadata, initial, vintages, [r1, r2, r3])


def bundle_receipt_dict(bundle: PilotBundle) -> Dict[str, Any]:
    out = {
        'pilot_scope_id': PILOT_SCOPE_ID,
        'series_id': PILOT_SERIES_ID,
        'classification': bundle.classification,
        'initial_release_record_count': len(bundle.initial_release_records),
        'vintage_date_count': len(bundle.vintage_dates),
        'receipts': [asdict(r) for r in bundle.receipts],
        'fred_exact_intraday_timing_authority': False,
        'fred_market_consensus_authority': False,
    }
    out.update(AUTHORITY_FALSE)
    return out


def authority_firewall() -> Dict[str, bool]:
    return dict(AUTHORITY_FALSE)
