#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

PAIRS=("AUDUSD","EURUSD","GBPUSD","USDJPY")
FIELDS=("o","h","l","c")
FAST,SLOW,VOL_WINDOW,VOL_THRESHOLD=20,50,12,0.0005

def hours(pair): return (11,14) if pair=="AUDUSD" else (11,13)

def load(path: Path):
    if not path.exists(): return pd.DataFrame(columns=["ts",*FIELDS])
    d=pd.read_csv(path)
    if d.empty: return pd.DataFrame(columns=["ts",*FIELDS])
    missing={"ts",*FIELDS}-set(d.columns)
    if missing: raise SystemExit(f"{path} missing columns: {sorted(missing)}")
    d["ts"]=pd.to_datetime(d["ts"],utc=True,errors="raise")
    for c in FIELDS: d[c]=pd.to_numeric(d[c],errors="raise")
    return d[["ts",*FIELDS]].sort_values("ts").drop_duplicates("ts",keep="last").reset_index(drop=True)

def expected(date_text,pair):
    s,e=hours(pair); day=pd.Timestamp(date_text,tz="UTC")
    start=day+pd.Timedelta(hours=s); end=day+pd.Timedelta(hours=e)
    return pd.date_range(start,end,freq="5min",inclusive="left")

def state(d,suffix,pair):
    x=d.copy(); c=x[f"c_{suffix}"]
    x[f"ret_{suffix}"]=c.pct_change()
    x[f"fast_{suffix}"]=c.rolling(FAST,min_periods=FAST).mean()
    x[f"slow_{suffix}"]=c.rolling(SLOW,min_periods=SLOW).mean()
    x[f"vol_{suffix}"]=x[f"ret_{suffix}"].rolling(VOL_WINDOW,min_periods=VOL_WINDOW).std(ddof=0)
    a,b=hours(pair)
    ins=(x.ts.dt.hour>=a)&(x.ts.dt.hour<b)&(x.ts.dt.dayofweek<5)
    vok=x[f"vol_{suffix}"]>=VOL_THRESHOLD
    ready=x[f"fast_{suffix}"].notna()&x[f"slow_{suffix}"].notna()&x[f"vol_{suffix}"].notna()
    raw=np.where(ready&ins&vok&(x[f"fast_{suffix}"]>x[f"slow_{suffix}"]),1,
        np.where(ready&ins&vok&(x[f"fast_{suffix}"]<x[f"slow_{suffix}"]),-1,0))
    x[f"vol_ok_{suffix}"]=vok.fillna(False)
    x[f"raw_{suffix}"]=raw.astype(int)
    x[f"delayed_{suffix}"]=pd.Series(raw,index=x.index).shift(1).fillna(0).astype(int)
    return x

