#!/usr/bin/env python3
"""RND-0060W deterministic broker-disconnected end-to-end shadow rehearsal."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from rnd0060u_strategy_integration_state_machine import (
    RND0060UError,
    provenance_check,
    activity_admissibility,
    risk_authorize,
    make_shadow_intent,
    reconcile,
    audit_commit,
    terminal_from,
)
from rnd0060v_shadow_execution_risk_realism import (
    QuoteSnapshot,
    RiskState,
    ShadowRequest,
    RND0060VError,
    simulate_shadow_execution,
    audit_lineage,
)

FORBIDDEN_KEYS={
    'q003_outcomes','rnd0060r_outcomes','validation_data','reserved_final_data',
    'broker_credentials','broker_endpoint','live_order_id','capital_authority',
    'broker_write_authority_true','automatic_promotion','automatic_merge'
}

class RND0060WError(ValueError): pass

def _require(c,m):
    if not c: raise RND0060WError(m)

def _hash(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),default=str).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def _reject_forbidden(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            _require(k not in FORBIDDEN_KEYS,f'prohibited integration field: {k}')
            _reject_forbidden(v)
    elif isinstance(obj,(list,tuple)):
        for v in obj: _reject_forbidden(v)

def _base_output(trace, terminal, **extra):
    out={
        'task_id':'RND-0060W',
        'mode':'SHADOW_ONLY',
        'broker_write_authority':False,
        'stage_trace':list(trace),
        'terminal_state':terminal,
        'live_authority':False,
        'capital_authority':False,
        'strategy_science':False,
    }
    out.update(extra)
    return out

def run_rehearsal(case, *, seen_request_ids=None, prior_reconciliation_block=False):
    """Run one synthetic integration scenario. All values must be explicit in case."""
    _require(isinstance(case,dict),'case must be a dict')
    _reject_forbidden(case)
    req=(
        'signal','approved_strategy_id','approved_strategy_version','seen_signal_ids',
        'valid_promotion_receipt','prohibited_contamination','timestamp_monotonic',
        'activity_decision','activity_decision_id','risk_decision','risk_decision_id',
        'authorized_exposure','critical_state_stale','reconciliation_healthy','kills',
        'intent_timestamp_utc','request_id','quote','risk_state','slippage',
        'latency_seconds','fill_fraction','simulate_reject','reconciliation_state',
        'reconciliation_event_id'
    )
    for k in req: _require(k in case,f'missing rehearsal field: {k}')
    _require(prior_reconciliation_block is False,'prior reconciliation block active')
    trace=['SIGNAL_PROPOSAL']

    try:
        prov=provenance_check(
            case['signal'],seen_signal_ids=case['seen_signal_ids'],
            approved_strategy_id=case['approved_strategy_id'],
            approved_strategy_version=case['approved_strategy_version'],
            valid_promotion_receipt=case['valid_promotion_receipt'],
            prohibited_contamination=case['prohibited_contamination'],
            timestamp_monotonic=case['timestamp_monotonic'])
    except RND0060UError as e:
        return _base_output(trace+['SIGNAL_PROVENANCE_CHECK'],'PROVENANCE_REJECTED',reason=str(e))
    trace.append('SIGNAL_PROVENANCE_CHECK')
    if prov.get('decision')=='REJECT_PROVENANCE':
        return _base_output(trace,'PROVENANCE_REJECTED',provenance=prov,filled_exposure=0.0)
    signal=prov['signal']

    activity=activity_admissibility(signal,case['activity_decision'])
    trace.append('ACTIVITY_ADMISSIBILITY')
    if activity.get('decision') in ('VETO','DEFER'):
        terminal=terminal_from(activity=activity)['terminal']
        return _base_output(trace,terminal,activity=activity,filled_exposure=0.0)

    risk=risk_authorize(
        activity,decision=case['risk_decision'],authorized_exposure=case['authorized_exposure'],
        critical_state_stale=case['critical_state_stale'],
        reconciliation_healthy=case['reconciliation_healthy'],kills=case['kills'])
    trace.append('RISK_AUTHORIZATION')
    if risk.get('terminal'):
        terminal=terminal_from(risk=risk,kills=case['kills'])['terminal']
        return _base_output(trace,terminal,risk=risk,filled_exposure=0.0)

    try:
        intent=make_shadow_intent(
            risk,admissibility_decision_id=case['activity_decision_id'],
            risk_decision_id=case['risk_decision_id'],intent_timestamp_utc=case['intent_timestamp_utc'],
            mode='SHADOW_ONLY',broker_write_authority=False,kills=case['kills'])
    except RND0060UError as e:
        return _base_output(trace+['SHADOW_EXECUTION_INTENT'],'KILLED' if case['kills'] else 'RISK_REJECTED',reason=str(e),filled_exposure=0.0)
    trace.append('SHADOW_EXECUTION_INTENT')

    q=QuoteSnapshot(**case['quote'])
    rs=RiskState(**case['risk_state'])
    _require(rs.mode=='SHADOW_ONLY' and rs.broker_write_authority is False,'risk realism mode violation')
    _require(rs.reconciliation_state=='RECONCILED','risk state must be reconciled before new exposure')
    request=ShadowRequest(
        request_id=case['request_id'],parent_intent_id=case.get('intent_id','intent-1'),
        parent_risk_id=case['risk_decision_id'],parent_admissibility_id=case['activity_decision_id'],
        parent_signal_id=signal['signal_id'],instrument=intent['instrument'],direction=intent['direction'],
        requested_exposure=signal['requested_exposure'],authorized_exposure=intent['authorized_exposure'],
        intent_timestamp_utc=intent['intent_timestamp_utc'],slippage=case['slippage'],
        latency_seconds=case['latency_seconds'],fill_fraction=case['fill_fraction'],
        simulate_reject=case['simulate_reject'],mode='SHADOW_ONLY',broker_write_authority=False)
    trace.append('EXECUTION_REALISM_PRECHECK')
    try:
        ex=simulate_shadow_execution(request,q,rs,seen_request_ids)
    except RND0060VError as e:
        return _base_output(trace+['SHADOW_EXECUTION_SIMULATION'],'SHADOW_EXECUTION_REJECTED',reason=str(e),filled_exposure=0.0)
    trace.append('SHADOW_EXECUTION_SIMULATION')
    _require(audit_lineage(ex),'execution audit lineage incomplete')
    _require(ex['mode']=='SHADOW_ONLY' and ex['broker_write_authority'] is False,'execution authority mutation')
    _require(ex['instrument'] if 'instrument' in ex else request.instrument,'execution instrument missing')
    if ex['simulated_status']=='REJECTED':
        return _base_output(trace,'SHADOW_EXECUTION_REJECTED',execution=ex,filled_exposure=0.0)

    execution_for_u={
        'execution_id':case.get('execution_id',case['request_id']),
        'parent_signal_id':ex['parent_signal_id'],'instrument':request.instrument,
        'direction':request.direction,'authorized_exposure':ex['authorized_exposure'],
        'outcome':'PARTIAL' if ex['simulated_status']=='PARTIAL_FILL' else 'FILLED',
        'broker_endpoint_called':False,
    }
    _require(ex['filled_exposure']<=ex['authorized_exposure']<=signal['requested_exposure'],'end-to-end exposure monotonicity breach')
    _require(request.instrument==signal['instrument'] and request.direction==signal['direction'],'end-to-end identity mutation')

    rec=reconcile(signal,activity,risk,intent,execution_for_u,state=case['reconciliation_state'])
    trace.append('RECONCILIATION')
    if rec.get('terminal'):
        terminal=terminal_from(reconciliation=rec)['terminal']
        return _base_output(trace,terminal,execution=ex,reconciliation=rec,filled_exposure=ex['filled_exposure'],blocks_new_intents=True)

    immutable_hashes={
        'signal':_hash(signal),'activity':_hash(activity),'risk':_hash(risk),
        'intent':_hash(intent),'execution':_hash(ex),'reconciliation':_hash(rec),
    }
    audit=audit_commit(
        signal=signal,activity_decision_id=case['activity_decision_id'],risk_decision_id=case['risk_decision_id'],
        intent=intent,execution=execution_for_u,reconciliation=rec,immutable_hashes=immutable_hashes)
    audit['reconciliation_event_id']=case['reconciliation_event_id']
    audit['quote_identity']=ex['quote_identity']
    audit['risk_state_identity']=ex['risk_state_identity']
    audit['shadow_request_id']=ex['request_id']
    trace.append('AUDIT_COMMIT')
    terminal=terminal_from(audit=audit)['terminal']
    trace.append('TERMINAL_STATE')
    return _base_output(trace,terminal,signal=deepcopy(signal),activity=deepcopy(activity),risk=deepcopy(risk),intent=deepcopy(intent),execution=deepcopy(ex),reconciliation=deepcopy(rec),audit=deepcopy(audit),filled_exposure=ex['filled_exposure'],blocks_new_intents=False)
