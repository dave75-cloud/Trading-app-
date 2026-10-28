"""RND-0074: four-pair 2019 session offset missingness and affected dates.

Read-only, development-only, no quote parsing or outcome authority.
"""
import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "orchestration"))
from rnd0074_development_metadata_audit import (
    PAIRS, ROOT_NAME, fail, load_json, summarize, validate_timestamp_strings)
from rnd0074_session_clock_rehearsal import CONVENTIONS, session_interval
from rnd0074_session_offset_coverage import OFFSETS, START, END, compute

def verified_sets(root):
    """Audit ALL four source shards before collecting any cross-pair figures."""
    sources = {}
    for pair in PAIRS:
        pair_dir = root / pair
        shard = pair_dir / "2019"
        if pair_dir.is_symlink() or not pair_dir.is_dir():
            fail("unsafe pair directory")
        verified = summarize(shard, pair, 2019, verify_hashes=True)
        if verified["hashes_checked"] is not True or verified["admitted"] is not False:
            fail("source integrity status mismatch")
        schedule = set(validate_timestamp_strings(
            load_json(shard / "standard_schedule.json"), "schedule", 2019))
        ledger = load_json(shard / "discrepancy_ledger.json")
        missing = set(validate_timestamp_strings(
            ledger["missing_timestamps"], "missing", 2019))
        if not missing <= schedule:
            fail("missing timestamps not in original schedule")
        sources[pair] = (schedule, missing)
    return sources

def aggregate(root):
    root = Path(root).expanduser()
    if root.name != ROOT_NAME or root.is_symlink() or not root.is_dir():
        fail("unsafe or incorrect development root")
    sources = verified_sets(root)
    # Reuse the frozen single-pair implementation; reject any discrepancy.
    coarse = {p: compute(root/p/"2019", p) for p in PAIRS}
    result = {}
    for session in CONVENTIONS:
        for boundary in ("OPEN", "CLOSE"):
            label = session + "_" + boundary
            offsets = {}
            for offset in OFFSETS:
                primary, sensitive = {}, {}
                for exclude, destination in ((False, primary), (True, sensitive)):
                    date_sets = {p: set() for p in PAIRS}
                    missing_counts = Counter()
                    membership = Counter()
                    for ordinal in range(365):
                        local = date(2019, 1, 1) + timedelta(days=ordinal)
                        if local.weekday() >= 5:
                            continue
                        if exclude and local.strftime("%m-%d") in ("01-01", "12-25"):
                            continue
                        interval = session_interval(session, local.isoformat())
                        anchor = datetime.fromisoformat(
                            (interval.open_utc if boundary == "OPEN" else interval.close_utc)
                            .replace("Z", "+00:00")).astimezone(timezone.utc)
                        stamp = anchor + timedelta(minutes=offset)
                        if not START <= stamp < END:
                            continue
                        present_missing = []
                        for p, (schedule, missing) in sources.items():
                            if stamp in schedule and stamp in missing:
                                date_sets[p].add(local.isoformat())
                                missing_counts[p] += 1
                                present_missing.append(p)
                        if present_missing:
                            membership[len(present_missing)] += 1
                    by_pair = {}
                    for p in PAIRS:
                        old = coarse[p]["windows"][label][
                            "exclude_jan1_dec25_sensitivity" if exclude else "primary"
                        ][f"offset:{offset:+d}"]
                        if missing_counts[p] != old["missing"]:
                            fail("cross-pair versus single-pair offset mismatch")
                        by_pair[p] = {"missing": missing_counts[p],
                                      "affected_local_dates": len(date_sets[p]),
                                      "eligible": old["eligible"]}
                        if by_pair[p]["affected_local_dates"] > old["eligible"]:
                            fail("affected-date count impossible")
                    if sum(k*v for k,v in membership.items()) != sum(missing_counts.values()):
                        fail("membership accounting mismatch")
                    destination.update({"pairs":by_pair,
                                        "distinct_missing_timestamps_by_pair_count":
                                        {str(k):membership[k] for k in (1,2,3,4)}})
                offsets[f"{offset:+d}"] = {"primary":primary,
                                           "exclude_jan1_dec25_sensitivity":sensitive}
            result[label] = offsets
    return {"status":"RND0074_CROSS_PAIR_OFFSET_METADATA_ONLY_PASS",
            "year":2019,"pair_count":len(PAIRS),
            "windows":result,
            "source_quarantine_unchanged":True,"admitted":False,
            "prices_parsed":False,"strategy_evaluated":False,
            "broker_writes":False,"provider_spend_usd":0}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True)
    parser.add_argument("--year",type=int,required=True,choices=(2019,))
    args=parser.parse_args()
    print(json.dumps(aggregate(args.root),sort_keys=True))

if __name__=="__main__":
    main()
