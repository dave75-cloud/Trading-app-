#!/usr/bin/env python3
"""
KQTRL M006d.1 — execution-source authority / cross-feed safety evaluator.
Pure decision engine. No network access. No OANDA write path.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(Path(__file__).with_name("m006d1_policy.json")))
    ap.add_argument("--action", choices=["entry","exit","reversal"], required=True)
    ap.add_argument("--pair", required=True)
    ap.add_argument("--oanda-signal", type=int, choices=[-1,0,1], required=True)
    ap.add_argument("--twelve-signal", type=int, choices=[-1,0,1])
    ap.add_argument("--oanda-vol-ok", choices=["true","false"], required=True)
    ap.add_argument("--twelve-vol-ok", choices=["true","false"])
    ap.add_argument("--oanda-age-min", type=float, required=True)
    ap.add_argument("--twelve-age-min", type=float)
    ap.add_argument("--event-age-min", type=float)
    ap.add_argument("--price-divergence-bps", type=float)
    ap.add_argument("--polygon-status", choices=["pass","disagree","unavailable"], default="unavailable")
    args = ap.parse_args()

    pol = json.loads(Path(args.policy).read_text())
    f = pol["freshness_minutes"]
    pd = pol["price_divergence_bps"]

    reasons = []
    warnings = []
    ovol = args.oanda_vol_ok == "true"
    tvol = None if args.twelve_vol_ok is None else args.twelve_vol_ok == "true"

    if args.oanda_age_min > f["oanda_price_max"]:
        reasons.append(f"OANDA_STALE_{args.oanda_age_min:.2f}M")

    if args.action in ("entry","reversal"):
        if args.event_age_min is None:
            reasons.append("EVENT_AGE_MISSING")
        elif args.event_age_min > f["signal_event_max"]:
            reasons.append(f"EVENT_STALE_{args.event_age_min:.2f}M")

        if args.twelve_signal is None or args.twelve_age_min is None or tvol is None:
            reasons.append("TWELVE_VALIDATOR_MISSING")
        else:
            if args.twelve_age_min > f["twelve_bar_max"]:
                reasons.append(f"TWELVE_STALE_{args.twelve_age_min:.2f}M")
            if args.oanda_signal == 0:
                reasons.append("OANDA_ENTRY_SIGNAL_FLAT")
            if args.twelve_signal != args.oanda_signal:
                reasons.append(
                    f"DIRECTION_DISAGREEMENT_OANDA_{args.oanda_signal}_TWELVE_{args.twelve_signal}"
                )
            if tvol != ovol:
                reasons.append(
                    f"VOL_ELIGIBILITY_DISAGREEMENT_OANDA_{ovol}_TWELVE_{tvol}"
                )
            if not ovol:
                reasons.append("OANDA_VOL_NOT_ELIGIBLE")

        if args.price_divergence_bps is not None:
            if args.price_divergence_bps > pd["entry_block"]:
                reasons.append(f"PRICE_DIVERGENCE_BLOCK_{args.price_divergence_bps:.3f}BPS")
            elif args.price_divergence_bps > pd["warning"]:
                warnings.append(f"PRICE_DIVERGENCE_WARNING_{args.price_divergence_bps:.3f}BPS")

    if args.action == "exit":
        # Risk-reducing exit is governed by OANDA freshness, not cross-feed agreement.
        if args.twelve_signal is not None and args.twelve_signal != args.oanda_signal:
            warnings.append("TWELVE_DISAGREES_BUT_EXIT_NOT_BLOCKED")
        if args.polygon_status == "disagree":
            warnings.append("POLYGON_DISAGREEMENT_LOG_ONLY")

    if args.action == "reversal":
        warnings.append("REVERSAL_MUST_SPLIT_EXIT_THEN_NEW_ENTRY")

    if args.polygon_status == "disagree" and args.action != "exit":
        warnings.append("POLYGON_DISAGREEMENT_LOG_ONLY_NOT_REALTIME_VETO")

    decision = "BLOCK" if reasons else ("ALLOW_DRY_RUN" if args.action != "exit" else "ALLOW_RISK_REDUCING_DRY_RUN")

    print("KQTRL M006d.1 — CROSS-FEED SAFETY DECISION")
    print("="*72)
    print("Pair:", args.pair.upper())
    print("Action:", args.action)
    print("Execution authority: OANDA")
    print("Secondary live validator: Twelve Data")
    print("Delayed reconciliation only: Polygon/Massive")
    print("Decision:", decision)
    if reasons:
        print("Block reasons:")
        for r in reasons: print(" -", r)
    if warnings:
        print("Warnings:")
        for w in warnings: print(" -", w)
    print("OANDA write endpoints invoked: FALSE")
    print("Canonical M005 modified: False")
    return 10 if reasons else 0

if __name__ == "__main__":
    raise SystemExit(main())
