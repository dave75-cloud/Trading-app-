#!/usr/bin/env python3
"""Governed single-trial RND-0060L full-development economic-utility runner."""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ORCH=ROOT/'rnd'/'orchestration'
if str(ORCH) not in sys.path: sys.path.insert(0,str(ORCH))

from rnd0035_development_runner import PLAN_PATH, _verify_evidence
from rnd0035_trial_plan import load_plan
from rnd0036_2020_development_acquisition import SYMBOLS, END_UTC as DEVELOPMENT_END, SHARD, ACQUISITION_PATH, CALENDAR_PATH, boundary_proof
from rnd0060_research_firewall import validate_research_declaration
from rnd0060l_activity_state_economic_utility import summarize
from oanda_historical_quarantine import _json, verify_existing_shard

DEVELOPMENT_START='2015-01-01T00:00:00Z'
ASSEMBLY_RECEIPT_PATH=ROOT/'rnd'/'research'/'RND0037_DEVELOPMENT_ASSEMBLY_RECEIPT.json'

class RND0060LDevelopmentError(ValueError): pass

def _require(c,m):
    if not c: raise RND0060LDevelopmentError(m)

def _sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def _declaration():
    return {
        'independent_of_q003':True,
        'hypothesis':'At 11:30 UTC, higher cross-sectional USD dispersion is associated with a higher next-30-minute movement-to-friction ratio across the four-symbol market set.',
        'fixed_parameters':{
            'timeframe':'M5','observation_time_utc':'11:30','lookback_intervals':6,'forward_horizon_intervals':6,
            'usd_orientation':{'AUDUSD':-1,'EURUSD':-1,'GBPUSD':-1,'USDJPY':1},
            'state':'RND0060H_POPULATION_STD_OF_FOUR_USD_ORIENTED_30_MINUTE_RETURNS',
            'relative_spread':'(ASK_CLOSE-BID_CLOSE)/MID_CLOSE_AT_11_30',
            'forward_movement':'(MAX_NEXT_6_M5_MID_HIGH-MIN_NEXT_6_M5_MID_LOW)/MID_CLOSE_AT_11_30',
            'primary_response':'EQUAL_WEIGHT_MEAN_OF_FOUR_FORWARD_MOVEMENT_TO_FRICTION_RATIOS',
            'trade_simulation':False,'pnl':False,
        },
        'datasets':['DEVELOPMENT_2015_2020'],'strategy_references':[],
        'declared_trial_count':1,'parameter_search':False,'threshold_search':False,
        'automatic_promotion':False,'broker_writes':False,'capital_authority':False,
    }

def _validate_assembly(path):
    r=_json(ASSEMBLY_RECEIPT_PATH)
    _require(r.get('status')=='COMPLETE','RND-0037 assembly receipt incomplete')
    _require(r.get('pair_years')=='24/24','RND-0037 pair-year receipt incomplete')
    _require(r.get('full_development_structural_evidence_complete') is True,'RND-0037 structural evidence incomplete')
    for k in ('strategy_evaluation','validation_open','final_test_open','broker_writes','capital_authority'):
        _require(r.get(k) is False,f'RND-0037 prohibited authority opened: {k}')
    p=Path(path).expanduser().resolve(); _require(p.is_file(),'RND-0037 assembly report missing')
    _require(_sha256_file(p)==r.get('external_report_sha256'),'RND-0037 assembly report SHA mismatch')

def _load_2020(root):
    acquisition=_json(ACQUISITION_PATH); calendar=_json(CALENDAR_PATH); root=Path(root).expanduser().resolve()
    rows={}; ids={}
    for s in SYMBOLS:
        shard=root/s/'2020-development'
        _require(verify_existing_shard(shard,s,SHARD,acquisition,calendar),f'{s}: 2020 shard identity verification failed')
        proof=boundary_proof(shard,s); _require(proof['rows_at_or_after_validation_boundary']==0,f'{s}: validation boundary breach')
        data=_json(shard/'canonical_rows.json'); manifest=_json(shard/'quarantine_manifest.json')
        _require(isinstance(data,list) and data,f'{s}: 2020 canonical rows missing')
        rows[s]=data; ids[s]={'row_count':len(data),'canonical_rows_sha256':manifest.get('canonical_rows_sha256'),'raw_bundle_sha256':manifest.get('aggregate_raw_bundle_sha256'),'standard_schedule_sha256':manifest.get('standard_schedule_sha256'),'boundary_proof':proof}
    return ids,rows

