#!/usr/bin/env python3
"""Outcome-blind cumulative ledger advancement for RND-0054."""
from __future__ import annotations

from datetime import datetime, timezone

CANDIDATE_ID = "Q003"
CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
PROSPECTIVE_START_UTC = "2026-10-05T07:25:00Z"
EARLIEST_READOUT_UTC = "2027-04-03T07:25:00Z"


class RND0054LedgerError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0054LedgerError(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0054LedgerError(f"{role}: invalid timestamp") from exc


def _validate_hash_map(hashes):
    _req(isinstance(hashes, dict) and set(hashes) == set(SYMBOLS), "exact four-symbol hash map required")
    for symbol in SYMBOLS:
        item = hashes[symbol]
        _req(isinstance(item, dict), f"{symbol}: hash mapping required")
        for key in ("raw_sha256", "canonical_sha256"):
            value = item.get(key)
            _req(
                isinstance(value, str)
                and len(value) == 64
                and all(c in "0123456789abcdef" for c in value),
                f"{symbol}: invalid {key}",
            )


def validate_record(record):
    _req(isinstance(record, dict), "record mapping required")
    _req(record.get("candidate_id") == CANDIDATE_ID, "candidate id mismatch")
    _req(record.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(tuple(record.get("symbols", ())) == SYMBOLS, "symbol universe mismatch")
    _req(record.get("strategy_evaluation") is False, "strategy evaluation prohibited")
    _req(record.get("reserved_final_access") is False, "reserved final access prohibited")
    _req(record.get("broker_writes") is False, "broker writes prohibited")
    _req(record.get("capital_authority") is False, "capital authority prohibited")
    _req(record.get("automatic_promotion") is False, "automatic promotion prohibited")
    _req(record.get("integrity_pass") is True, "integrity PASS required")
    start = _utc(record.get("start_utc"), "start_utc")
    end = _utc(record.get("end_utc"), "end_utc")
    _req(start < end, "start must precede end")
    _req(start >= _utc(PROSPECTIVE_START_UTC, "prospective start"), "pre-freeze evidence prohibited")
    _req(end <= _utc(EARLIEST_READOUT_UTC, "readout boundary"), "end beyond frozen readout boundary")
    _validate_hash_map(record.get("hashes"))
    return start, end


def audit_and_advance(records):
    _req(isinstance(records, list) and records, "non-empty record list required")
    validated = [(*validate_record(record), record) for record in records]
    validated.sort(key=lambda item: item[0])

    _req(validated[0][0] == _utc(PROSPECTIVE_START_UTC, "prospective start"), "first tranche must start at prospective boundary")

    seen_hash_tuples = set()
    previous_end = None
    for start, end, record in validated:
        if previous_end is not None:
            _req(start == previous_end, "tranche windows must be exactly contiguous")
        previous_end = end
        for symbol in SYMBOLS:
            h = record["hashes"][symbol]
            pair = (symbol, h["raw_sha256"], h["canonical_sha256"])
            _req(pair not in seen_hash_tuples, f"duplicate evidence hash tuple for {symbol}")
            seen_hash_tuples.add(pair)

    cumulative_end = validated[-1][1]
    horizon_met = cumulative_end == _utc(EARLIEST_READOUT_UTC, "readout boundary")
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "tranche_count": len(validated),
        "cumulative_start_utc": validated[0][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cumulative_end_utc": cumulative_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state": "READOUT_ELIGIBLE_PENDING_HUMAN_GATE" if horizon_met else "ACCUMULATING",
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
