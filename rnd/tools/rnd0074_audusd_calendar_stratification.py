"""RND-0074: 2019 AUDUSD NY-close missingness by local calendar strata.

Read-only, outcome-blind, original source quarantine retained.
Imports the separately verified four-pair shared-reference integrity gate.
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from rnd0074_development_metadata_audit import fail
from rnd0074_shared_schedule_diagnostic import (
    YEAR, HOLIDAYS, PAIRS, START, END, verified_sources,
)
from rnd0074_session_clock_rehearsal import session_interval

OFFSETS = (15, 20)

def cells_for_days(schedule, missing, days):
    """Pure analytical kernel: deterministic 2019 local-date classification."""
    cells = defaultdict(lambda: {"eligible": 0, "missing": 0, "affected_dates": set()})
    observed = {"by_offset": Counter(), "union_dates": set(), "membership": Counter()}
    for local in days:
        if local.year != YEAR or local.weekday() >= 5:
            fail("invalid local date passed to calendar kernel")
        clock = session_interval("NEW_YORK", local.isoformat())
        anchor = datetime.fromisoformat(clock.close_utc.replace("Z", "+00:00"))
        for offset in OFFSETS:
            stamp = anchor + timedelta(minutes=offset)
            if not START <= stamp < END or stamp not in schedule:
                continue
            keys = (("month", local.strftime("%m")),
                    ("weekday", local.strftime("%A")),
                    ("offset", f"{offset:+d}"))
            for key in keys:
                cells[key]["eligible"] += 1
            if stamp in missing["AUDUSD"]:
                observed["by_offset"][offset] += 1
                observed["union_dates"].add(local.isoformat())
                observed["membership"][1+sum(stamp in missing[p] for p in PAIRS if p!="AUDUSD")] += 1
                for key in keys:
                    cells[key]["missing"] += 1
                    cells[key]["affected_dates"].add(local.isoformat())
    table = {}
    for (dimension, label), row in sorted(cells.items()):
        table.setdefault(dimension, {})[label] = {
            "eligible": row["eligible"],
            "missing": row["missing"],
            "present": row["eligible"]-row["missing"],
            "coverage_pct": round(100*(row["eligible"]-row["missing"])/row["eligible"],4)
                            if row["eligible"] else None,
            "distinct_affected_dates": len(row["affected_dates"]),
        }
    return {
        "strata":table,
        "audusd_missing_by_offset":{f"+{o}":observed["by_offset"][o] for o in OFFSETS},
        "audusd_distinct_affected_dates":len(observed["union_dates"]),
        "audusd_missing_timestamp_pair_membership":{
            str(k):observed["membership"][k] for k in (1,2,3,4)},
    }

def assert_consistency(result):
    table = result["strata"]
    expected_missing = sum(result["audusd_missing_by_offset"].values())
    for dimension in ("month", "weekday", "offset"):
        if dimension not in table:
            fail("absent strata: "+dimension)
        rows = table[dimension].values()
        if sum(x["missing"] for x in rows) != expected_missing:
            fail("missingness strata do not reconcile")
        if sum(x["eligible"] for x in rows) != sum(
            x["eligible"] for x in table["offset"].values()):
            fail("eligible strata do not reconcile")
    if sum(result["audusd_missing_timestamp_pair_membership"].values()) != expected_missing:
        fail("pair membership does not reconcile")
    if result["audusd_distinct_affected_dates"] > expected_missing:
        fail("affected date union impossible")

def analyze(root):
    schedule, missing, provenance, digest = verified_sources(Path(root).expanduser())
    dates = [date(YEAR,1,1)+timedelta(days=i) for i in range(365)]
    primary = cells_for_days(schedule, missing, (d for d in dates if d.weekday()<5))
    sensitivity = cells_for_days(schedule, missing, (
        d for d in dates if d.weekday()<5 and d.strftime("%m-%d") not in HOLIDAYS))
    assert_consistency(primary)
    assert_consistency(sensitivity)
    # Match previous independent four-pair metadata results, without baking in 75/68/70/5.
    # No diagnostic should promote when the source fails its integrity gate.
    return {
        "status":"AUDUSD_2019_CALENDAR_STRATIFICATION_METADATA_ONLY_PASS",
        "year":YEAR,"session":"NEW_YORK_CLOSE",
        "offsets":list(OFFSETS),
        "clock_convention":"illustrative_not_provider_verified",
        "holiday_exclusion":"sensitivity_only_Jan_1_Dec_25",
        "schedule_sha256":digest,
        "source_provenance":provenance,
        "primary":primary,
        "exclude_jan1_dec25_sensitivity":sensitivity,
        "limitations":{
            "missing_not_random_not_established":True,
            "liquidity_or_provider_cause_not_established":True,
            "economic_strategy_effect_not_established":True,
            "original_source_restored":False,
            "original_file_provenance_complete":False,
        },
        "prices_parsed":False,"admitted":False,
        "source_quarantine_unchanged":True,
        "broker_writes":False,"strategy_evaluated":False,
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True)
    ap.add_argument("--year",type=int,choices=(2019,),required=True)
    args=ap.parse_args()
    print(json.dumps(analyze(args.root),sort_keys=True))

if __name__ == "__main__":
    main()