def run(aud2015,cross2015,dev1619,dev2020,assembly):
    validate_research_declaration(_declaration()); _validate_assembly(assembly)
    plan=load_plan(PLAN_PATH)
    _require(plan.get('validation_open') is False,'validation unexpectedly open')
    _require(plan.get('final_test_open') is False,'reserved final unexpectedly open')
    ids_old,verified,historical=_verify_evidence(plan,aud2015,cross2015,dev1619,load_rows=True)
    _require(verified==20,'2015-2019 evidence verification not 20/20')
    ids20,rows20=_load_2020(dev2020)
    full={}
    for s in SYMBOLS:
        data=list(historical[s])+list(rows20[s]); ts=[r['timestamp_utc'] for r in data]
        _require(ts==sorted(ts),f'{s}: rows not chronological')
        _require(len(ts)==len(set(ts)),f'{s}: duplicate timestamps')
        _require(ts[0]>=DEVELOPMENT_START,f'{s}: pre-development row')
        _require(ts[-1]<DEVELOPMENT_END,f'{s}: validation row detected')
        full[s]=data
    decision=summarize(full)
    return {
        'contract_version':'RND0060L-full-development-v1','task_id':'RND-0060L','mode':'NON_TRADING_ACTIVITY_STATE_ECONOMIC_UTILITY',
        'development_interval':{'start_inclusive_utc':DEVELOPMENT_START,'end_exclusive_utc':DEVELOPMENT_END},
        'declaration':_declaration(),
        'evidence_identity':{'verified_2015_2019':'20/20','verified_2020':'4/4','pair_years':'24/24','identities_2015_2019':ids_old,'identities_2020':ids20},
        'structure_screen':decision,'trial_count':1,'parameter_search':False,'threshold_search':False,'trade_simulation':False,'pnl':False,'strategy_candidate':False,
        'q003_reference':False,'validation_open':False,'final_test_open':False,'reserved_final_access':False,'prospective_candidate_outcomes_open':False,'portfolio_sizing':False,
        'broker_writes':False,'capital_authority':False,'automatic_promotion':False,'automatic_merge':False,'status':'COMPLETE_REQUIRES_HUMAN_REVIEW',
    }

def _write_new(path,value):
    p=Path(path).expanduser().resolve()
    _require(p!=ROOT and ROOT not in p.parents,'research report must remain outside repository')
    _require(not p.exists(),'report exists; overwrite prohibited')
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8'); return p

def main(argv=None):
    ap=argparse.ArgumentParser()
    for a in ('audusd-2015-shard','cross-pair-2015-root','development-2016-2019-root','development-2020-root','rnd0037-assembly-report','report'): ap.add_argument('--'+a,required=True)
    a=ap.parse_args(argv)
    v=run(a.audusd_2015_shard,a.cross_pair_2015_root,a.development_2016_2019_root,a.development_2020_root,a.rnd0037_assembly_report)
    out=_write_new(a.report,v); s=v['structure_screen']
    print('RND0060L_FULL_DEVELOPMENT: COMPLETE')
    print('verified_2015_2019=20/20'); print('verified_2020=4/4'); print('pair_years=24/24')
    print('trial_count=1'); print('parameter_search=FALSE'); print('threshold_search=FALSE'); print('trade_simulation=FALSE'); print('pnl=FALSE')
    print(f"classification={s['classification']}")
    print('validation_open=FALSE'); print('final_test_open=FALSE'); print('reserved_final_access=FALSE'); print('prospective_candidate_outcomes_open=FALSE')
    print('broker_writes=FALSE'); print('capital_authority=FALSE')
    print(f'report={out}'); print(f'report_sha256={_sha256_file(out)}')
    return 0

if __name__=='__main__': raise SystemExit(main())
