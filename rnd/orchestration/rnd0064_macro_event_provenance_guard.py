from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Optional

PROHIBITED_MARKET_FIELDS={
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}
PROTECTED_PARTITIONS={'VALIDATION_2021_2022','RESERVED_FINAL_2023_2024'}
PROTECTED_PROSPECTIVE={'Q003','RND0060QR'}

AUTHORITY_FALSE={
    'promotion_authority':False,
    'broker_write_authority':False,
    'capital_authority':False,
    'live_execution_authority':False,
    'automatic_merge':False,
}

class RND0064Error(ValueError):
    pass

@dataclass(frozen=True)
class RawEvent:
    provider: str
    provider_event_id: str
    event_series: str
    economy: str
    currency: str
    scheduled_timestamp: str
    timestamp_precision: str
    actual_as_released: Optional[float]
    consensus: Optional[float]
    previous: Optional[float]
    revised_previous: Optional[float]
    unit: str
    reference_period: str
    raw_hash: str
    source_identity: str
    cancelled: bool=False
    rescheduled_from: str=''
    partition: str='DEVELOPMENT_2015_2020'
    prospective_source: str=''


def _dt(s:str)->datetime:
    if not s:
        raise RND0064Error('missing timestamp')
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None:
        raise RND0064Error('timestamp must be timezone-aware')
    return d.astimezone(timezone.utc)


def canonical_event_id(e:RawEvent)->str:
    ts=_dt(e.scheduled_timestamp).isoformat().replace('+00:00','Z')
    return f'{e.provider}:{e.provider_event_id}:{e.event_series}:{ts}'


def normalize_event(e:RawEvent, *, seen_ids:Optional[set]=None, extra_fields:Optional[Dict[str,Any]]=None)->Dict[str,Any]:
    if not e.provider or not e.provider_event_id or not e.event_series:
        raise RND0064Error('missing provider/event identity')
    if not e.raw_hash or not e.source_identity:
        raise RND0064Error('missing provenance identity')
    if e.partition in PROTECTED_PARTITIONS:
        raise RND0064Error('protected partition prohibited')
    if e.partition != 'DEVELOPMENT_2015_2020':
        raise RND0064Error('nondevelopment partition prohibited')
    if e.prospective_source in PROTECTED_PROSPECTIVE:
        raise RND0064Error('prospective outcome contamination prohibited')
    if extra_fields and any(k in PROHIBITED_MARKET_FIELDS for k in extra_fields):
        raise RND0064Error('market outcome field prohibited')
    if e.timestamp_precision not in {'EXACT','ESTIMATED','TENTATIVE','NON_TIMED'}:
        raise RND0064Error('unknown timestamp precision')

    ts=_dt(e.scheduled_timestamp)
    cid=canonical_event_id(e)
    seen_ids=seen_ids if seen_ids is not None else set()
    if cid in seen_ids:
        raise RND0064Error('duplicate event identity')
    seen_ids.add(cid)

    exact_time_eligible=(e.timestamp_precision=='EXACT' and not e.cancelled)
    consensus_available=e.consensus is not None
    actual_available=e.actual_as_released is not None

    payload='|'.join([
        cid,e.economy,e.currency,ts.isoformat(),e.timestamp_precision,
        '' if e.actual_as_released is None else repr(e.actual_as_released),
        '' if e.consensus is None else repr(e.consensus),
        '' if e.previous is None else repr(e.previous),
        '' if e.revised_previous is None else repr(e.revised_previous),
        e.unit,e.reference_period,e.raw_hash,e.source_identity,str(e.cancelled),e.rescheduled_from
    ])
    normalized_hash=sha256(payload.encode('utf-8')).hexdigest()

    out={
        'canonical_event_id':cid,
        'provider':e.provider,
        'provider_event_id':e.provider_event_id,
        'event_series':e.event_series,
        'economy':e.economy,
        'currency':e.currency,
        'scheduled_timestamp_utc':ts.isoformat().replace('+00:00','Z'),
        'timestamp_precision':e.timestamp_precision,
        'actual_as_released':e.actual_as_released,
        'consensus':e.consensus,
        'previous':e.previous,
        'revised_previous':e.revised_previous,
        'unit':e.unit,
        'reference_period':e.reference_period,
        'cancelled':e.cancelled,
        'rescheduled_from':e.rescheduled_from,
        'consensus_available':consensus_available,
        'actual_available':actual_available,
        'exact_time_eligible':exact_time_eligible,
        'raw_hash':e.raw_hash,
        'source_identity':e.source_identity,
        'normalized_hash':normalized_hash,
        'partition':'DEVELOPMENT_2015_2020',
    }
    out.update(AUTHORITY_FALSE)
    return out


def validate_revision_lineage(original_actual:Optional[float], revised_value:Optional[float], normalized_actual:Optional[float])->bool:
    if original_actual is None:
        return normalized_actual is None
    if normalized_actual != original_actual:
        raise RND0064Error('actual-as-released overwritten by revision')
    return True


def classify_source_pilot(*, total_events:int, exact_timed:int, consensus_count:int,
                          actual_count:int, provenance_failures:int, duplicate_count:int,
                          unexplained_gaps:int)->Dict[str,Any]:
    if total_events <= 0:
        classification='SOURCE_EVALUATION_INCONCLUSIVE'
    elif provenance_failures>0 or duplicate_count>0:
        classification='SOURCE_NOT_ADMISSIBLE_FOR_POINT_IN_TIME_RESEARCH'
    else:
        exact_ratio=exact_timed/total_events
        consensus_ratio=consensus_count/total_events
        actual_ratio=actual_count/total_events
        if exact_ratio>=0.95 and consensus_ratio>=0.80 and actual_ratio>=0.95 and unexplained_gaps==0:
            classification='SOURCE_ADMISSIBLE_FOR_STRUCTURAL_NORMALIZATION'
        elif exact_ratio>=0.80 and consensus_ratio>=0.60 and actual_ratio>=0.90:
            classification='SOURCE_ADMISSIBLE_WITH_DOCUMENTED_LIMITATIONS'
        else:
            classification='SOURCE_EVALUATION_INCONCLUSIVE'
    out={
        'classification':classification,
        'total_events':total_events,
        'exact_timed':exact_timed,
        'consensus_count':consensus_count,
        'actual_count':actual_count,
        'provenance_failures':provenance_failures,
        'duplicate_count':duplicate_count,
        'unexplained_gaps':unexplained_gaps,
    }
    out.update(AUTHORITY_FALSE)
    return out
