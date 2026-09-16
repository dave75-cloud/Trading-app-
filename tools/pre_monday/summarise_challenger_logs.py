#!/usr/bin/env python3
from pathlib import Path
import re,sys,csv
patterns={"trades":[r"\bTrades:\s*(\d+)",r"\bTrades\s+(\d+)"],"final_equity":[r"Final equity[:\s]+([0-9.]+)"],"max_dd_pct":[r"Max DD[:\s]+([+-]?\d+(?:\.\d+)?)%"],"avg_trade_pct":[r"Avg/?trade[:\s]+([+-]?\d+(?:\.\d+)?)%"],"median_trade_pct":[r"Median[:\s]+([+-]?\d+(?:\.\d+)?)%"],"win_rate_pct":[r"Win rate[:\s]+([+-]?\d+(?:\.\d+)?)%"],"best_pct":[r"Best[:\s]+([+-]?\d+(?:\.\d+)?)%"],"worst_pct":[r"Worst[:\s]+([+-]?\d+(?:\.\d+)?)%"]}
def last(text,pats):
 vals=[]
 for p in pats: vals+=re.findall(p,text,re.I)
 return vals[-1] if vals else ""
def main():
 paths=[Path(x) for x in sys.argv[1:]] or sorted((Path.home()/"Projects"/"Trading-app-"/"logs"/"challenger_updates").glob("*.log")); rows=[]
 for p in paths:
  if not p.exists(): continue
  t=p.read_text(errors="replace"); r={"file":str(p)}; r.update({k:last(t,v) for k,v in patterns.items()}); r["synthetic_minus_0_5_clip_seen"]="YES" if re.search(r"capped_return|-0\.5000%|-0\.005\b",t,re.I) else "NO"; rows.append(r)
 fields=["file"]+list(patterns)+["synthetic_minus_0_5_clip_seen"]; w=csv.DictWriter(sys.stdout,fieldnames=fields); w.writeheader(); w.writerows(rows); print("NOTE: legacy diagnostic only; clipped runs do not override frozen M004/M005.",file=sys.stderr)
if __name__=="__main__": main()
