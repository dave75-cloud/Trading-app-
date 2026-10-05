#!/usr/bin/env python3
"""Outcome-blind weekly prospective evidence workflow coordinator for RND-0054.

This module plans the next exact tranche window and, after a separately performed
GET-only acquisition, verifies the sealed tranche before atomically advancing the
cumulative ledger. It has no broker-write, strategy-evaluation, validation-readout,
reserved-final, or capital authority.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rnd0054_generic_verifier import verify_tranche
from rnd0054_ledger import (
    CANDIDATE_FINGERPRINT,
    EARLIEST_READOUT_UTC,
    audit_and_advance,
)

WEEK = timedelta(days=7)


class RND0054WorkflowError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0054WorkflowError(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0054WorkflowError(f"{role}: invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, f"{role}: M5 boundary required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_next(ledger_state, now_utc):
    """Derive the next exact contiguous prospective tranche window."""
    _req(isinstance(ledger_state, dict), "ledger state mapping required")
    _req(ledger_state.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    for field in ("strategy_evaluation", "reserved_final_access", "broker_writes", "capital_authority", "automatic_promotion"):
        _req(ledger_state.get(field) is False, f"{field} must remain false")

    start = _utc(ledger_state.get("cumulative_end_utc"), "cumulative_end_utc")
    boundary = _utc(EARLIEST_READOUT_UTC, "readout boundary")
    now = _utc(now_utc, "now_utc")

    if start == boundary:
        return {"status": "ACCUMULATION_COMPLETE", "window": None}
    _req(start < boundary, "cumulative end beyond readout boundary")

    end = min(start + WEEK, boundary)
    window = {"start_utc": _z(start), "end_utc": _z(end)}
    return {
        "status": "RUNNABLE" if now >= end else "NOT_YET_RUNNABLE",
        "window": window,
    }


def verify_and_advance(existing_records, tranche_root, expected_start_utc, expected_end_utc):
    """Verify one sealed tranche, then re-audit the complete prospective ledger."""
    _req(isinstance(existing_records, list), "existing record list required")
    record = verify_tranche(tranche_root, expected_start_utc, expected_end_utc)
    records = list(existing_records) + [record]
    state = audit_and_advance(records)
    return {
        "new_record": record,
        "records": records,
        "ledger_state": state,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
