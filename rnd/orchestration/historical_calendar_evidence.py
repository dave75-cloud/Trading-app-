#!/usr/bin/env python3
"""Outcome-blind historical-calendar evidence hardening for RND-0031."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TASK_ID = "RND-0031"
BASE_COMMIT = "d9a93899a1c0fba531f67639685ce9545b2b473c"
NY = ZoneInfo("America/New_York")
M5 = timedelta(minutes=5)
OUTCOME_KEYS = {
    "signal", "position", "trade", "return", "pnl", "equity", "drawdown",
    "sharpe", "win_rate", "strategy_score", "parameter", "feature",
}


class HistoricalCalendarError(ValueError):
    pass


def _parse_utc(value, role="timestamp"):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HistoricalCalendarError(f"{role}: UTC timestamp ending Z required")
    body = value[:-1]
    if "." in body:
        head, frac = body.split(".", 1)
        if not frac or any(ch != "0" for ch in frac):
            raise HistoricalCalendarError(f"{role}: non-zero subsecond timestamp prohibited")
        body = head
    try:
        dt = datetime.fromisoformat(body + "+00:00")
    except ValueError as exc:
        raise HistoricalCalendarError(f"{role}: invalid timestamp") from exc
    if int(dt.timestamp()) % 300:
        raise HistoricalCalendarError(f"{role}: M5 grid required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ordered(values, role):
    if not isinstance(values, list):
        raise HistoricalCalendarError(f"{role}: list required")
    parsed = [_parse_utc(x, role) for x in values]
    if parsed != sorted(parsed) or len(set(parsed)) != len(parsed):
        raise HistoricalCalendarError(f"{role}: unique ordered timestamps required")
    return parsed


def _reject_outcome_keys(value, role="record"):
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in OUTCOME_KEYS:
                raise HistoricalCalendarError(f"{role}: strategy outcome field prohibited")
            _reject_outcome_keys(child, role)
    elif isinstance(value, list):
        for child in value:
            _reject_outcome_keys(child, role)


def historical_1700_candidate_schedule(standard_timestamps, start_utc, end_utc):
    """Add 17:00 NY starts as a hypothesis; never remove authoritative timestamps."""
    standard_dt = _ordered(standard_timestamps, "standard timestamps")
    start = _parse_utc(start_utc, "candidate.start")
    end = _parse_utc(end_utc, "candidate.end")
    if start >= end:
        raise HistoricalCalendarError("candidate: start must precede end")
    candidate = set(standard_dt)
    cursor = start
    while cursor < end:
        local = cursor.astimezone(NY)
        if local.weekday() in (0, 1, 2, 3, 6) and local.hour == 17 and local.minute == 0:
            candidate.add(cursor)
        cursor += M5
    return [_z(x) for x in sorted(candidate)]


def discrepancy(actual_timestamps, expected_timestamps):
    actual = _ordered(actual_timestamps, "actual timestamps")
    expected = _ordered(expected_timestamps, "expected timestamps")
    aset, eset = set(actual), set(expected)
    return {
        "actual_count": len(actual),
        "expected_count": len(expected),
        "missing_timestamps": [_z(x) for x in expected if x not in aset],
        "unexpected_timestamps": [_z(x) for x in actual if x not in eset],
    }


def contiguous_runs(timestamps):
    parsed = _ordered(timestamps, "missing timestamps")
    if not parsed:
        return []
    runs = []
    start = previous = parsed[0]
    count = 1
    for current in parsed[1:]:
        if current - previous == M5:
            previous = current
            count += 1
        else:
            runs.append({"bars": count, "start_utc": _z(start), "end_utc": _z(previous)})
            start = previous = current
            count = 1
    runs.append({"bars": count, "start_utc": _z(start), "end_utc": _z(previous)})
    return runs


def classify_missing_runs(timestamps, short_max_bars=3, closure_candidate_min_bars=12):
    if short_max_bars < 1 or closure_candidate_min_bars <= short_max_bars:
        raise HistoricalCalendarError("classification: invalid thresholds")
    result = {
        "residual_short_gap": [],
        "closure_shaped_candidate": [],
        "unclassified": [],
    }
    for run in contiguous_runs(timestamps):
        if run["bars"] <= short_max_bars:
            result["residual_short_gap"].append(run)
        elif run["bars"] >= closure_candidate_min_bars:
            result["closure_shaped_candidate"].append(run)
        else:
            result["unclassified"].append(run)
    return result


def evaluate_1700_hypothesis(actual_timestamps, standard_timestamps, start_utc, end_utc):
    baseline = discrepancy(actual_timestamps, standard_timestamps)
    candidate_schedule = historical_1700_candidate_schedule(
        standard_timestamps, start_utc, end_utc
    )
    candidate = discrepancy(actual_timestamps, candidate_schedule)
    before = len(baseline["unexpected_timestamps"])
    after = len(candidate["unexpected_timestamps"])
    explained = before - after
    return {
        "candidate_authority": "NONE",
        "calendar_modified": False,
        "evidence_modified": False,
        "strategy_evaluation": False,
        "authoritative_schedule_count": len(standard_timestamps),
        "candidate_schedule_count": len(candidate_schedule),
        "actual_count": len(actual_timestamps),
        "baseline_missing_count": len(baseline["missing_timestamps"]),
        "baseline_unexpected_count": before,
        "candidate_missing_count": len(candidate["missing_timestamps"]),
        "candidate_unexpected_count": after,
        "explained_original_unexpected_count": explained,
        "explained_original_unexpected_fraction": (explained / before if before else 0.0),
        "remaining_unexpected_timestamps": candidate["unexpected_timestamps"],
        "missing_run_classes": classify_missing_runs(candidate["missing_timestamps"]),
    }


def validate_pilot_record(value):
    _reject_outcome_keys(value)
    required = {
        "contract_version", "task_id", "base_commit", "pilot", "integrity",
        "authoritative_calendar_comparison", "candidate_1700_falsification",
        "documentary_evidence", "future_acceptance_policy", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise HistoricalCalendarError("pilot record: exact fields required")
    if (
        value["contract_version"] != "RND-0031-pilot-evidence-v0.1"
        or value["task_id"] != TASK_ID
        or value["base_commit"] != BASE_COMMIT
    ):
        raise HistoricalCalendarError("pilot record: identity drift")
    if value["pilot"] != {
        "symbol": "AUDUSD",
        "year": 2015,
        "timeframe": "M5",
        "evidence_target_label": "rnd0031-audusd-2015-attempt3",
        "development_partition_only": True,
    }:
        raise HistoricalCalendarError("pilot record: pilot identity drift")
    integ = value["integrity"]
    if integ.get("verification") != "PASS" or integ.get("credential_leak_scan") != "PASS":
        raise HistoricalCalendarError("pilot record: integrity not established")
    for key in ("raw_bundle_sha256", "canonical_rows_sha256", "standard_schedule_sha256"):
        digest = integ.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise HistoricalCalendarError(f"pilot record: invalid {key}")
    auth = value["authoritative_calendar_comparison"]
    if auth != {
        "status": "QUARANTINED_UNRESOLVED_DISCREPANCIES",
        "row_count": 74313,
        "expected_standard_session_count": 74907,
        "raw_page_count": 22,
        "missing_count": 849,
        "unexpected_count": 255,
        "ledger_resolved": False,
        "ledger_seal_allowed": False,
        "rnd0030_seal_allowed": False,
        "seal_block_reason": "UNRESOLVED_CALENDAR_DISCREPANCIES",
    }:
        raise HistoricalCalendarError("pilot record: authoritative comparison drift")
    cand = value["candidate_1700_falsification"]
    if cand.get("candidate_authority") != "NONE":
        raise HistoricalCalendarError("pilot record: candidate authority prohibited")
    expected_candidate = {
        "authoritative_schedule_count": 74907,
        "candidate_schedule_count": 75168,
        "actual_count": 74313,
        "candidate_missing_count": 856,
        "candidate_unexpected_count": 1,
        "explained_original_unexpected_count": 254,
        "remaining_unexpected_timestamp_utc": "2015-08-28T21:05:00Z",
        "remaining_unexpected_ny": "2015-08-28T17:05:00-04:00",
        "residual_short_gap_bars": 208,
        "closure_shaped_candidate_bars": 648,
    }
    for key, expected in expected_candidate.items():
        if cand.get(key) != expected:
            raise HistoricalCalendarError(f"pilot record: candidate {key} drift")
    if abs(cand.get("explained_original_unexpected_fraction", -1) - (254 / 255)) > 1e-12:
        raise HistoricalCalendarError("pilot record: candidate fraction drift")
    docs = value["documentary_evidence"]
    if docs.get("exact_2015_oanda_hours_found") is not False:
        raise HistoricalCalendarError("pilot record: undocumented historical authority")
    if docs.get("returned_candles_can_authorize_calendar_change") is not False:
        raise HistoricalCalendarError("pilot record: returned candles cannot authorize change")
    policy = value["future_acceptance_policy"]
    expected_policy = {
        "zero_unexplained_gap_required": False,
        "documented_session_calendar_required": True,
        "explicit_gap_ledger_required": True,
        "synthetic_candles_allowed": False,
        "gap_aware_simulator_required": True,
        "cross_pair_consistency_check_required": True,
        "human_review_required": True,
    }
    if policy != expected_policy:
        raise HistoricalCalendarError("pilot record: acceptance policy drift")
    if value["authority"] != {
        "broker_writes": False,
        "strategy_evaluation": False,
        "calendar_promotion": False,
        "automatic_merge": False,
        "automatic_promotion": False,
        "capital_authority": False,
        "human_review_required": True,
    }:
        raise HistoricalCalendarError("pilot record: authority escalation")
    return True



def validate_documentary_source_register(value):
    _reject_outcome_keys(value)
    required = {
        "contract_version", "task_id", "reviewed_utc_date", "sources",
        "search_result", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise HistoricalCalendarError("documentary register: exact fields required")
    if (
        value["contract_version"] != "RND-0031-documentary-source-register-v0.1"
        or value["task_id"] != TASK_ID
        or value["reviewed_utc_date"] != "2026-09-29"
    ):
        raise HistoricalCalendarError("documentary register: identity drift")
    sources = value["sources"]
    if not isinstance(sources, list) or len(sources) != 3:
        raise HistoricalCalendarError("documentary register: three reviewed sources required")
    expected_ids = {
        "OANDA-CURRENT-AU-HOURS",
        "OANDA-CURRENT-US-LEGAL",
        "OANDA-CURRENT-US-HOLIDAY",
    }
    if {x.get("source_id") for x in sources if isinstance(x, dict)} != expected_ids:
        raise HistoricalCalendarError("documentary register: source identity drift")
    for item in sources:
        if not isinstance(item, dict) or set(item) != {
            "source_id", "publisher", "locator", "supports", "historical_2015_authority"
        }:
            raise HistoricalCalendarError("documentary register: exact source fields required")
        if item["publisher"] != "OANDA":
            raise HistoricalCalendarError("documentary register: OANDA publisher required")
        if not item["locator"].startswith("https://www.oanda.com/"):
            raise HistoricalCalendarError("documentary register: official OANDA locator required")
        if item["historical_2015_authority"] is not False:
            raise HistoricalCalendarError("documentary register: current source cannot claim 2015 authority")
        if not isinstance(item["supports"], str) or not item["supports"].strip():
            raise HistoricalCalendarError("documentary register: support statement required")
    if value["search_result"] != {
        "exact_2015_daily_break_rule_located": False,
        "exact_2015_holiday_schedule_located": False,
        "current_rules_may_be_projected_backward": False,
        "returned_candles_may_substitute_for_documentary_authority": False,
    }:
        raise HistoricalCalendarError("documentary register: search conclusion drift")
    if value["authority"] != {
        "calendar_promotion": False,
        "exception_promotion": False,
        "strategy_evaluation": False,
        "human_review_required": True,
    }:
        raise HistoricalCalendarError("documentary register: authority escalation")
    return True

def record_sha256(value):
    import json
    validate_pilot_record(value)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
