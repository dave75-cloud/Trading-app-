from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any

Q003_START = datetime.fromisoformat('2026-10-05T07:25:00+00:00')
Q003_MIN = datetime.fromisoformat('2027-04-03T07:25:00+00:00')
QR_START = datetime.fromisoformat('2026-10-09T02:33:50+00:00')
QR_MIN = datetime.fromisoformat('2027-04-07T02:33:50+00:00')

AUTHORITY_FALSE_FIELDS = {
    'economic_fields_open': False,
    'promotion_authority': False,
    'broker_write_authority': False,
    'capital_authority': False,
    'live_execution_authority': False,
    'reserved_final_open': False,
    'automatic_merge': False,
}

PROHIBITED_OUTPUT_FIELDS = {
    'trade_count','returns','pnl','equity','drawdown','win_rate','pair_ranking',
    'admit_mean','veto_mean','admit_median','veto_median','symbol_economic_comparison',
    'threshold_suggestion','tuning_suggestion','rescue_signal','combined_economic_statistic'
}

class RND0060YError(ValueError):
    pass

@dataclass(frozen=True)
class StructuralInput:
    stream_id: str
    protocol_id: str
    evaluation_time_utc: str
    ledger_identity: str
    ledger_hash: str
    record_count: int
    eligible_non_defer_count: int = 0
    duplicate_identity_count: int = 0
    chronology_regression_count: int = 0
    pre_start_contamination_count: int = 0
    prohibited_partition_access_count: int = 0
    missing_provenance_hash_count: int = 0
    evidence_mutation_count: int = 0
    unexplained_gap_count: int = 0
    recoverable_scheduler_delay: bool = False
    duplicate_scheduler_acquisition: bool = False
    acquisition_before_close_boundary: bool = False
    recovery_receipt_present: bool = True
    last_sealed_evidence_timestamp: str = ''
    next_expected_acquisition_boundary: str = ''


def _dt(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None:
        raise RND0060YError('evaluation time must be timezone-aware')
    return d.astimezone(timezone.utc)


def _stream_constants(stream_id: str):
    if stream_id == 'Q003':
        return Q003_START, Q003_MIN, 'Q003'
    if stream_id == 'RND0060QR':
        return QR_START, QR_MIN, 'RND0060QR'
    raise RND0060YError('unknown stream')


def _structural_failure(inp: StructuralInput) -> bool:
    return any([
        inp.pre_start_contamination_count > 0,
        inp.duplicate_identity_count > 0,
        inp.chronology_regression_count > 0,
        inp.prohibited_partition_access_count > 0,
        inp.missing_provenance_hash_count > 0,
        inp.evidence_mutation_count > 0,
        inp.unexplained_gap_count > 0,
    ]) or not inp.ledger_identity or not inp.ledger_hash


def _attention(inp: StructuralInput) -> bool:
    return any([
        inp.recoverable_scheduler_delay,
        inp.duplicate_scheduler_acquisition,
        inp.acquisition_before_close_boundary,
    ])


def evaluate_health(inp: StructuralInput) -> Dict[str, Any]:
    start, earliest, canonical = _stream_constants(inp.stream_id)
    now = _dt(inp.evaluation_time_utc)
    elapsed_days = max(0, (now - start).days)

    if _structural_failure(inp):
        state = 'STRUCTURAL_REMEDIATION_REQUIRED'
    elif _attention(inp):
        state = 'ATTENTION_REQUIRED'
    else:
        time_ready = now >= earliest and elapsed_days >= 180
        if canonical == 'Q003':
            ready = time_ready
        else:
            ready = time_ready and inp.eligible_non_defer_count >= 100
        state = 'READOUT_ELIGIBLE_PENDING_HUMAN_GATE' if ready else 'HEALTHY_ACCUMULATING'

    out = {
        'stream_id': canonical,
        'protocol_id': inp.protocol_id,
        'prospective_start_utc': start.isoformat().replace('+00:00','Z'),
        'evaluation_time_utc': now.isoformat().replace('+00:00','Z'),
        'elapsed_calendar_days': elapsed_days,
        'earliest_time_based_readout_utc': earliest.isoformat().replace('+00:00','Z'),
        'ledger_identity': inp.ledger_identity,
        'ledger_hash': inp.ledger_hash,
        'record_count': inp.record_count,
        'duplicate_identity_count': inp.duplicate_identity_count,
        'chronology_regression_count': inp.chronology_regression_count,
        'pre_start_contamination_count': inp.pre_start_contamination_count,
        'prohibited_partition_access_count': inp.prohibited_partition_access_count,
        'missing_provenance_hash_count': inp.missing_provenance_hash_count,
        'evidence_mutation_count': inp.evidence_mutation_count,
        'unexplained_gap_count': inp.unexplained_gap_count,
        'recoverable_scheduler_delay': inp.recoverable_scheduler_delay,
        'duplicate_scheduler_acquisition': inp.duplicate_scheduler_acquisition,
        'acquisition_before_close_boundary': inp.acquisition_before_close_boundary,
        'recovery_receipt_present': inp.recovery_receipt_present,
        'last_sealed_evidence_timestamp': inp.last_sealed_evidence_timestamp,
        'next_expected_acquisition_boundary': inp.next_expected_acquisition_boundary,
        'health_state': state,
    }
    if canonical == 'RND0060QR':
        out['eligible_non_defer_count'] = inp.eligible_non_defer_count
    out.update(AUTHORITY_FALSE_FIELDS)
    validate_output_contract(out)
    return out


def validate_output_contract(out: Dict[str, Any]) -> bool:
    if any(k in out for k in PROHIBITED_OUTPUT_FIELDS):
        raise RND0060YError('prohibited prospective economic field in monitor output')
    for k, v in AUTHORITY_FALSE_FIELDS.items():
        if out.get(k) is not v:
            raise RND0060YError(f'authority firewall violation: {k}')
    if out.get('reserved_final_open') is not False:
        raise RND0060YError('reserved final must remain closed')
    if out.get('stream_id') == 'Q003' and 'eligible_non_defer_count' in out:
        raise RND0060YError('cross-stream structural counter leakage')
    return True


def compare_streams(q003: StructuralInput, qr: StructuralInput) -> Dict[str, Any]:
    a = evaluate_health(q003)
    b = evaluate_health(qr)
    return {'Q003': a, 'RND0060QR': b}
