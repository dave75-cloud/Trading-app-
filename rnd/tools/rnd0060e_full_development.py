#!/usr/bin/env python3
"""Governed single-trial RND-0060E full-development runner."""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from rnd0035_development_runner import PLAN_PATH, _verify_evidence
from rnd0035_trial_plan import load_plan
from rnd0036_2020_development_acquisition import SYMBOLS, END_UTC as DEVELOPMENT_END, SHARD, ACQUISITION_PATH, CALENDAR_PATH, boundary_proof
from rnd0035_concurrent_reference_stats import concurrent_reference_statistics
from rnd0060_research_firewall import validate_research_declaration
from rnd0060e_volatility_contraction_expansion import evaluate_symbol
from oanda_historical_quarantine import _json, verify_existing_shard

DEVELOPMENT_START = "2015-01-01T00:00:00Z"
ASSEMBLY_RECEIPT_PATH = ROOT / "rnd" / "research" / "RND0037_DEVELOPMENT_ASSEMBLY_RECEIPT.json"

class RND0060EDevelopmentError(ValueError): pass

def _require(c,m):
    if not c: raise RND0060EDevelopmentError(m)

def _sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def _declaration():
    return {"independent_of_q003":True,"hypothesis":"A fixed intraday volatility-contraction state followed by first directional range expansion has positive net short-horizon expectancy under fixed rules.","fixed_parameters":{"timeframe":"M5","observation_time_utc":"11:30","baseline_bars":18,"short_bars":6,"contraction_ratio_max":1/3,"range_field":"MID_HIGH_LOW","breakout_rule":"FIRST_STRICT_CLOSE_OUTSIDE_SHORT_RANGE","entry_delay_eligible_bars":1,"entry_must_remain_in_frozen_session":True,"hold_eligible_bars":3,"maximum_one_trade_per_symbol_day":True},"datasets":["DEVELOPMENT_2015_2020"],"strategy_references":[],"declared_trial_count":1,"parameter_search":False,"automatic_promotion":False,"broker_writes":False,"capital_authority":False}

def _validate_assembly_report(path):
    receipt=_json(ASSEMBLY_RECEIPT_PATH)
    _require(receipt.get("status")=="COMPLETE","RND-0037 assembly receipt incomplete")
    _require(receipt.get("pair_years")=="24/24","RND-0037 pair-year receipt incomplete")
    _require(receipt.get("full_development_structural_evidence_complete") is True,"RND-0037 structural evidence incomplete")
    for key in ("strategy_evaluation","validation_open","final_test_open","broker_writes","capital_authority"):
        _require(receipt.get(key) is False,f"RND-0037 prohibited authority opened: {key}")
    report=Path(path).expanduser().resolve(); _require(report.is_file(),"RND-0037 assembly report missing")
    _require(_sha256_file(report)==receipt.get("external_report_sha256"),"RND-0037 assembly report SHA mismatch")

def _load_2020_rows(root):
    acquisition=_json(ACQUISITION_PATH); calendar=_json(CALENDAR_PATH); root=Path(root).expanduser().resolve(); rows_by_symbol={}; identities={}
    for symbol in SYMBOLS:
        shard_root=root/symbol/"2020-development"
        _require(verify_existing_shard(shard_root,symbol,SHARD,acquisition,calendar),f"{symbol}: 2020 shard identity verification failed")
        proof=boundary_proof(shard_root,symbol); _require(proof["rows_at_or_after_validation_boundary"]==0,f"{symbol}: validation boundary breach")
        rows=_json(shard_root/"canonical_rows.json"); _require(isinstance(rows,list) and rows,f"{symbol}: 2020 canonical rows missing")
        manifest=_json(shard_root/"quarantine_manifest.json")
        rows_by_symbol[symbol]=rows; identities[symbol]={"row_count":len(rows),"canonical_rows_sha256":manifest.get("canonical_rows_sha256"),"raw_bundle_sha256":manifest.get("aggregate_raw_bundle_sha256"),"standard_schedule_sha256":manifest.get("standard_schedule_sha256"),"boundary_proof":proof}
    return identities,rows_by_symbol

