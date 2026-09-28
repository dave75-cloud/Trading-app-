#!/usr/bin/env python3
"""Outcome-blind OANDA FX session calendar and quarantine controls for RND-0030."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = "RND-calendar-aware-acquisition-v0.1"
TASK_ID = "RND-0030"
BASE_COMMIT = "baa62608d734f0562470d6b4b1bc4eeeda4aa909"
START = "2015-01-01T00:00:00Z"
END = "2025-01-01T00:00:00Z"
SYMBOLS = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]
YEARS = list(range(2015, 2025))
M5_SECONDS = 300
NY_NAME = "America/New_York"
ALLOWED_EXCEPTION_SOURCE_KINDS = {"OFFICIAL_OANDA_TRADING_HOURS_NOTICE"}
OUTCOME_KEYS = {
    "signal", "position", "trade", "return", "pnl", "equity", "drawdown",
    "sharpe", "win_rate", "strategy_score", "parameter", "feature",
}


class CalendarError(ValueError):
    pass


def _utc(value, role):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise CalendarError(f"{role}: UTC timestamp ending Z required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise CalendarError(f"{role}: invalid timestamp") from exc
    if int(dt.timestamp()) % M5_SECONDS:
        raise CalendarError(f"{role}: M5 grid required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ny_zone():
    try:
        return ZoneInfo(NY_NAME)
    except ZoneInfoNotFoundError as exc:
        raise CalendarError("calendar: America/New_York timezone data unavailable") from exc


def is_standard_session_start(timestamp_utc):
    """True only for ordinary OANDA FX M5 candle starts, excluding holidays."""
    dt = _utc(timestamp_utc, "calendar timestamp")
    local = dt.astimezone(_ny_zone())
    weekday = local.weekday()  # Monday=0 ... Sunday=6
    minute = local.hour * 60 + local.minute
    if weekday == 5:  # Saturday
        return False
    if weekday == 6:  # Sunday opens 17:05 New York
        return minute >= 17 * 60 + 5
    if weekday == 4:  # Friday closes 16:59; final M5 start is 16:55
        return minute <= 16 * 60 + 55
    # Monday-Thursday: ordinary daily break removes the 17:00 M5 start.
    return minute <= 16 * 60 + 55 or minute >= 17 * 60 + 5


def standard_session_schedule(start_utc, end_utc):
    start = _utc(start_utc, "schedule.start")
    end = _utc(end_utc, "schedule.end")
    if start >= end:
        raise CalendarError("schedule: start must precede end")
    rows = []
    cursor = start
    while cursor < end:
        text = _z(cursor)
        if is_standard_session_start(text):
            rows.append(text)
        cursor += timedelta(seconds=M5_SECONDS)
    return rows


def year_shards():
    return [
        {
            "year": year,
            "start_utc": f"{year:04d}-01-01T00:00:00Z",
            "end_utc": f"{year + 1:04d}-01-01T00:00:00Z",
        }
        for year in YEARS
    ]


def schedule_sha256(timestamps):
    _validate_timestamp_list(timestamps, "schedule digest")
    payload = ("\n".join(timestamps) + "\n").encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _validate_timestamp_list(values, role):
    if not isinstance(values, list):
        raise CalendarError(f"{role}: list required")
    parsed = [_utc(x, role) for x in values]
    if len(set(parsed)) != len(parsed) or parsed != sorted(parsed):
        raise CalendarError(f"{role}: unique ordered timestamps required")
    return parsed


def build_discrepancy_ledger(actual_timestamps, expected_timestamps):
    actual_dt = _validate_timestamp_list(actual_timestamps, "actual timestamps")
    expected_dt = _validate_timestamp_list(expected_timestamps, "expected timestamps")
    actual_map = {dt: text for dt, text in zip(actual_dt, actual_timestamps)}
    expected_map = {dt: text for dt, text in zip(expected_dt, expected_timestamps)}
    missing = [expected_map[dt] for dt in expected_dt if dt not in actual_map]
    unexpected = [actual_map[dt] for dt in actual_dt if dt not in expected_map]
    return {
        "expected_count": len(expected_dt),
        "actual_count": len(actual_dt),
        "missing_count": len(missing),
        "unexpected_count": len(unexpected),
        "missing_timestamps": missing,
        "unexpected_timestamps": unexpected,
        "standard_schedule_sha256": schedule_sha256(expected_timestamps),
        "resolved": not missing and not unexpected,
        "seal_allowed": not missing and not unexpected,
    }


def validate_exception_evidence(value):
    required = {"contract_version", "task_id", "horizon", "exceptions", "authority"}
    if not isinstance(value, dict) or set(value) != required:
        raise CalendarError("exception evidence: exact fields required")
    if value["contract_version"] != "RND-calendar-exception-evidence-v0.1" or value["task_id"] != TASK_ID:
        raise CalendarError("exception evidence: identity mismatch")
    if value["horizon"] != {"start_utc": START, "end_utc": END}:
        raise CalendarError("exception evidence: horizon drift")
    if value["authority"] != {
        "strategy_outcomes_allowed": False,
        "returned_candles_can_authorize_exception": False,
        "human_review_required": True,
    }:
        raise CalendarError("exception evidence: authority drift")
    items = value["exceptions"]
    if not isinstance(items, list):
        raise CalendarError("exception evidence: exceptions list required")
    intervals = []
    ids = set()
    for i, item in enumerate(items):
        fields = {
            "exception_id", "start_utc", "end_utc", "reason", "source_kind",
            "source_locator", "source_sha256",
        }
        if not isinstance(item, dict) or set(item) != fields:
            raise CalendarError(f"exception[{i}]: exact fields required")
        if set(k.lower() for k in item) & OUTCOME_KEYS:
            raise CalendarError(f"exception[{i}]: outcome field prohibited")
        eid = item["exception_id"]
        if not isinstance(eid, str) or not eid or eid in ids:
            raise CalendarError(f"exception[{i}]: unique exception_id required")
        ids.add(eid)
        start = _utc(item["start_utc"], f"exception[{i}].start")
        end = _utc(item["end_utc"], f"exception[{i}].end")
        if start >= end or start < _utc(START, "horizon.start") or end > _utc(END, "horizon.end"):
            raise CalendarError(f"exception[{i}]: invalid interval")
        if item["source_kind"] not in ALLOWED_EXCEPTION_SOURCE_KINDS:
            raise CalendarError(f"exception[{i}]: official OANDA source required")
        locator = item["source_locator"]
        if not isinstance(locator, str) or not locator.startswith("https://www.oanda.com/"):
            raise CalendarError(f"exception[{i}]: official OANDA locator required")
        digest = item["source_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise CalendarError(f"exception[{i}]: source SHA-256 required")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise CalendarError(f"exception[{i}]: reason required")
        intervals.append((start, end))
    intervals.sort()
    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            raise CalendarError("exception evidence: overlapping intervals prohibited")
    return True


def apply_exception_evidence(expected_timestamps, evidence):
    validate_exception_evidence(evidence)
    parsed = _validate_timestamp_list(expected_timestamps, "expected timestamps")
    intervals = [
        (_utc(x["start_utc"], "exception.start"), _utc(x["end_utc"], "exception.end"), x["exception_id"])
        for x in evidence["exceptions"]
    ]
    kept = []
    removed = []
    hits = {eid: 0 for _, _, eid in intervals}
    for dt, text in zip(parsed, expected_timestamps):
        match = next((eid for start, end, eid in intervals if start <= dt < end), None)
        if match is None:
            kept.append(text)
        else:
            removed.append({"timestamp_utc": text, "exception_id": match})
            hits[match] += 1
    unused = [eid for eid, count in hits.items() if count == 0]
    if unused:
        raise CalendarError("exception evidence: interval removes no expected timestamp")
    return {"adjusted_expected_timestamps": kept, "removed": removed}


def validate_declaration(value):
    required = {
        "contract_version", "task_id", "base_commit", "status", "horizon",
        "symbols", "standard_session", "sharding", "quarantine",
        "exception_evidence", "reserved_final_test", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CalendarError("declaration: exact fields required")
    if (
        value["contract_version"] != VERSION
        or value["task_id"] != TASK_ID
        or value["base_commit"] != BASE_COMMIT
        or value["status"] != "QUARANTINE_READY"
    ):
        raise CalendarError("declaration: identity/status mismatch")
    if value["horizon"] != {"start_utc": START, "end_utc": END} or value["symbols"] != SYMBOLS:
        raise CalendarError("declaration: horizon/universe drift")
    if value["standard_session"] != {
        "timezone": NY_NAME,
        "weekly_open_local": "Sunday 17:05",
        "weekly_close_local": "Friday 16:59",
        "daily_break_local": "16:59-17:05",
        "candle_granularity": "M5",
        "expected_start_minutes": [0,5,10,15,20,25,30,35,40,45,50,55],
        "public_holiday_exceptions_in_baseline": False,
    }:
        raise CalendarError("declaration: standard-session drift")
    if value["sharding"] != {
        "basis": "UTC_CALENDAR_YEAR",
        "years": YEARS,
        "overwrite_allowed": False,
        "resume_policy": "SKIP_VERIFIED_EXISTING_SHARDS_ONLY",
    }:
        raise CalendarError("declaration: sharding drift")
    if value["quarantine"] != {
        "raw_pages_required": True,
        "canonical_rows_required": True,
        "raw_page_hashes_required": True,
        "aggregate_raw_bundle_hash_required": True,
        "standard_schedule_digest_required": True,
        "discrepancy_ledger_required": True,
        "sealing_allowed_with_unresolved_discrepancies": False,
        "output_must_be_outside_repository": True,
    }:
        raise CalendarError("declaration: quarantine drift")
    if value["exception_evidence"] != {
        "source_must_be_independent_of_returned_candles": True,
        "allowed_source_kinds": ["OFFICIAL_OANDA_TRADING_HOURS_NOTICE"],
        "strategy_outcomes_allowed": False,
        "automatic_exception_inference": False,
    }:
        raise CalendarError("declaration: exception-evidence drift")
    if value["reserved_final_test"] != {
        "state": "SEALED_BOUNDARY_BOUND",
        "start_utc": "2023-01-01T09:40:00Z",
        "end_utc": "2025-01-01T00:00:00Z",
        "structural_acquisition_allowed": True,
        "strategy_metrics_allowed": False,
        "signal_generation_allowed": False,
        "trade_simulation_allowed": False,
        "parameter_selection_allowed": False,
        "human_open_gate_required": True,
    }:
        raise CalendarError("declaration: reserved-test drift")
    if value["authority"] != {
        "strategy_selection": False,
        "broker_writes": False,
        "automatic_merge": False,
        "automatic_promotion": False,
        "capital_authority": False,
        "human_review_required": True,
    }:
        raise CalendarError("declaration: authority escalation")
    return True


def validate_quarantine_target(target, repo_root):
    target = Path(target).expanduser().resolve()
    repo_root = Path(repo_root).resolve()
    if target == repo_root or repo_root in target.parents:
        raise CalendarError("quarantine: output must remain outside repository")
    if target.exists():
        raise CalendarError("quarantine: overwrite prohibited")
    return target
