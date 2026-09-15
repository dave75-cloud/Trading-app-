#!/usr/bin/env python3
import argparse,json,os,urllib.request
from collections import Counter
BASE="https://api-fxpractice.oanda.com/v3"; MAP={"AUDUSD":"AUD_USD","EURUSD":"EUR_USD","GBPUSD":"GBP_USD","USDJPY":"USD_JPY"}; LEGS={"AUDUSD":("AUD","USD"),"EURUSD":("EUR","USD"),"GBPUSD":("GBP","USD"),"USDJPY":("USD","JPY")}
def getj(url,t):
 r=urllib.request.Request(url,headers={"Authorization":f"Bearer {t}"},method="GET");
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--entries",required=True); ap.add_argument("--existing",default=""); a=ap.parse_args()
 if os.getenv("OANDA_ENV")!="practice": raise SystemExit("FAIL_CLOSED: OANDA_ENV must be practice")
 tok=os.getenv("OANDA_API_TOKEN",""); acct=os.getenv("OANDA_ACCOUNT_ID","");
 if not tok or not acct: raise SystemExit("FAIL_CLOSED: missing OANDA credentials")
 entries=[]
 for item in filter(None,a.entries.split(",")):
  pair,side=item.strip().upper().split(":"); side=side.lower();
  if pair not in MAP or side not in ("long","short"): raise SystemExit(f"Bad entry {item}")
  entries.append((pair,side))
 existing={}
 if a.existing.strip():
  for item in a.existing.split(","): pair,x=item.strip().upper().split(":"); existing[pair]=float(x)
 s=getj(f"{BASE}/accounts/{acct}/summary",tok)["account"];
 if s.get("currency")!="AUD": raise SystemExit("FAIL_CLOSED: AUD account required")
 nav=float(s["NAV"]); prices=getj(f"{BASE}/accounts/{acct}/pricing?instruments="+",".join(MAP.values()),tok)["prices"]; mids={p["instrument"]:(float(p["bids"][0]["price"])+float(p["asks"][0]["price"]))/2 for p in prices}; audusd=mids["AUD_USD"]
 gross=sum(abs(x) for x in existing.values()); cleg=Counter(); newleg=Counter()
 for pair,x in existing.items():
  if pair in LEGS:
   a1,b1=LEGS[pair]; cleg[a1]+=abs(x); cleg[b1]+=abs(x)
 for pair,_ in entries: a1,b1=LEGS[pair]; newleg[a1]+=1; newleg[b1]+=1
 alpha=1.0
 if entries:
  alpha=min(alpha,max(0,(4-gross)/len(entries)))
  for c,n in newleg.items(): alpha=min(alpha,max(0,(3-cleg[c])/n))
 alpha=max(0,min(1,alpha)); aud_per_base={"AUDUSD":1.0,"EURUSD":mids["EUR_USD"]/audusd,"GBPUSD":mids["GBP_USD"]/audusd,"USDJPY":1/audusd}
 print("KQTRL M006d — DEMO SIZING / PRO-RATA ALLOCATOR"); print("="*74); print(f"NAV_AUD={nav:.2f} desired_each=1x gross_cap=4x currency_leg_cap=3x"); print(f"Existing gross={gross:.4f}x pro_rata_alpha={alpha:.6f}")
 for pair,side in entries:
  units=nav*alpha/aud_per_base[pair]; signed=units if side=="long" else -units; print(f"{pair} {side}: allocation={alpha:.6f}x approx_units={int(round(signed)):+d}")
 print("Calculation only. OANDA write endpoints invoked: FALSE.")
if __name__=="__main__": main()
