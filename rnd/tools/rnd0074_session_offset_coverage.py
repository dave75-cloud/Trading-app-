"""RND-0074 2019 outcome-blind M5 timestamp availability; read-only."""
import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "orchestration"))
from rnd0074_development_metadata_audit import (
    PAIRS, ROOT_NAME, fail, load_json, summarize, validate_timestamp_strings)
from rnd0074_session_clock_rehearsal import CONVENTIONS, session_interval

OFFSETS = tuple(range(-30, 30, 5))
START = datetime(2019, 1, 1, tzinfo=timezone.utc)
END = datetime(2020, 1, 1, tzinfo=timezone.utc)

def new_cell():
    return dict(slots=0, eligible=0, present=0, missing=0,
                unscheduled=0, out_of_year=0, unexpected=0)

def populate(cell, stamp, schedule, missing, unexpected):
    cell["slots"] += 1
    if not START <= stamp < END:
        cell["out_of_year"] += 1
    elif stamp in schedule:
        cell["eligible"] += 1
        cell["missing" if stamp in missing else "present"] += 1
    else:
        cell["unscheduled"] += 1
    if stamp in unexpected:
        cell["unexpected"] += 1

def finalize(cell):
    if cell["slots"] != cell["eligible"] + cell["unscheduled"] + cell["out_of_year"]:
        fail("slot denominator mismatch")
    if cell["eligible"] != cell["present"] + cell["missing"]:
        fail("present/missing mismatch")
    return dict(cell, coverage_pct=(round(100*cell["present"]/cell["eligible"], 4)
                                    if cell["eligible"] else None))

def compute(shard, pair, year=2019):
    if pair not in PAIRS or year != 2019:
        fail("unauthorized pair or year")
    checked = summarize(shard, pair, year, verify_hashes=True)
    if checked["hashes_checked"] is not True or checked["admitted"] is not False:
        fail("metadata audit authority mismatch")
    schedule = set(validate_timestamp_strings(
        load_json(Path(shard)/"standard_schedule.json"), "schedule", year))
    ledger = load_json(Path(shard)/"discrepancy_ledger.json")
    missing = set(validate_timestamp_strings(ledger["missing_timestamps"], "missing", year))
    unexpected = set(validate_timestamp_strings(ledger["unexpected_timestamps"], "unexpected", year))
    if not missing <= schedule or unexpected & schedule:
        fail("ledger membership mismatch")
    results = {}
    for session, spec in CONVENTIONS.items():
        for boundary in ("OPEN", "CLOSE"):
            views = {"primary": defaultdict(new_cell),
                     "exclude_jan1_dec25_sensitivity": defaultdict(new_cell)}
            for d in range(365):
                local = date(2019,1,1) + timedelta(days=d)
                if local.weekday() >= 5:
                    continue
                interval = session_interval(session, local.isoformat())
                t = datetime.fromisoformat(
                    (interval.open_utc if boundary == "OPEN" else interval.close_utc)
                    .replace("Z","+00:00")).astimezone(timezone.utc)
                for offset in OFFSETS:
                    stamp = t + timedelta(minutes=offset)
                    for view, cells in views.items():
                        if view != "primary" and local.strftime("%m-%d") in ("01-01","12-25"):
                            continue
                        keys = ("total", f"offset:{offset:+d}",
                                f"month:{local.strftime('%m')}",
                                f"weekday:{local.strftime('%A')}")
                        for key in keys:
                            populate(cells[key], stamp, schedule, missing, unexpected)
            emitted = {}
            for view, cells in views.items():
                rows = {k: finalize(v) for k,v in sorted(cells.items())}
                total = rows["total"]
                for dimension in ("offset:", "month:", "weekday:"):
                    sub = [v for k,v in rows.items() if k.startswith(dimension)]
                    for field in ("slots","eligible","present","missing","unscheduled","out_of_year","unexpected"):
                        if sum(v[field] for v in sub) != total[field]:
                            fail("stratum aggregation mismatch")
                emitted[view] = rows
            results[f"{session}_{boundary}"] = emitted
    return {"status":"METADATA_ONLY_PASS","pair":pair,"year":year,
            "protocol":"RND0074_OUTCOME_BLIND_COVERAGE_ADMISSION_PROTOCOL_V1",
            "integrity":checked,"windows":results,
            "holiday_calendar_verified":False,"calendar_promotion":False,
            "source_quarantine_unchanged":True,"admitted":False,
            "prices_parsed":False,"strategy_evaluated":False,
            "broker_writes":False,"provider_spend_usd":0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--pair",required=True,choices=PAIRS)
    ap.add_argument("--year",required=True,type=int,choices=(2019,))
    args = ap.parse_args()
    root = Path(args.root).expanduser()
    if root.name != ROOT_NAME or root.is_symlink() or not root.is_dir():
        fail("unsafe development root")
    pair = root/args.pair
    if pair.is_symlink() or not pair.is_dir():
        fail("unsafe pair directory")
    print(json.dumps(compute(pair/str(args.year),args.pair,args.year),sort_keys=True))

if __name__ == "__main__":
    main()
