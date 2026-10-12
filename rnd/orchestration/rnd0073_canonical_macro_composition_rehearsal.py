from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from typing import Any, Dict, Iterable, List

from rnd0066_fred_alfred_macro_provenance_backbone import (
    ConsensusEvidence,
    FredVintageEvidence,
    TimingEvidence,
    compose_event,
)
from rnd0069_bls_historical_timing_adapter import BLSScheduleEvidence, validate_frozen_triplet

PILOT_SCOPE_ID = 'RND0073_US_CPI_2019Q1_CANONICAL_COMPOSITION_REHEARSAL'
EXPECTED_REFERENCE_PERIODS = ('2019-01', '2019-02', '2019-03')
PROHIBITED_MARKET_FIELDS = {
    'fx_return','pnl','equity','drawdown','hit_rate','win_rate','pair_rank',
    'directional_response','strategy_signal','strategy_outcome'
}
AUTHORITY_FALSE = {
    'provider_access_authority': False,
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


class RND0073Error(ValueError):
    pass


def validate_no_market_outcomes(payload: Any) -> None:
    if isinstance(payload, dict):
        lowered = {str(k).lower() for k in payload}
        if lowered.intersection(PROHIBITED_MARKET_FIELDS):
            raise RND0073Error('market outcome contamination prohibited')
        for value in payload.values():
            validate_no_market_outcomes(value)
    elif isinstance(payload, (list, tuple)):
        for value in payload:
            validate_no_market_outcomes(value)


def timing_from_bls(row: BLSScheduleEvidence) -> TimingEvidence:
    return TimingEvidence(
        provider=row.provider,
        provider_event_id=row.provider_event_id,
        link_key=row.link_key,
        event_series=row.event_series,
        economy=row.economy,
        currency=row.currency,
        reference_period=row.reference_period,
        scheduled_timestamp=row.scheduled_timestamp_utc,
        timestamp_precision=row.timestamp_precision,
        raw_hash=row.raw_hash,
        source_identity=row.source_identity,
        cancelled=False,
        rescheduled_from='',
    )


def validate_triplet_alignment(actuals: Iterable[FredVintageEvidence], timings: Iterable[BLSScheduleEvidence],
                               consensuses: Iterable[ConsensusEvidence]) -> tuple[List[FredVintageEvidence], List[BLSScheduleEvidence], List[ConsensusEvidence]]:
    a = list(actuals)
    t = validate_frozen_triplet(list(timings))
    c = list(consensuses)
    if len(a) != 3 or len(c) != 3:
        raise RND0073Error('frozen rehearsal requires exactly three actual and consensus records')
    for rows in (a, t, c):
        periods = [r.reference_period for r in rows]
        if periods != list(EXPECTED_REFERENCE_PERIODS):
            raise RND0073Error('reference periods must be complete, ordered and identical')
    return a, t, c


def rehearse_composition(actuals: Iterable[FredVintageEvidence], timings: Iterable[BLSScheduleEvidence],
                         consensuses: Iterable[ConsensusEvidence]) -> Dict[str, Any]:
    a, t, c = validate_triplet_alignment(actuals, timings, consensuses)
    seen = set()
    events = []
    for actual, bls, consensus in zip(a, t, c):
        if consensus.provider != 'SYNTHETIC_CONSENSUS_FIXTURE':
            raise RND0073Error('RND-0073 permits synthetic consensus only')
        validate_no_market_outcomes(asdict(actual))
        validate_no_market_outcomes(asdict(bls))
        validate_no_market_outcomes(asdict(consensus))
        event = compose_event(actual, timing_from_bls(bls), consensus, seen_ids=seen)
        if event.get('eligibility_state') != 'SURPRISE_INPUT_ELIGIBLE':
            raise RND0073Error('composite event failed canonical eligibility')
        if not event.get('surprise_eligible_inputs_present'):
            raise RND0073Error('canonical surprise inputs absent')
        validate_no_market_outcomes(event)
        events.append(event)

    material = '|'.join(e['normalized_hash'] for e in events)
    receipt = {
        'pilot_scope_id': PILOT_SCOPE_ID,
        'record_count': len(events),
        'reference_periods': [e['reference_period'] for e in events],
        'canonical_event_ids': [e['canonical_event_id'] for e in events],
        'bundle_sha256': sha256(material.encode('utf-8')).hexdigest(),
        'fred_alfred_actual_role_verified': True,
        'bls_exact_timing_role_verified': True,
        'synthetic_consensus_role_verified': True,
        'canonical_schema': 'RND0064',
        'canonical_composition_verified': True,
        'live_consensus_used': False,
        'provider_spend_incurred': False,
        'fx_outcomes_present': False,
        'classification': 'CANONICAL_COMPOSITION_REHEARSAL_CONFIRMED',
    }
    receipt.update(AUTHORITY_FALSE)
    return {'events': events, 'receipt': receipt}


def authority_firewall() -> Dict[str, bool]:
    return dict(AUTHORITY_FALSE)
