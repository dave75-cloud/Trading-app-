"""RND-0074 2019 shared-schedule metadata diagnostic. No archive writes or prices read.

Only run when 2019 manifest hashes explicitly match the intact AUDUSD schedule.
Not a source restoration, RND-0030 provenance verification, or admission gate.
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
    PAIRS, ROOT_NAME, HASH_FILES, fail, load_json, sha256_file,
    summarize, validate_timestamp_strings,
)
from rnd0074_session_clock_rehearsal import CONVENTIONS, session_interval
from rnd0074_session_offset_coverage import OFFSETS, START, END, compute

YEAR = 2019
HOLIDAYS = {"01-01", "12-25"}
IDENTITY = {
    "year": YEAR, "provider": "OANDA", "environment": "PRACTICE",
    "timeframe": "M5", "price_components": ["bid", "ask", "mid"],
    "complete_candles_only": True, "seal_allowed": False,
    "status": "QUARANTINED_UNRESOLVED_DISCREPANCIES",
    "seal_block_reason": "UNRESOLVED_CALENDAR_DISCREPANCIES",
    "start_utc": "2019-01-01T00:00:00Z",
    "end_utc": "2020-01-01T00:00:00Z",
}

def safe_file(path):
    if path.is_symlink() or not path.is_file():
        fail("unsafe or absent file: " + str(path))

def safe_directory(path):
    if path.is_symlink() or not path.is_dir():
        fail("unsafe or absent directory: " + str(path))

def verified_sources(root):
    """Validate all existing shard files against their manifests, without changing them."""
    safe_directory(root)
    if root.name != ROOT_NAME:
        fail("wrong development archive root")
    reference = root / "AUDUSD" / "2019"
    safe_directory(root / "AUDUSD")
    safe_directory(reference)
    # Unchanged original checker is authoritative for the intact reference.
    intact = summarize(reference, "AUDUSD", YEAR, verify_hashes=True)
    if intact.get("hashes_checked") is not True or intact.get("admitted") is not False:
        fail("reference integrity failure")
    schedule_file = reference / "standard_schedule.json"
    safe_file(schedule_file)
    schedule_sha = sha256_file(schedule_file)
    schedule = set(validate_timestamp_strings(
        load_json(schedule_file), "shared schedule", YEAR))
    manifest_ref = load_json(reference / "quarantine_manifest.json")
    content_sha = manifest_ref.get("standard_schedule_sha256")
    if not isinstance(content_sha, str) or len(content_sha) != 64:
        fail("reference content digest missing")
    missing_by_pair = {}
    provenance = {}
    for pair in PAIRS:
        pair_dir = root / pair
        shard = pair_dir / "2019"
        safe_directory(pair_dir)
        safe_directory(shard)
        manifest_file = shard / "quarantine_manifest.json"
        ledger_file = shard / "discrepancy_ledger.json"
        safe_file(manifest_file)
        safe_file(ledger_file)
        manifest = load_json(manifest_file)
        if not isinstance(manifest, dict) or any(manifest.get(k) != v
                                                    for k,v in IDENTITY.items()):
            fail(pair + ": quarantine/identity mismatch")
        if manifest.get("symbol") != pair:
            fail(pair + ": symbol mismatch")
        if manifest.get("standard_schedule_file_sha256") != schedule_sha:
            fail(pair + ": shared schedule file digest mismatch")
        if manifest.get("standard_schedule_sha256") != content_sha:
            fail(pair + ": shared schedule content digest mismatch")
        original_schedule = shard / "standard_schedule.json"
        if original_schedule.is_symlink():
            fail(pair + ": original schedule is symlink")
        exists = original_schedule.is_file()
        if exists and sha256_file(original_schedule) != schedule_sha:
            fail(pair + ": original schedule does not match manifest")
        if original_schedule.exists() and not exists:
            fail(pair + ": unsafe original schedule")
        # Hash original non-calendar evidence as OPAQUE BYTES; never parse prices.
        for field, filename in HASH_FILES.items():
            if filename == "standard_schedule.json":
                continue
            path = shard / filename
            safe_file(path)
            expected = manifest.get(field)
            if not isinstance(expected, str) or len(expected) != 64:
                fail(pair + ": absent SHA for " + filename)
            if sha256_file(path) != expected:
                fail(pair + ": hash mismatch for " + filename)
        ledger = load_json(ledger_file)
        if not isinstance(ledger, dict) or ledger.get("resolved") is not False or ledger.get("seal_allowed") is not False:
            fail(pair + ": ledger not quarantined")
        missing = set(validate_timestamp_strings(ledger.get("missing_timestamps"), "missing", YEAR))
        unexpected = set(validate_timestamp_strings(ledger.get("unexpected_timestamps"), "unexpected", YEAR))
        if not missing <= schedule or unexpected & schedule:
            fail(pair + ": discrepancy membership mismatch")
        if (ledger.get("expected_count") != len(schedule)
            or ledger.get("missing_count") != len(missing)
            or ledger.get("unexpected_count") != len(unexpected)
            or ledger.get("actual_count") != len(schedule)-len(missing)+len(unexpected)
            or manifest.get("row_count") != ledger.get("actual_count")
            or manifest.get("missing_count") != len(missing)
            or manifest.get("unexpected_count") != len(unexpected)
            or manifest.get("expected_standard_session_count") != len(schedule)):
            fail(pair + ": count reconciliation mismatch")
        missing_by_pair[pair] = missing
        provenance[pair] = {
            "original_schedule_present": exists,
            "schedule_reference": "original_file" if exists else "verified_AUDUSD_2019_shared_reference",
            "non_schedule_original_sha256_checked": True,
            "source_quarantine": manifest["status"],
        }
    return schedule, missing_by_pair, provenance, schedule_sha

def analyze(root):
    root = Path(root).expanduser()
    schedule, missing, provenance, digest = verified_sources(root)
    # AUDUSD is compared against the already tested original strict coverage auditor.
    strict_reference = compute(root / "AUDUSD" / "2019", "AUDUSD", YEAR)
    output = {}
    for session in CONVENTIONS:
        for boundary in ("OPEN","CLOSE"):
            key = session + "_" + boundary
            cells = {}
            for view, exclude in (("primary",False),
                                  ("exclude_jan1_dec25_sensitivity",True)):
                cell = {}
                for offset in OFFSETS:
                    pair_days = {p:set() for p in PAIRS}
                    pair_counts = Counter()
                    membership = Counter()
                    eligible = 0
                    for day_no in range(365):
                        local = date(2019,1,1) + timedelta(days=day_no)
                        if local.weekday() >= 5 or (exclude and local.strftime("%m-%d") in HOLIDAYS):
                            continue
                        clock = session_interval(session, local.isoformat())
                        anchor = datetime.fromisoformat(
                            (clock.open_utc if boundary == "OPEN" else clock.close_utc
                            ).replace("Z","+00:00")).astimezone(timezone.utc)
                        stamp = anchor + timedelta(minutes=offset)
                        if not START <= stamp < END or stamp not in schedule:
                            continue
                        eligible += 1
                        participants = [p for p in PAIRS if stamp in missing[p]]
                        for p in participants:
                            pair_counts[p] += 1
                            pair_days[p].add(local.isoformat())
                        if participants:
                            membership[len(participants)] += 1
                    strict = strict_reference["windows"][key][view][f"offset:{offset:+d}"]
                    if eligible != strict["eligible"] or pair_counts["AUDUSD"] != strict["missing"]:
                        fail("strict AUDUSD offset coverage disagreement")
                    if sum(k*v for k,v in membership.items()) != sum(pair_counts.values()):
                        fail("cross-pair membership reconciliation error")
                    cell[f"{offset:+d}"] = {
                        "eligible":eligible,
                        "pairs":{p:{"missing":pair_counts[p],
                                    "affected_local_dates":len(pair_days[p])} for p in PAIRS},
                        "membership":{str(n):membership[n] for n in (1,2,3,4)},
                    }
                cells[view] = cell
            output[key] = cells
    # A distinct-date union for the historically researched AUDUSD New York close.
    union_dates=set()
    overlap=Counter()
    for day_no in range(365):
        local=date(2019,1,1)+timedelta(days=day_no)
        if local.weekday()>=5 or local.strftime("%m-%d") in HOLIDAYS:
            continue
        clock=session_interval("NEW_YORK",local.isoformat())
        anchor=datetime.fromisoformat(clock.close_utc.replace("Z","+00:00"))
        for offset in (15,20):
            stamp=anchor+timedelta(minutes=offset)
            if START <= stamp < END and stamp in schedule and stamp in missing["AUDUSD"]:
                union_dates.add(local.isoformat())
                overlap[1+sum(stamp in missing[p] for p in PAIRS if p!="AUDUSD")]+=1
    return {
        "status":"SHARED_REFERENCE_METADATA_DIAGNOSTIC_PASS",
        "year":YEAR,"pairs":list(PAIRS),
        "schedule_sha256":digest,"source_provenance":provenance,
        "windows":output,
        "audusd_ny_close_plus15_plus20":{
            "view":"exclude_jan1_dec25_sensitivity",
            "distinct_affected_local_dates":len(union_dates),
            "missing_audusd_timestamps_by_total_missing_pair_count":{
                str(n):overlap[n] for n in (1,2,3,4)},
        },
        "original_source_restored":False,
        "original_schedule_files_verified_for_all_pairs":False,
        "full_original_provenance_verified":False,
        "source_quarantine_unchanged":True,
        "prices_parsed":False,"admitted":False,
        "strategy_evaluated":False,"broker_writes":False,
        "provider_spend_usd":0,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True)
    parser.add_argument("--year",type=int,choices=(2019,),required=True)
    args=parser.parse_args()
    print(json.dumps(analyze(args.root),sort_keys=True))

if __name__=="__main__":
    main()