def append(path,rows):
    if not rows: return
    exists=path.exists() and path.stat().st_size>0
    with path.open("a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));
        if not exists: w.writeheader()
        w.writerows(rows)

def dates(d): return set(d.ts.dt.strftime("%Y-%m-%d")) if not d.empty else set()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--twelve-dir",required=True); ap.add_argument("--polygon-dir",required=True); ap.add_argument("--output-dir",required=True); ap.add_argument("--price-tolerance-bps",type=float,default=5); ap.add_argument("--max-sessions-per-run",type=int,default=10); a=ap.parse_args()
    td_dir,pg_dir,out=Path(a.twelve_dir),Path(a.polygon_dir),Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    ledger=out/"provider_acceptance_ledger.csv"; pairledger=out/"provider_acceptance_pair_ledger.csv"
    done=set(pd.read_csv(ledger,dtype=str).session_date_utc) if ledger.exists() and ledger.stat().st_size else set()
    TD={p:load(td_dir/f"{p}_5m.csv") for p in PAIRS}; PG={p:load(pg_dir/f"{p}_5m.csv") for p in PAIRS}
    common=None
    for p in PAIRS:
        x=dates(TD[p])&dates(PG[p]); common=x if common is None else common&x
    candidates=[d for d in sorted(common or set()) if d not in done and pd.Timestamp(d).dayofweek<5]
    agg=[]; pairs=[]; waiting=[]
    for d in candidates[:a.max_sessions_per_run]:
        results=[]; complete=True
        for p in PAIRS:
            exp=expected(d,p); exp_set=set(exp)
            td_present=set(TD[p].loc[TD[p].ts.isin(exp),"ts"]); pg_present=set(PG[p].loc[PG[p].ts.isin(exp),"ts"])
            mt=sorted(exp_set-td_present); mp=sorted(exp_set-pg_present)
            if mt or mp:
                complete=False; waiting.append({"session_date_utc":d,"pair":p,"expected_bars":len(exp),"twelve_missing_bars":len(mt),"polygon_missing_bars":len(mp),"twelve_first_missing":mt[0].isoformat() if mt else "","polygon_first_missing":mp[0].isoformat() if mp else ""}); continue
            t=state(TD[p].rename(columns={c:f"{c}_td" for c in FIELDS}),"td",p)
            g=state(PG[p].rename(columns={c:f"{c}_pg" for c in FIELDS}),"pg",p)
            s=t.merge(g,on="ts",how="inner"); s=s[s.ts.isin(exp)].sort_values("ts").copy()
            if len(s)!=len(exp): complete=False; continue
            for f in FIELDS:
                s[f"{f}_bps"]=(s[f"{f}_td"]-s[f"{f}_pg"]).abs()/s[f"{f}_pg"].abs()*10000
                s[f"{f}_pass"]=s[f"{f}_bps"]<=a.price_tolerance_bps
            oc=(~s.o_pass)|(~s.c_pass); hl=s.o_pass&s.c_pass&((~s.h_pass)|(~s.l_pass))
            raw=s.raw_td!=s.raw_pg; delayed=s.delayed_td!=s.delayed_pg; vol=s.vol_ok_td!=s.vol_ok_pg
            r={"session_date_utc":d,"pair":p,"session_utc":f"{hours(p)[0]:02d}:00-{hours(p)[1]:02d}:00","expected_bars":len(exp),"compared_bars":len(s),"open_close_failure_rows":int(oc.sum()),"high_low_only_failure_rows":int(hl.sum()),"raw_signal_disagreements":int(raw.sum()),"delayed_signal_disagreements":int(delayed.sum()),"volatility_eligibility_disagreements":int(vol.sum()),"median_close_bps_diff":float(s.c_bps.median()),"p95_close_bps_diff":float(s.c_bps.quantile(.95)),"max_close_bps_diff":float(s.c_bps.max()),"max_any_ohlc_bps_diff":float(s[[f"{f}_bps" for f in FIELDS]].max(axis=1).max()),"pair_pass":bool(delayed.sum()==0 and vol.sum()==0)}
            results.append(r)
        if complete and len(results)==4:
            pairs.extend(results); agg.append({"session_date_utc":d,"processed_at_utc":pd.Timestamp.now(tz="UTC").isoformat(),"provider_candidate":"twelve_data","reference_provider":"polygon","total_expected_bars":sum(x["expected_bars"] for x in results),"total_compared_bars":sum(x["compared_bars"] for x in results),"open_close_failure_rows":sum(x["open_close_failure_rows"] for x in results),"high_low_only_failure_rows":sum(x["high_low_only_failure_rows"] for x in results),"raw_signal_disagreements":sum(x["raw_signal_disagreements"] for x in results),"delayed_signal_disagreements":sum(x["delayed_signal_disagreements"] for x in results),"volatility_eligibility_disagreements":sum(x["volatility_eligibility_disagreements"] for x in results),"max_close_bps_diff":max(x["max_close_bps_diff"] for x in results),"max_any_ohlc_bps_diff":max(x["max_any_ohlc_bps_diff"] for x in results),"session_pass":bool(all(x["pair_pass"] for x in results)),"canonical_m005_modified":False})
    append(ledger,agg); append(pairledger,pairs)
    run=pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%SZ"); wait=out/f"waiting_for_complete_overlap_{run}.csv"; pd.DataFrame(waiting).to_csv(wait,index=False)
    cum=pd.read_csv(ledger) if ledger.exists() else pd.DataFrame(); n=len(cum); passes=int(cum.session_pass.astype(str).str.lower().eq("true").sum()) if n else 0; ds=int(pd.to_numeric(cum.delayed_signal_disagreements).sum()) if n else 0; vs=int(pd.to_numeric(cum.volatility_eligibility_disagreements).sum()) if n else 0
    report={"run_id":run,"processed_sessions_this_run":len(agg),"processed_dates_this_run":[x["session_date_utc"] for x in agg],"waiting_rows":len(waiting),"cumulative_sessions":n,"cumulative_passes":passes,"cumulative_failures":n-passes,"cumulative_delayed_signal_disagreements":ds,"cumulative_volatility_disagreements":vs,"provisional_10_session_checkpoint_met":bool(n>=10 and passes==n and ds==0 and vs==0),"canonical_m005_modified":False,"ledger":str(ledger),"pair_ledger":str(pairledger),"waiting_report":str(wait)}
    status=out/f"acceptance_status_{run}.json"; status.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    manifest=out/f"acceptance_manifest_{run}.json"; manifest.write_text(json.dumps({"run_id":run,"logic":{"fast_ma":FAST,"slow_ma":SLOW,"vol_window":VOL_WINDOW,"vol_threshold":VOL_THRESHOLD,"price_tolerance_bps":a.price_tolerance_bps},"hashes":{ledger.name:sha(ledger),pairledger.name:sha(pairledger),wait.name:sha(wait),status.name:sha(status)}},indent=2,sort_keys=True)+"\n")
    print("KQTRL M005 v1.2h — DELAYED PROVIDER ACCEPTANCE LEDGER"); print("="*76); print(f"Processed sessions this run: {len(agg)}"); print(f"Waiting/incomplete pair rows: {len(waiting)}"); print(f"Cumulative reconciled sessions: {n}"); print(f"Cumulative passes: {passes}"); print(f"Cumulative delayed-signal disagreements: {ds}"); print(f"Cumulative volatility disagreements: {vs}"); print(f"10-session provisional checkpoint met: {report['provisional_10_session_checkpoint_met']}"); print("Canonical M005 modified: False"); print(f"Ledger: {ledger}"); print(f"Status: {status}")
if __name__=="__main__": main()
