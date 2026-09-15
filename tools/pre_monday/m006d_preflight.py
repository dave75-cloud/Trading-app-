#!/usr/bin/env python3
import json, os, urllib.request
from datetime import datetime, timezone
BASE="https://api-fxpractice.oanda.com/v3"; PAIRS="AUD_USD,EUR_USD,GBP_USD,USD_JPY"
def getj(url,t):
    r=urllib.request.Request(url,headers={"Authorization":f"Bearer {t}"},method="GET")
    with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)
def main():
    env=os.getenv("OANDA_ENV",""); tok=os.getenv("OANDA_API_TOKEN",""); acct=os.getenv("OANDA_ACCOUNT_ID",""); master=os.getenv("ENABLE_DEMO_EXECUTION","NO").upper()
    print("KQTRL M006d — EXECUTION PREFLIGHT / KILL SWITCH"); print("="*72); checks=[]
    def ck(n,ok,d=""): checks.append(ok); print("PASS" if ok else "FAIL",n,d)
    ck("practice_environment",env=="practice",repr(env)); ck("token_present",bool(tok),f"length={len(tok)}"); ck("account_present",bool(acct)); ck("master_switch_locked",master=="NO",master)
    if not (env=="practice" and tok and acct): print("FAIL_CLOSED"); return 2
    try:
        s=getj(f"{BASE}/accounts/{acct}/summary",tok)["account"]; tr=getj(f"{BASE}/accounts/{acct}/openTrades",tok).get("trades",[]); po=getj(f"{BASE}/accounts/{acct}/pendingOrders",tok).get("orders",[]); ps=getj(f"{BASE}/accounts/{acct}/openPositions",tok).get("positions",[]); prices=getj(f"{BASE}/accounts/{acct}/pricing?instruments={PAIRS}",tok).get("prices",[])
    except Exception as e: print("FAIL_CLOSED network/account GET",type(e).__name__,e); return 3
    ck("account_currency_AUD",s.get("currency")=="AUD",s.get("currency")); ck("no_open_trades",not tr,f"count={len(tr)}"); ck("no_pending_orders",not po,f"count={len(po)}"); ck("no_open_positions",not ps,f"count={len(ps)}")
    now=datetime.now(timezone.utc); stale=[]
    for p in prices:
        if not p.get("time"): stale.append((p.get("instrument"),None)); continue
        dt=datetime.fromisoformat(p["time"].replace("Z","+00:00")); age=(now-dt).total_seconds()/60
        if age>5: stale.append((p.get("instrument"),round(age,2)))
    ck("prices_fresh_le_5m",not stale,str(stale)); print("NAV:",s.get("NAV"),s.get("currency")); print("OANDA write methods implemented: NONE"); print("Order endpoints invoked: FALSE")
    if all(checks): print("PREFLIGHT_PASS_DRY_RUN"); return 0
    print("PREFLIGHT_FAIL_CLOSED"); return 10
if __name__=="__main__": raise SystemExit(main())