def classify(per_symbol,portfolio):
    _require(set(per_symbol)==set(SYMBOLS),"exact four-pair result set required")
    pair_positive=sum(1 for s in SYMBOLS if float(per_symbol[s]["terminal_net_equity"])>=1.0)
    annual={y:0.0 for y in range(2015,2021)}
    for s in SYMBOLS:
        for y in annual: annual[y]+=float(per_symbol[s]["annual_realized_net"][y])
    realized={s:float(per_symbol[s]["realized_net_sum"]) for s in SYMBOLS}; total=sum(realized.values()); loo={s:total-realized[s] for s in SYMBOLS}
    criteria={"portfolio_terminal_net_equity_gt_1":float(portfolio["final_equal_unit_normalized_equity_index"])>1.0,"portfolio_realized_net_sum_gt_0":float(portfolio["realized_completed_trade_net_return_sum"])>0.0,"at_least_3_of_4_pair_terminal_equities_gte_1":pair_positive>=3,"portfolio_max_drawdown_gte_minus_0_10":float(portfolio["equal_unit_normalized_max_drawdown"])>=-0.10,"at_least_4_of_6_positive_development_years":sum(1 for v in annual.values() if v>0.0)>=4,"every_leave_one_pair_out_realized_net_sum_gt_0":all(v>0.0 for v in loo.values()),"integrity_reconciliation_pass":portfolio.get("status")=="PASS"}
    return {"classification":"ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW" if all(criteria.values()) else "DEVELOPMENT_FALSIFIED","criteria":criteria,"pair_terminal_equity_positive_count":pair_positive,"annual_aggregate_realized_net":annual,"positive_development_year_count":sum(1 for v in annual.values() if v>0.0),"leave_one_pair_out_realized_net_sum":loo}

def run(audusd_2015_shard,cross_pair_2015_root,development_2016_2019_root,development_2020_root,rnd0037_assembly_report):
    validate_research_declaration(_declaration()); _validate_assembly_report(rnd0037_assembly_report)
    plan=load_plan(PLAN_PATH); _require(plan.get("validation_open") is False,"validation unexpectedly open"); _require(plan.get("final_test_open") is False,"reserved final unexpectedly open")
    identities_2015_2019,verified,historical_rows=_verify_evidence(plan,audusd_2015_shard,cross_pair_2015_root,development_2016_2019_root,load_rows=True); _require(verified==20,"2015-2019 evidence verification not 20/20")
    identities_2020,rows_2020=_load_2020_rows(development_2020_root); full_rows={}
    for symbol in SYMBOLS:
        rows=list(historical_rows[symbol])+list(rows_2020[symbol]); ts=[r["timestamp_utc"] for r in rows]
        _require(ts==sorted(ts),f"{symbol}: full-development rows not chronological"); _require(len(ts)==len(set(ts)),f"{symbol}: duplicate full-development timestamps"); _require(ts[0]>=DEVELOPMENT_START,f"{symbol}: pre-development row detected"); _require(ts[-1]<DEVELOPMENT_END,f"{symbol}: validation row detected"); full_rows[symbol]=rows
    per_symbol={s:evaluate_symbol(s,full_rows[s]) for s in SYMBOLS}; portfolio=concurrent_reference_statistics(per_symbol); decision=classify(per_symbol,portfolio)
    return {"contract_version":"RND0060E-full-development-v1","task_id":"RND-0060E","mode":"SINGLE_PREDECLARED_VOLATILITY_CONTRACTION_EXPANSION","development_interval":{"start_inclusive_utc":DEVELOPMENT_START,"end_exclusive_utc":DEVELOPMENT_END},"declaration":_declaration(),"evidence_identity":{"verified_2015_2019":"20/20","verified_2020":"4/4","pair_years":"24/24","identities_2015_2019":identities_2015_2019,"identities_2020":identities_2020},"per_symbol":per_symbol,"portfolio":portfolio,"falsification_screen":decision,"trial_count":1,"parameter_search":False,"q003_reference":False,"rnd0060a_reference":False,"rnd0060b_reference":False,"rnd0060c_reference":False,"rnd0060d_reference":False,"validation_open":False,"final_test_open":False,"reserved_final_access":False,"portfolio_sizing":False,"broker_writes":False,"capital_authority":False,"automatic_promotion":False,"automatic_merge":False,"status":"COMPLETE_REQUIRES_HUMAN_REVIEW"}

def _write_new(path,value):
    path=Path(path).expanduser().resolve(); _require(path!=ROOT and ROOT not in path.parents,"research report must remain outside repository"); _require(not path.exists(),"report exists; overwrite prohibited"); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n",encoding="utf-8"); return path

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--audusd-2015-shard",required=True); p.add_argument("--cross-pair-2015-root",required=True); p.add_argument("--development-2016-2019-root",required=True); p.add_argument("--development-2020-root",required=True); p.add_argument("--rnd0037-assembly-report",required=True); p.add_argument("--report",required=True); a=p.parse_args(argv)
    value=run(a.audusd_2015_shard,a.cross_pair_2015_root,a.development_2016_2019_root,a.development_2020_root,a.rnd0037_assembly_report); output=_write_new(a.report,value); screen=value["falsification_screen"]
    print("RND0060E_FULL_DEVELOPMENT: COMPLETE"); print("verified_2015_2019=20/20"); print("verified_2020=4/4"); print("pair_years=24/24"); print("trial_count=1"); print("parameter_search=FALSE"); print(f"classification={screen['classification']}"); print("validation_open=FALSE"); print("final_test_open=FALSE"); print("reserved_final_access=FALSE"); print("broker_writes=FALSE"); print("capital_authority=FALSE"); print(f"report={output}"); print(f"report_sha256={_sha256_file(output)}"); return 0

if __name__=="__main__": raise SystemExit(main())
