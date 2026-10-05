#!/usr/bin/env python3
"""RND-0048 outcome-blind prospective evidence accumulation tracker.

This module validates tranche metadata and cumulative chronology only. It does
not read price values for strategy purposes, generate signals, simulate trades,
compute returns, or classify validation outcomes.
"""
from __future__ import annotations

from datetime import datetime, timezone

TASK_ID = "RND-0048"
CANDIDATE_ID = "Q003"
CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
PROSPECTIVE_START_UTC = "2026-10-05T07:25:00Z"
EARLIEST_READOUT_UTC = "2027-04-03T07:25:00Z"


class RND0048Error(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0048Error(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0048Error(f"{role}: invalid UTC timestamp") from exc


def validate_tranche_record(record):
    _req(isinstance(record, dict), "tranche: mapping required")
    _req(record.get("candidate_id") == CANDIDATE_ID, "tranche: candidate id mismatch")
    _req(record.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "tranche: candidate fingerprint mismatch")
    _req(tuple(record.get("symbols", ())) == SYMBOLS, "tranche: symbol universe mismatch")
    _req(record.get("strategy_evaluation") is False, "tranche: strategy evaluation prohibited")
    _req(record.get("reserved_final_access") is False, "tranche: reserved-final access prohibited")
    _req(record.get("broker_writes") is False, "tranche: broker writes prohibited")
    _req(record.get("capital_authority") is False, "tranche: capital authority prohibited")
    _req(record.get("integrity_pass") is True, "tranche: integrity PASS required")
    start = _utc(record.get("start_utc"), "tranche.start_utc")
    end = _utc(record.get("end_utc"), "tranche.end_utc")
    _req(start < end, "tranche: start must precede end")
    _req(start >= _utc(PROSPECTIVE_START_UTC, "prospective start"), "tranche: pre-freeze evidence prohibited")
    hashes = record.get("hashes")
    _req(isinstance(hashes, dict) and set(hashes) == set(SYMBOLS), "tranche: exact symbol hash map required")
    for symbol in SYMBOLS:
        item = hashes[symbol]
        _req(isinstance(item, dict), f"tranche: {symbol} hash record required")
        for field in ("raw_sha256", "canonical_sha256"):
            value = item.get(field)
            _req(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value), f"tranche: {symbol} invalid {field}")
    return start, end


def audit_cumulative(records):
    _req(isinstance(records, list) and records, "cumulative: non-empty tranche list required")
    intervals = []
    seen_hash_pairs = set()
    for i, record in enumerate(records):
        start, end = validate_tranche_record(record)
        intervals.append((start, end, i))
        for symbol in SYMBOLS:
            item = record["hashes"][symbol]
            pair = (symbol, item["raw_sha256"], item["canonical_sha256"])
            _req(pair not in seen_hash_pairs, f"cumulative: duplicate evidence hash tuple for {symbol}")
            seen_hash_pairs.add(pair)

    intervals.sort(key=lambda x: (x[0], x[1]))
    _req(intervals[0][0] == _utc(PROSPECTIVE_START_UTC, "prospective start"), "cumulative: first tranche must start at prospective boundary")

    previous_end = intervals[0][1]
    for start, end, _ in intervals[1:]:
        _req(start >= previous_end, "cumulative: overlapping tranche windows prohibited")
        previous_end = max(previous_end, end)

    cumulative_start = intervals[0][0]
    cumulative_end = max(end for _, end, _ in intervals)
    horizon_met = cumulative_end >= _utc(EARLIEST_READOUT_UTC, "earliest readout")

    return {
        "task_id": TASK_ID,
        "candidate_id": CANDIDATE_ID,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "tranche_count": len(records),
        "cumulative_start_utc": cumulative_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cumulative_end_utc": cumulative_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "minimum_horizon_days": 180,
        "earliest_readout_utc": EARLIEST_READOUT_UTC,
        "minimum_horizon_met": horizon_met,
        "state": "READOUT_ELIGIBLE_PENDING_HUMAN_GATE" if horizon_met else "ACCUMULATING",
        "strategy_evaluation": False,
        "validation_classification": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
    }
