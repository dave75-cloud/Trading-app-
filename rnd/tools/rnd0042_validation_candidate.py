#!/usr/bin/env python3
"""Evaluate the sole RND-0042 candidate on sealed validation evidence."""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from oanda_historical_acquisition import _utc
from oanda_historical_quarantine import _json
from rnd0035_concurrent_reference_stats import concurrent_reference_statistics
from rnd0035_cost_diagnostics import cost_bridge
from rnd0035_stationary_bootstrap import bootstrap_configuration, declared_configuration_grid
from rnd0042_validation_adapter import reconstruct_validation_candidate

SYMBOLS = ("AUDUSD","EURUSD","GBPUSD","USDJPY")
START = "2020-12-31T19:15:00Z"
END = "2023-01-01T09:40:00Z"
SEAL_SHA = "b2b9a48e204910d3e87ed7af18ad4b47a35ae33681b1d7c5d1e75a15d22af35c"
AUTH = ROOT / "rnd/research/RND0042_VALIDATION_OUTCOME_AUTHORIZATION.json"

class RND0042Error(ValueError): pass

def req(x,m):
    if not x: raise RND0042Error(m)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def authorization():
    a=_json(AUTH)
    req(a.get("task_id")=="RND-0042" and a.get("status")=="ACTIVE","authorization inactive")
    req(a.get("scope")=="FIXED_0006_SEALED_VALIDATION_EVALUATION_ONLY","authorization scope drift")
    req(a.get("candidate_threshold")==0.0006 and a.get("validation_outcomes_authorized") is True,"candidate not authorized")
    for k in ("alternate_thresholds","r000_validation_comparator","parameter_search","strategy_selection","reserved_final_open","portfolio_sizing","broker_writes","capital_authority","automatic_promotion","automatic_merge"):
        req(a.get(k) is False, f"prohibited authority opened: {k}")
    return a

def load_rows(root,symbol):
    p=Path(root).expanduser().resolve()/symbol/"validation"/"canonical_rows.json"
    rows=_json(p); req(isinstance(rows,list) and rows,f"{symbol}: rows missing")
    s,e=_utc(START,"start"),_utc(END,"end")
    prev=None
    for r in rows:
        t=_utc(r["timestamp_utc"],f"{symbol}.timestamp")
        req(s <= t < e,f"{symbol}: boundary breach")
        if prev is not None: req(t>prev,f"{symbol}: chronology failure")
        prev=t
    return rows

def summary(r):
    return {"trades":r["completed_trade_count"],"hit_rate":r["net_hit_rate"],"gross_equity_index":r["completed_trade_gross_equity_index"],"net_equity_index":r["completed_trade_net_equity_index"],"net_max_drawdown":r["completed_trade_net_max_drawdown"],"execution_cost_drag":r["total_execution_cost_drag"]}

def run(evidence_root, seal_report):
    authorization()
    req(sha(seal_report)==SEAL_SHA,"structural seal SHA mismatch")
    seal=_json(seal_report)
    req(seal.get("verified_symbols")=="4/4" and seal.get("reserved_final_open") is False,"invalid structural seal")
    results={s:reconstruct_validation_candidate(s,load_rows(evidence_root,s)) for s in SYMBOLS}
    per_pair={s:summary(results[s]) for s in SYMBOLS}
    trades=[]
    year_sum=defaultdict(float); pair_sum={}
    for s in SYMBOLS:
        pair_trades=results[s]["trades"]
        pair_sum[s]=sum(float(t["net_return"]) for t in pair_trades)
        trades.extend(pair_trades)
        for t in pair_trades:
            year=str(t["exit_timestamp"])[:4]
            year_sum[year]+=float(t["net_return"])
    pos_pair={k:v for k,v in pair_sum.items() if v>0}; pos_year={k:v for k,v in year_sum.items() if v>0}
    pair_pos_total=sum(pos_pair.values()); year_pos_total=sum(pos_year.values())
    pair_share=max((v/pair_pos_total for v in pos_pair.values()),default=0.0)
    year_share=max((v/year_pos_total for v in pos_year.values()),default=0.0)
    concurrent=concurrent_reference_statistics(results)
    cost={s:cost_bridge(results[s]["trades"]) for s in SYMBOLS}
    boot={}
    for s in SYMBOLS:
        stream=[{"symbol":s,"net_return":t["net_return"]} for t in results[s]["trades"]]
        boot[s]=[bootstrap_configuration(stream,c["seed"],c["expected_block_length_trades"]) for c in declared_configuration_grid()]
    c1=concurrent["final_equal_unit_normalized_equity_index"]>1.0
    c2=concurrent["realized_completed_trade_net_return_sum"]>0
    c3=sum(1 for s in SYMBOLS if per_pair[s]["net_equity_index"]>=1.0)>=3
    c4=pair_share<=0.70
    c5=year_share<=0.70
    c6=concurrent["equal_unit_normalized_max_drawdown"]>=-0.10
    c7=True
    crit={"1_terminal_equity_positive":c1,"2_realized_net_positive":c2,"3_at_least_3_pairs_nonnegative":c3,"4_pair_concentration_ok":c4,"5_year_concentration_ok":c5,"6_drawdown_ok":c6,"7_identity_boundary_warmup_ok":c7}
    if not (c1 and c2 and c6 and c7): classification="VALIDATION_REJECTED"
    elif not (c3 and c4 and c5): classification="VALIDATION_INCONCLUSIVE_CONCENTRATED"
    else: classification="VALIDATION_SUPPORTED"
    return {"contract_version":"RND0042-validation-candidate-v1","task_id":"RND-0042","candidate_threshold":0.0006,"warmup_rows_used":0,"warmup_policy":"ZERO_OF_AT_MOST_50_STATE_ONLY_ROWS","structural_seal_sha256":SEAL_SHA,"per_pair":per_pair,"pair_net_return_sum":pair_sum,"year_net_return_sum":dict(sorted(year_sum.items())),"max_positive_pair_contribution_share":pair_share,"max_positive_year_contribution_share":year_share,"cost_diagnostics":cost,"stationary_bootstrap":boot,"four_pair_concurrent_reference":concurrent,"criteria":crit,"classification":classification,"parameter_search":False,"strategy_selection":False,"reserved_final_open":False,"broker_writes":False,"capital_authority":False,"automatic_promotion":False,"automatic_merge":False,"status":"COMPLETE_REQUIRES_HUMAN_REVIEW"}

def write_new(path,val):
    p=Path(path).expanduser().resolve(); req(not p.exists(),"report exists; overwrite prohibited")
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(val,sort_keys=True,indent=2)+"\n")
    return p

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--evidence-root",required=True); p.add_argument("--seal-report",required=True); p.add_argument("--report",required=True); a=p.parse_args(argv)
    v=run(a.evidence_root,a.seal_report); out=write_new(a.report,v)
    print("RND0042_VALIDATION_CANDIDATE: COMPLETE"); print("candidate_threshold=0.0006"); print(f"classification={v['classification']}"); print("parameter_search=FALSE"); print("strategy_selection=FALSE"); print("reserved_final_open=FALSE"); print("broker_writes=FALSE"); print("capital_authority=FALSE"); print(f"report={out}"); print(f"report_sha256={sha(out)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
