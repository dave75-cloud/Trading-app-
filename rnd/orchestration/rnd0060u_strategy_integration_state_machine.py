#!/usr/bin/env python3
"""Pure broker-disconnected RND-0060U strategy integration state machine."""
from __future__ import annotations

from copy import deepcopy

PIPELINE=(
    'SIGNAL_PROPOSAL','SIGNAL_PROVENANCE_CHECK','ACTIVITY_ADMISSIBILITY',
    'RISK_AUTHORIZATION','SHADOW_EXECUTION_INTENT','SHADOW_EXECUTION_SIMULATION',
    'RECONCILIATION','AUDIT_COMMIT','TERMINAL_STATE'
)
KILL_PRECEDENCE=(
    'GLOBAL_KILL','RECONCILIATION_KILL','DATA_INTEGRITY_KILL',
    'RISK_LIMIT_KILL','STRATEGY_SUSPEND'
)
TERMINAL_STATES={
    'PROVENANCE_REJECTED','ACTIVITY_VETOED','ACTIVITY_DEFERRED','RISK_REJECTED',
    'SHADOW_EXECUTION_REJECTED','RECONCILIATION_PENDING','RECONCILIATION_FAILED',
    'SHADOW_CYCLE_RECONCILED','KILLED'
}

class RND0060UError(ValueError): pass

def _require(c,m):
    if not c: raise RND0060UError(m)

def _same_identity(a,b):
    return all(a.get(k)==b.get(k) for k in ('instrument','direction'))

def _kill_state(kills):
    active=set(kills or [])
    for k in KILL_PRECEDENCE:
        if k in active: return k
    return None

def validate_signal(signal):
    req=('signal_id','strategy_id','strategy_version','instrument','direction','requested_exposure','signal_timestamp_utc','source_evidence_identity','strategy_promotion_receipt')
    for k in req: _require(k in signal and signal[k] not in (None,''),f'missing signal field: {k}')
    _require(signal['direction'] in ('LONG','SHORT'),'invalid direction')
    _require(isinstance(signal['requested_exposure'],(int,float)) and signal['requested_exposure']>0,'requested_exposure must be > 0')
    _require(signal.get('broker_write_authority',False) is False,'signal may not carry broker write authority')
    return deepcopy(signal)

def provenance_check(signal, *, seen_signal_ids, approved_strategy_id, approved_strategy_version, valid_promotion_receipt=True, prohibited_contamination=False, timestamp_monotonic=True):
    s=validate_signal(signal)
    if s['signal_id'] in set(seen_signal_ids or []): return {'decision':'REJECT_PROVENANCE','reason':'DUPLICATE_SIGNAL_ID'}
    if s['strategy_id']!=approved_strategy_id or s['strategy_version']!=approved_strategy_version: return {'decision':'REJECT_PROVENANCE','reason':'UNAPPROVED_STRATEGY'}
    if not valid_promotion_receipt: return {'decision':'REJECT_PROVENANCE','reason':'INVALID_PROMOTION_RECEIPT'}
    if prohibited_contamination: return {'decision':'REJECT_PROVENANCE','reason':'PROHIBITED_EVIDENCE_CONTAMINATION'}
    if not timestamp_monotonic: return {'decision':'REJECT_PROVENANCE','reason':'TIMESTAMP_REGRESSION'}
    return {'decision':'PROVENANCE_OK','signal':s}

def activity_admissibility(signal, decision):
    _require(decision in ('ADMIT','VETO','DEFER'),'invalid activity decision')
    if decision=='VETO': return {'decision':'VETO','terminal':'ACTIVITY_VETOED','exposure':0}
    if decision=='DEFER': return {'decision':'DEFER','terminal':'ACTIVITY_DEFERRED','exposure':0}
    return {'decision':'ADMIT','signal':deepcopy(signal),'instrument':signal['instrument'],'direction':signal['direction'],'requested_exposure':signal['requested_exposure']}

def risk_authorize(admitted, *, decision, authorized_exposure=None, instrument=None, direction=None, critical_state_stale=False, reconciliation_healthy=True, kills=None):
    kill=_kill_state(kills)
    if kill: return {'decision':'KILL','kill':kill,'terminal':'KILLED'}
    _require(admitted.get('decision')=='ADMIT','risk cannot bypass non-ADMIT activity state')
    if critical_state_stale or not reconciliation_healthy: return {'decision':'REJECT','reason':'STALE_OR_UNHEALTHY_STATE','terminal':'RISK_REJECTED'}
    _require(decision in ('AUTHORIZE_UNCHANGED','REDUCE','REJECT'),'invalid risk decision')
    if decision=='REJECT': return {'decision':'REJECT','terminal':'RISK_REJECTED'}
    sig=admitted['signal']
    out_instrument=sig['instrument'] if instrument is None else instrument
    out_direction=sig['direction'] if direction is None else direction
    _require(out_instrument==sig['instrument'],'risk cannot substitute instrument')
    _require(out_direction==sig['direction'],'risk cannot invert direction')
    if decision=='AUTHORIZE_UNCHANGED':
        exp=sig['requested_exposure'] if authorized_exposure is None else authorized_exposure
        _require(exp==sig['requested_exposure'],'unchanged authorization must preserve exposure')
    else:
        _require(isinstance(authorized_exposure,(int,float)),'REDUCE requires authorized_exposure')
        _require(0 < authorized_exposure < sig['requested_exposure'],'risk REDUCE must strictly reduce positive exposure')
        exp=authorized_exposure
    return {'decision':decision,'instrument':out_instrument,'direction':out_direction,'authorized_exposure':exp,'parent_signal_id':sig['signal_id']}

