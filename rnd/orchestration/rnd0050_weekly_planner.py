#!/usr/bin/env python3
"""Pure planner for RND-0050 weekly prospective acquisition.

No network access, file IO, strategy evaluation, broker writes, or market-data
access. It derives only the next structurally admissible tranche window.
"""
from datetime import datetime, timedelta, timezone

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
ACCUMULATION_END = "2027-04-03T07:25:00Z"
WEEK = timedelta(days=7)


class RND0050PlannerError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0050PlannerError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    dt = datetime.fromisoformat(value[:-1] + "+00:00")
    _req(int(dt.timestamp()) % 300 == 0, "M5 boundary required")
    return dt.astimezone(timezone.utc)


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_next(ledger, now_utc):
    _req(isinstance(ledger, dict), "ledger mapping required")
    _req(ledger.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(ledger.get("strategy_evaluation") is False, "strategy evaluation prohibited")
    _req(ledger.get("reserved_final_access") is False, "reserved-final access prohibited")
    _req(ledger.get("broker_writes") is False, "broker writes prohibited")
    _req(ledger.get("capital_authority") is False, "capital authority prohibited")
    _req(ledger.get("automatic_promotion") is False, "automatic promotion prohibited")

    previous_end = _utc(ledger.get("verified_end_utc"))
    boundary = _utc(ACCUMULATION_END)
    now = _utc(now_utc)
    tranche_number = ledger.get("next_tranche_number")
    _req(isinstance(tranche_number, int) and tranche_number >= 2, "valid next tranche number required")

    if previous_end >= boundary:
        return {"status": "ACCUMULATION_COMPLETE", "window": None}

    end = min(previous_end + WEEK, boundary)
    window = {"start_utc": _z(previous_end), "end_utc": _z(end)}
    if now < end:
        return {
            "status": "NOT_YET_RUNNABLE",
            "tranche_number": tranche_number,
            "window": window,
        }
    return {
        "status": "RUNNABLE",
        "tranche_number": tranche_number,
        "window": window,
    }
