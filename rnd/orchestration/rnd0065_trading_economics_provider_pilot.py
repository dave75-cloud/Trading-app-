from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote
from urllib.request import Request, urlopen

from rnd0064_macro_event_provenance_guard import RawEvent, normalize_event, RND0064Error

PROVIDER = 'TRADING_ECONOMICS'
PILOT_START = datetime.fromisoformat('2019-01-01T00:00:00+00:00')
PILOT_END = datetime.fromisoformat('2019-04-01T00:00:00+00:00')
PILOT_COUNTRIES = ('United States', 'Australia', 'United Kingdom', 'Euro Area', 'Japan')
API_ROOT = 'https://api.tradingeconomics.com'
PROHIBITED_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}

class RND0065Error(ValueError):
    pass

@dataclass(frozen=True)
class BatchReceipt:
    provider: str
    request_identity: str
    request_url_redacted: str
    acquisition_timestamp_utc: str
    raw_sha256: str
    raw_record_count: int
    normalized_record_count: int
    rejected_record_count: int
    parser_version: str='RND0065_V1'


def _utc(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def build_request_url(api_key: str) -> str:
    if not api_key or api_key.strip() in {'', 'guest:guest'}:
        raise RND0065Error('explicit authorized Trading Economics API key required')
    countries = ','.join(PILOT_COUNTRIES)
    path = '/calendar/country/{}/{}/{}'.format(
        quote(countries, safe=','), PILOT_START.date().isoformat(), (PILOT_END.date()).isoformat()
    )
    return f'{API_ROOT}{path}?c={quote(api_key, safe="")}&f=json'


def redact_url(url: str) -> str:
    if '?c=' not in url:
        return url
    prefix, tail = url.split('?c=', 1)
    rest = ''
    if '&' in tail:
        _, rest = tail.split('&', 1)
        rest = '&' + rest
    return prefix + '?c=REDACTED' + rest


def request_identity(url: str) -> str:
    return sha256(redact_url(url).encode('utf-8')).hexdigest()


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(',', '')
    if not s or s.lower() in {'null','none','nan','n/a','na','-'}:
        return None
    s = s.replace('%', '')
    m = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([KkMmBbTt])?', s)
    if not m:
        raise RND0065Error(f'unparseable macro numeric value: {value!r}')
    num = float(m.group(1))
    suffix = (m.group(2) or '').upper()
    scale = {'':1.0,'K':1e3,'M':1e6,'B':1e9,'T':1e12}[suffix]
    return num * scale


def _precision(row: Dict[str, Any]) -> str:
    span = str(row.get('DateSpan', '')).strip()
    if span == '0':
        return 'EXACT'
    if span == '1':
        return 'ESTIMATED'
    return 'TENTATIVE'


def _series(row: Dict[str, Any]) -> str:
    return str(row.get('Ticker') or row.get('Symbol') or row.get('Category') or row.get('Event') or '').strip()


def _event_id(row: Dict[str, Any]) -> str:
    return str(row.get('CalendarId') or row.get('CalendarID') or '').strip()


def _source_identity(row: Dict[str, Any]) -> str:
    src = str(row.get('Source') or '').strip()
    src_url = str(row.get('SourceURL') or '').strip()
    return ' | '.join(x for x in (src, src_url) if x)


def validate_raw_row_no_market_outcomes(row: Dict[str, Any]) -> None:
    lowered = {str(k).lower() for k in row}
    if lowered.intersection(PROHIBITED_FIELDS):
        raise RND0065Error('market outcome contamination in provider row')


def normalize_te_row(row: Dict[str, Any], *, raw_hash: str, seen_ids: set) -> Dict[str, Any]:
    validate_raw_row_no_market_outcomes(row)
    economy = str(row.get('Country') or '').strip()
    if economy not in PILOT_COUNTRIES:
        raise RND0065Error('economy outside frozen pilot scope')
    ts_raw = str(row.get('Date') or '').strip()
    if not ts_raw:
        raise RND0065Error('missing release timestamp')
    ts = _utc(ts_raw)
    if not (PILOT_START <= ts < PILOT_END):
        raise RND0065Error('release timestamp outside frozen pilot window')
    event_id = _event_id(row)
    series = _series(row)
    source_identity = _source_identity(row)
    if not event_id or not series or not source_identity:
        raise RND0065Error('missing provider identity/series/source')

    event = RawEvent(
        provider=PROVIDER,
        provider_event_id=event_id,
        event_series=series,
        economy=economy,
        currency=str(row.get('Currency') or '').strip(),
        scheduled_timestamp=ts.isoformat().replace('+00:00','Z'),
        timestamp_precision=_precision(row),
        actual_as_released=_parse_number(row.get('ActualValue', row.get('Actual'))),
        consensus=_parse_number(row.get('ForecastValue', row.get('Forecast'))),
        previous=_parse_number(row.get('PreviousValue', row.get('Previous'))),
        revised_previous=_parse_number(row.get('Revised')),
        unit=str(row.get('Unit') or '').strip(),
        reference_period=str(row.get('Reference') or row.get('ReferenceDate') or '').strip(),
        raw_hash=raw_hash,
        source_identity=source_identity,
        partition='DEVELOPMENT_2015_2020',
    )
    out = normalize_event(event, seen_ids=seen_ids)
    out['provider_last_update'] = str(row.get('LastUpdate') or '').strip()
    out['provider_date_span'] = str(row.get('DateSpan') or '').strip()
    out['provider_importance'] = row.get('Importance')
    out['provider_request_scope'] = 'RND0065_FIXED_2019Q1_FIVE_ECONOMIES'
    out['surprise_eligible_inputs_present'] = bool(out['exact_time_eligible'] and out['consensus_available'] and out['actual_available'])
    return out


def process_payload(payload: Any, *, request_url: str, acquisition_timestamp_utc: str) -> Tuple[List[Dict[str, Any]], BatchReceipt, List[Dict[str, str]]]:
    if not isinstance(payload, list):
        raise RND0065Error('Trading Economics payload must be a list')
    raw_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    raw_hash = sha256(raw_bytes).hexdigest()
    seen: set = set()
    normalized: List[Dict[str, Any]] = []
    rejected: List[Dict[str, str]] = []
    for i, row in enumerate(payload):
        if not isinstance(row, dict):
            rejected.append({'index':str(i),'reason':'NON_OBJECT_RECORD'})
            continue
        try:
            normalized.append(normalize_te_row(row, raw_hash=raw_hash, seen_ids=seen))
        except (RND0065Error, RND0064Error, ValueError) as exc:
            rejected.append({'index':str(i),'reason':str(exc)})
    receipt = BatchReceipt(
        provider=PROVIDER,
        request_identity=request_identity(request_url),
        request_url_redacted=redact_url(request_url),
        acquisition_timestamp_utc=_utc(acquisition_timestamp_utc).isoformat().replace('+00:00','Z'),
        raw_sha256=raw_hash,
        raw_record_count=len(payload),
        normalized_record_count=len(normalized),
        rejected_record_count=len(rejected),
    )
    return normalized, receipt, rejected


def fetch_live_payload(*, api_key: Optional[str]=None, timeout_seconds: int=30) -> Tuple[Any, str]:
    key = api_key or os.environ.get('TRADING_ECONOMICS_API_KEY', '')
    url = build_request_url(key)
    req = Request(url, headers={'User-Agent':'Trading-RND0065/1.0','Accept':'application/json'})
    with urlopen(req, timeout=timeout_seconds) as response:
        status = getattr(response, 'status', 200)
        if status != 200:
            raise RND0065Error(f'provider HTTP status {status}')
        body = response.read()
    try:
        payload = json.loads(body.decode('utf-8'))
    except Exception as exc:
        raise RND0065Error('invalid JSON response') from exc
    return payload, url


def authority_firewall() -> Dict[str, bool]:
    return {
        'strategy_outcome_open':False,
        'validation_open':False,
        'reserved_final_open':False,
        'prospective_outcomes_open':False,
        'promotion_authority':False,
        'broker_write_authority':False,
        'capital_authority':False,
        'live_execution_authority':False,
        'automatic_merge':False,
    }
