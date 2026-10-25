#!/usr/bin/env python3
"""RND-0074: read-only, outcome-blind 2019 session-clock coverage audit."""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORCH = HERE.parent / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))
from rnd0074_session_clock_rehearsal import CONVENTIONS, session_interval
from rnd0074_development_metadata_audit import (
    AuditError, PAIRS, ROOT_NAME, load_json, summarize, validate_timestamp_strings,
)

YEAR = 2019
HALF_WINDOW = timedelta(minutes=30)

def utc_stamp(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def pilot_coverage(shard, pair, year=YEAR):
    if year != YEAR or pair not in PAIRS:
        raise AuditError("FAIL_CLOSED: only 2019 development pilot/pairs authorized")
    integrity = summarize(shard, pair, year, verify_hashes=True)
    schedule = load_json(Path(shard) / "standard_schedule.json")
    ledger = load_json(Path(shard) / "discrepancy_ledger.json")
    scheduled = set(validate_timestamp_strings(schedule, "schedule", year))
    missing = set(validate_timestamp_strings(ledger["missing_timestamps"], "missing", year))
    unexpected = set(validate_timestamp_strings(ledger["unexpected_timestamps"], "unexpected", year))
    available = scheduled - missing
    out = []
    # Predeclared UTC-year pilot; weekdays in each venue's local time. Holiday
    # status is NOT inferred. The unchanged reference schedule defines eligibility.
    for session in CONVENTIONS:
        for phase in ("OPEN", "CLOSE"):
            windows = covered = slots = absent = zero = observed_unexpected = 0
            for ordinal in range(1, 366):
                day = datetime(year, 1, 1).date() + timedelta(days=ordinal - 1)
                if day.weekday() >= 5:
                    continue
                interval = session_interval(session, day.isoformat())
                boundary = utc_stamp(interval.open_utc if phase == "OPEN" else interval.close_utc)
                windows += 1
                window_start = boundary - HALF_WINDOW
                window_end = boundary + HALF_WINDOW  # exclusive
                eligible = [window_start + timedelta(minutes=5*i) for i in range(12)
                            if window_start + timedelta(minutes=5*i) in scheduled]
                n = len(eligible)
                slots += n
                a = sum(t in available for t in eligible)
                covered += a
                absent += n-a
                zero += (n == 0)
                observed_unexpected += sum(window_start <= t < window_end for t in unexpected)
            if slots != covered + absent:
                raise AuditError("FAIL_CLOSED: coverage accounting mismatch")
            out.append({
                "session": session, "boundary": phase,
                "local_boundary": CONVENTIONS[session][1 if phase == "OPEN" else 2],
                "window_minutes_each_side": 30,
                "local_weekday_windows": windows, "zero_eligible_windows": zero,
                "expected_baseline_m5": slots, "present_baseline_m5": covered,
                "missing_baseline_m5": absent,
                "coverage_pct": round(100*covered/slots, 4) if slots else None,
                "unexpected_provider_timestamps_in_windows": observed_unexpected,
            })
    return integrity, out

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--pair", required=True, choices=PAIRS)
    parser.add_argument("--year", required=True, type=int, choices=(2019,))
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser()
    if root.is_symlink() or root.name != ROOT_NAME or not root.is_dir():
        raise AuditError("FAIL_CLOSED: exact development archive root required")
    pair_root = root / args.pair
    if pair_root.is_symlink() or not pair_root.is_dir():
        raise AuditError("FAIL_CLOSED: unsafe pair root")
    _, records = pilot_coverage(pair_root / str(args.year), args.pair, args.year)
    print(f"RND0074_SESSION_COVERAGE: METADATA_ONLY_PASS pair={args.pair} year={args.year}")
    for x in records:
        print(" ".join(f"{k}={v}" for k,v in x.items()))
    print("original_evidence_admitted=FALSE")
    print("original_quarantine_unchanged=TRUE")
    print("market_prices_opened=FALSE")
    print("broker_writes=FALSE")

if __name__ == "__main__":
    try:
        main()
    except (AuditError, OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc))