def make_shadow_intent(risk, *, admissibility_decision_id, risk_decision_id, intent_timestamp_utc, mode='SHADOW_ONLY', broker_write_authority=False, kills=None):
    kill=_kill_state(kills)
    if kill: return {'decision':'KILL','kill':kill,'terminal':'KILLED'}
    _require(risk.get('decision') in ('AUTHORIZE_UNCHANGED','REDUCE'),'shadow intent requires authorized risk decision')
    _require(mode=='SHADOW_ONLY','SHADOW_ONLY is mandatory')
    _require(broker_write_authority is False,'broker_write_authority must remain FALSE')
    return {
        'parent_signal_id':risk['parent_signal_id'],'admissibility_decision_id':admissibility_decision_id,
        'risk_decision_id':risk_decision_id,'instrument':risk['instrument'],'direction':risk['direction'],
        'authorized_exposure':risk['authorized_exposure'],'intent_timestamp_utc':intent_timestamp_utc,
        'mode':'SHADOW_ONLY','broker_write_authority':False
    }

def simulate_shadow(intent, *, outcome='FILLED', execution_id='shadow-exec-1'):
    _require(intent.get('mode')=='SHADOW_ONLY','simulation requires SHADOW_ONLY intent')
    _require(intent.get('broker_write_authority') is False,'simulation forbids broker write authority')
    _require(outcome in ('FILLED','PARTIAL','REJECTED'),'invalid simulated outcome')
    return {'execution_id':execution_id,'parent_signal_id':intent['parent_signal_id'],'instrument':intent['instrument'],'direction':intent['direction'],'authorized_exposure':intent['authorized_exposure'],'outcome':outcome,'broker_endpoint_called':False}

def reconcile(signal, activity, risk, intent, execution, *, state='RECONCILED'):
    _require(state in ('RECONCILED','RECONCILIATION_PENDING','RECONCILIATION_FAILED'),'invalid reconciliation state')
    _require(intent['parent_signal_id']==signal['signal_id'],'intent lineage mismatch')
    _require(execution['parent_signal_id']==signal['signal_id'],'execution lineage mismatch')
    _require(_same_identity(signal,intent) and _same_identity(intent,execution),'identity mutation detected')
    if state=='RECONCILIATION_FAILED': return {'state':state,'blocks_new_intents':True,'terminal':'RECONCILIATION_FAILED'}
    if state=='RECONCILIATION_PENDING': return {'state':state,'blocks_new_intents':True,'terminal':'RECONCILIATION_PENDING'}
    return {'state':'RECONCILED','blocks_new_intents':False}

def audit_commit(*, signal, activity_decision_id, risk_decision_id, intent, execution, reconciliation, immutable_hashes):
    _require(reconciliation.get('state')=='RECONCILED','audit completion requires reconciled cycle')
    _require(intent['parent_signal_id']==signal['signal_id'],'audit signal lineage mismatch')
    _require(bool(activity_decision_id) and bool(risk_decision_id),'missing decision lineage')
    _require(isinstance(immutable_hashes,dict) and all(immutable_hashes.get(k) for k in ('signal','activity','risk','intent','execution','reconciliation')),'incomplete immutable hash lineage')
    return {'signal_id':signal['signal_id'],'activity_decision_id':activity_decision_id,'risk_decision_id':risk_decision_id,'execution_id':execution['execution_id'],'hashes':deepcopy(immutable_hashes),'append_only':True,'reconstructable':True}

def terminal_from(*, provenance=None, activity=None, risk=None, reconciliation=None, audit=None, kills=None):
    kill=_kill_state(kills)
    if kill: return {'terminal':'KILLED','kill':kill}
    if provenance and provenance.get('decision')=='REJECT_PROVENANCE': return {'terminal':'PROVENANCE_REJECTED'}
    if activity and activity.get('terminal'): return {'terminal':activity['terminal']}
    if risk and risk.get('terminal'): return {'terminal':risk['terminal']}
    if reconciliation and reconciliation.get('terminal'): return {'terminal':reconciliation['terminal']}
    if audit: return {'terminal':'SHADOW_CYCLE_RECONCILED'}
    raise RND0060UError('terminal state cannot be inferred permissively')
