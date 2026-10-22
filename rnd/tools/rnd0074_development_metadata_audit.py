#!/usr/bin/env python3
"""RND-0074 read-only 2016-2019 development metadata integrity/gap auditor. No price parsing or writes."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
YEARS = (2016, 2017, 2018, 2019)
ROOT_NAME = "rnd0033-development-history-2016-2019"
NY = ZoneInfo("America/New_York")
HASH_FILES = {
    "raw_bundle_file_sha256": "raw_bundle.bin",
    "canonical_rows_file_sha256": "canonical_rows.json",
    "page_evidence_file_sha256": "page_evidence.json",
    "standard_schedule_file_sha256": "standard_schedule.json",
    "discrepancy_ledger_file_sha256": "discrepancy_ledger.json",
}

class AuditError(ValueError):
    pass

def fail(message):
    raise AuditError("FAIL_CLOSED: " + message)

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def validate_timestamp_strings(rows, label, start_year):
    if not isinstance(rows, list) or not all(isinstance(x, str) for x in rows):
        fail(label + ": timestamp list required")
    previous = None
    parsed = []
    for stamp in rows:
        try:
            if not stamp.endswith("Z"):
                raise ValueError("not UTC")
            dt = datetime.fromisoformat(stamp[:-1] + "+00:00")
        except ValueError:
            fail(label + ": invalid timestamp")
        if dt.year != start_year or dt.second or dt.microsecond or dt.minute % 5:
            fail(label + ": outside year or non-M5 timestamp")
        if previous is not None and dt <= previous:
            fail(label + ": not unique ordered")
        parsed.append(dt)
        previous = dt
    return parsed

def summarize(shard, pair, year, verify_hashes=True):
    shard = Path(shard)
    if shard.is_symlink() or not shard.is_dir():
        fail(f"{pair}/{year}: unsafe or absent shard")
    names = ["quarantine_manifest.json", "standard_schedule.json", "discrepancy_ledger.json"]
    if verify_hashes:
        names += list(HASH_FILES.values())
    for name in set(names):
        path = shard / name
        if path.is_symlink() or not path.is_file():
            fail(f"{pair}/{year}: unsafe or missing {name}")
    m = load_json(shard / "quarantine_manifest.json")
    identity = {
        "symbol": pair, "year": year, "provider": "OANDA",
        "environment": "PRACTICE", "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "complete_candles_only": True, "seal_allowed": False,
        "status": "QUARANTINED_UNRESOLVED_DISCREPANCIES",
        "seal_block_reason": "UNRESOLVED_CALENDAR_DISCREPANCIES",
        "start_utc": f"{year}-01-01T00:00:00Z",
        "end_utc": f"{year+1}-01-01T00:00:00Z",
    }
    if not isinstance(m, dict) or any(m.get(k) != v for k, v in identity.items()):
        fail(f"{pair}/{year}: identity/quarantine mismatch")
    if verify_hashes:
        for key, name in HASH_FILES.items():
            expected = m.get(key)
            if not isinstance(expected, str) or len(expected) != 64 or sha256_file(shard / name) != expected:
                fail(f"{pair}/{year}: SHA-256 mismatch for {name}")
    schedule = load_json(shard / "standard_schedule.json")
    ledger = load_json(shard / "discrepancy_ledger.json")
    if not isinstance(ledger, dict) or ledger.get("resolved") is not False or ledger.get("seal_allowed") is not False:
        fail(f"{pair}/{year}: ledger authority mismatch")
    sched = validate_timestamp_strings(schedule, "schedule", year)
    missing = validate_timestamp_strings(ledger.get("missing_timestamps"), "missing", year)
    unexpected = validate_timestamp_strings(ledger.get("unexpected_timestamps"), "unexpected", year)
    expected = set(sched)
    if not set(missing).issubset(expected) or set(unexpected) & expected:
        fail(f"{pair}/{year}: discrepancy-set membership mismatch")
    if (
        len(sched) != ledger.get("expected_count")
        or len(missing) != ledger.get("missing_count")
        or len(unexpected) != ledger.get("unexpected_count")
        or ledger.get("actual_count") != len(sched)-len(missing)+len(unexpected)
        or m.get("row_count") != ledger.get("actual_count")
        or m.get("missing_count") != len(missing)
        or m.get("unexpected_count") != len(unexpected)
        or m.get("expected_standard_session_count") != len(sched)
    ):
        fail(f"{pair}/{year}: ledger/count reconciliation mismatch")
    # Exact thresholds from RND-0031; closure-shaped is NOT proof of closure.
    bands, runs = Counter(), Counter()
    prior, length = None, 0
    def add_run(n):
        if n:
            group = "short" if n <= 3 else "closure_shaped" if n >= 12 else "intermediate"
            runs[group] += 1
            bands[group + "_bars"] += n
    for dt in missing:
        ny = dt.astimezone(NY)
        bands["missing_near_rollover" if ny.hour in (16, 17, 18) else "missing_other_hours"] += 1
        if prior is not None and int((dt-prior).total_seconds()) != 300:
            add_run(length)
            length = 0
        length += 1
        prior = dt
    add_run(length)
    rollover = sum(dt.astimezone(NY).strftime("%H:%M") == "17:00" for dt in unexpected)
    if bands["short_bars"] + bands["intermediate_bars"] + bands["closure_shaped_bars"] != len(missing):
        fail(f"{pair}/{year}: gap accounting mismatch")
    return {
        "pair": pair, "year": year, "rows": ledger["actual_count"],
        "missing": len(missing), "unexpected": len(unexpected),
        "unexpected_at_1700_ny": rollover,
        "unexpected_elsewhere": len(unexpected)-rollover,
        "short_bars": bands["short_bars"],
        "intermediate_bars": bands["intermediate_bars"],
        "closure_shaped_bars": bands["closure_shaped_bars"],
        "short_runs": runs["short"], "intermediate_runs": runs["intermediate"],
        "closure_shaped_runs": runs["closure_shaped"],
        "missing_near_rollover": bands["missing_near_rollover"],
        "hashes_checked": verify_hashes, "admitted": False,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Exact RND0033 development evidence root")
    parser.add_argument("--pair", required=True, choices=PAIRS)
    parser.add_argument("--year", required=True, type=int, choices=YEARS)
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser()
    if root.is_symlink() or root.name != ROOT_NAME or not root.is_dir():
        fail("expected exact development root; symlinks rejected")
    pair = root / args.pair
    if pair.is_symlink() or not pair.is_dir():
        fail("unsafe or absent pair directory")
    result = summarize(pair / str(args.year), args.pair, args.year)
    print("RND0074_METADATA_AUDIT: STRUCTURAL_METADATA_CHECK_PASS")
    for key, value in result.items():
        print(f"{key}={value}")
    print("source_quarantine_unchanged=TRUE")
    print("strategy_evaluation=FALSE")
    print("calendar_promotion=FALSE")

if __name__ == "__main__":
    try:
        main()
    except (AuditError, OSError, ValueError, TypeError, KeyError) as exc:
        raise SystemExit(str(exc))
