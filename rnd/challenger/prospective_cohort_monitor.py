#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

PAIRS = {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}

def truth(v):
    return str(v).strip().lower() == "true"

def number(v):
    return float(v or 0)

def integer(v):
    return int(float(v or 0))

def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--pair-ledger", required=True)
    a = ap.parse_args()

    baseline = json.loads(Path(a.baseline).read_text())
    ledger = load_csv(a.ledger)
    pairs = load_csv(a.pair_ledger)

    start = baseline["cohort_start_utc"]
    requirement = int(baseline["prospective_requirement_sessions"])
    candidate = baseline["provider_candidate"]
    reference = baseline["reference_provider"]

    cohort = [r for r in ledger if r["session_date_utc"] >= start]
    pair_cohort = [r for r in pairs if r["session_date_utc"] >= start]

    errors = []

    dates = [r["session_date_utc"] for r in cohort]
    if len(dates) != len(set(dates)):
        errors.append("duplicate prospective session dates")

    for r in cohort:
        if r["provider_candidate"] != candidate:
            errors.append(f"{r['session_date_utc']}: candidate provider mismatch")
        if r["reference_provider"] != reference:
            errors.append(f"{r['session_date_utc']}: reference provider mismatch")
        if truth(r["canonical_m005_modified"]):
            errors.append(f"{r['session_date_utc']}: canonical M005 modification recorded")

    by_date = {}
    for r in pair_cohort:
        by_date.setdefault(r["session_date_utc"], set()).add(r["pair"])

    for d in dates:
        if by_date.get(d, set()) != PAIRS:
            errors.append(f"{d}: incomplete or duplicate four-pair coverage")

    delayed = sum(integer(r["delayed_signal_disagreements"]) for r in cohort)
    volatility = sum(integer(r["volatility_eligibility_disagreements"]) for r in cohort)
    clean = sum(truth(r["session_pass"]) for r in cohort)
    failures = len(cohort) - clean

    max_close = max(
        [number(r["max_close_bps_diff"]) for r in cohort],
        default=0.0
    )
    max_any = max(
        [number(r["max_any_ohlc_bps_diff"]) for r in cohort],
        default=0.0
    )

    requirement_met = (
        len(cohort) >= requirement
        and delayed == baseline["required_delayed_signal_disagreements"]
        and volatility == baseline["required_volatility_eligibility_disagreements"]
        and failures == 0
        and not errors
    )

    report = {
        "cohort_start_utc": start,
        "provider_candidate": candidate,
        "reference_provider": reference,
        "prospective_sessions": len(cohort),
        "required_sessions": requirement,
        "clean_sessions": clean,
        "failed_sessions": failures,
        "delayed_signal_disagreements": delayed,
        "volatility_eligibility_disagreements": volatility,
        "max_close_bps_diff": max_close,
        "max_any_ohlc_bps_diff": max_any,
        "integrity_errors": errors,
        "evidence_requirement_met": requirement_met,
        "automatic_promotion": False,
        "human_review_required": True,
        "canonical_m005_modified": False
    }

    print(json.dumps(report, indent=2, sort_keys=True))

    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
