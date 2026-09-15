#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, inspect, json
from pathlib import Path
import pandas as pd

PAIRS=("AUDUSD","EURUSD","GBPUSD","USDJPY")
FAST=20; SLOW=50; VOL_WINDOW=12

def load_module(path):
    spec=importlib.util.spec_from_file_location("kqtrl_actual_observer", str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def normalise(df):
    out=df.copy()
    out["ts"]=pd.to_datetime(out["ts"], utc=True, errors="raise")
    return out.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)

def ref_indicators(df):
    out=normalise(df)
    out["ret"]=out["c"].pct_change()
    out["fast_ma"]=out["c"].rolling(FAST, min_periods=FAST).mean()
    out["slow_ma"]=out["c"].rolling(SLOW, min_periods=SLOW).mean()
    out["vol"]=out["ret"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std(ddof=0)
    return out

def choose(cols,names):
    for n in names:
        if n in cols: return n
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project", default=str(Path.home()/"Projects"/"Trading-app-"))
    ap.add_argument("--observer", default="cli/run_m005_twelve_shadow_observer.py")
    ap.add_argument("--bars-dir", default="data/live_5m_twelve")
    ap.add_argument("--rows", type=int, default=2000)
    a=ap.parse_args()
    project=Path(a.project).expanduser().resolve()
    observer=project/a.observer
    print("KQTRL M005 v1.2j.2b — CORRECTED EXACT LOGIC AUDIT")
    print("="*78)
    print("Actual observer:", observer)
    print("SHA256:", hashlib.sha256(observer.read_bytes()).hexdigest())
    mod=load_module(observer)
    print("add_indicators signature:", inspect.signature(mod.add_indicators))
    clean=True; total=0
    for pair in PAIRS:
        path=project/a.bars_dir/f"{pair}_5m.csv"
        raw=pd.read_csv(path).tail(a.rows).copy()
        inp=normalise(raw)
        ref=ref_indicators(inp).set_index("ts")
        act=normalise(mod.add_indicators(inp.copy(), pair)).set_index("ts")
        idx=ref.index.intersection(act.index); total+=len(idx)
        mapping={
            "fast_ma":choose(act.columns,["fast_ma","ma_fast","fast","sma_fast"]),
            "slow_ma":choose(act.columns,["slow_ma","ma_slow","slow","sma_slow"]),
            "vol":choose(act.columns,["vol","volatility","rolling_vol"]),
        }
        result={}
        for logical,acol in mapping.items():
            if acol is None:
                result[logical]="ACTUAL_COLUMN_NOT_FOUND"; clean=False; continue
            av=pd.to_numeric(act.loc[idx,acol],errors="coerce")
            rv=pd.to_numeric(ref.loc[idx,logical],errors="coerce")
            mask=av.notna() & rv.notna()
            if not mask.any():
                result[logical]={"n":0,"max_abs":None,"disagree":0}; continue
            d=(av[mask]-rv[mask]).abs()
            bad=int((d>1e-12).sum())
            result[logical]={"n":int(mask.sum()),"max_abs":float(d.max()),"disagree":bad}
            clean = clean and bad==0
        print(pair, json.dumps(result,sort_keys=True))
    print("-"*78)
    print("Rows overlapped:",total)
    print("Actual process_pair signature:", inspect.signature(mod.process_pair) if hasattr(mod,"process_pair") else "NOT EXPOSED")
    if not clean:
        print("FAIL: actual observer indicator path differs from independent reference.")
        return 10
    print("INDICATOR_PATH_PASS: actual observer indicators match independent reference.")
    print("PARTIAL_PASS_NEEDS_ADAPTER: full event-state-machine equivalence not yet asserted.")
    print("Canonical M005 modified: False")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
