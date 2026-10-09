"""Pure operational-integrity primitives for RND-0060S.

No economic outcomes are accepted or exposed here. The module manages only
prospective tranche identity, chronology, provenance, counts, gaps/recovery, and
readout-lock state for the RND-0060R confirmation stream.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

STREAM_ID = "RND0060R_ACTIVITY_POLICY_CONFIRMATION"
SEALED_START_UTC = "2026-10-09T02:33:50Z"
MIN_CALENDAR_DAYS = 180
MIN_ELIGIBLE_NON_DEFER = 100
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RND0060SIntegrityError(ValueError):
    pass


def _req(ok: bool, message: str) -> None:
    if not ok:
        raise RND0060SIntegrityError(message)


def _utc(value: Any, name: str) -> datetime:
    _req(isinstance(value, str) and value.endswith("Z"), f"{name}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060SIntegrityError(f"{name}: invalid UTC timestamp") from exc
    return dt


def _count(value: Any, name: str) -> int:
    _req(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{name}: non-negative integer required")
    return value


def _sha(value: Any, name: str) -> str:
    _req(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, f"{name}: lowercase sha256 required")
    return value


def validate_tranche(record: Mapping[str, Any]) -> dict[str, Any]:
    _req(isinstance(record, Mapping), "tranche: mapping required")
    required = {
        "tranche_id", "stream_id", "window_start_utc", "window_end_utc",
        "captured_at_utc", "source_sha256", "artifact_sha256",
        "eligible_non_defer_count", "defer_count", "status",
    }
    _req(required.issubset(record), "tranche: required fields missing")
    _req(record["stream_id"] == STREAM_ID, "tranche: wrong stream id")
    _req(isinstance(record["tranche_id"], str) and record["tranche_id"].strip(), "tranche_id required")
    start = _utc(record["window_start_utc"], "window_start_utc")
    end = _utc(record["window_end_utc"], "window_end_utc")
    captured = _utc(record["captured_at_utc"], "captured_at_utc")
    sealed = _utc(SEALED_START_UTC, "sealed_start")
    _req(start >= sealed, "pre-start/backfill interval prohibited")
    _req(end > start, "tranche window must be non-empty")
    _req(captured >= end, "capture time cannot precede window end")
    source_sha = _sha(record["source_sha256"], "source_sha256")
    artifact_sha = _sha(record["artifact_sha256"], "artifact_sha256")
    eligible = _count(record["eligible_non_defer_count"], "eligible_non_defer_count")
    defer = _count(record["defer_count"], "defer_count")
    _req(record["status"] in {"CAPTURED", "RECOVERED"}, "unsupported tranche status")
    return {
        "tranche_id": record["tranche_id"],
        "stream_id": STREAM_ID,
        "window_start_utc": record["window_start_utc"],
        "window_end_utc": record["window_end_utc"],
        "captured_at_utc": record["captured_at_utc"],
        "source_sha256": source_sha,
        "artifact_sha256": artifact_sha,
        "eligible_non_defer_count": eligible,
        "defer_count": defer,
        "status": record["status"],
        "recovered": record["status"] == "RECOVERED",
    }


def reconcile_ledger(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    validated = [validate_tranche(r) for r in records]
    _req(validated, "ledger must contain at least one tranche")

    ids: set[str] = set()
    artifacts: set[str] = set()
    gaps = []
    previous_end: datetime | None = None
    previous_id: str | None = None

    for rec in validated:
        _req(rec["tranche_id"] not in ids, "duplicate tranche id")
        _req(rec["artifact_sha256"] not in artifacts, "duplicate artifact sha256")
        ids.add(rec["tranche_id"])
        artifacts.add(rec["artifact_sha256"])

        start = _utc(rec["window_start_utc"], "window_start_utc")
        end = _utc(rec["window_end_utc"], "window_end_utc")
        if previous_end is not None:
            _req(start >= previous_end, "overlapping or out-of-order tranche window")
            if start > previous_end:
                gaps.append({
                    "status": "GAP_DETECTED",
                    "after_tranche_id": previous_id,
                    "gap_start_utc": previous_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "gap_end_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
        previous_end = end
        previous_id = rec["tranche_id"]

    return {
        "stream_id": STREAM_ID,
        "tranche_count": len(validated),
        "eligible_non_defer_count": sum(r["eligible_non_defer_count"] for r in validated),
        "defer_count": sum(r["defer_count"] for r in validated),
        "recovered_tranche_count": sum(1 for r in validated if r["recovered"]),
        "gap_count": len(gaps),
        "gaps": gaps,
        "first_window_start_utc": validated[0]["window_start_utc"],
        "last_window_end_utc": validated[-1]["window_end_utc"],
        "ledger_integrity_pass": True,
    }


def operational_status(records: Iterable[Mapping[str, Any]], as_of_utc: str) -> dict[str, Any]:
    ledger = reconcile_ledger(records)
    as_of = _utc(as_of_utc, "as_of_utc")
    sealed = _utc(SEALED_START_UTC, "sealed_start")
    _req(as_of >= sealed, "as_of cannot precede sealed start")
    elapsed_seconds = (as_of - sealed).total_seconds()
    elapsed_days = elapsed_seconds / 86400.0
    time_met = elapsed_seconds >= MIN_CALENDAR_DAYS * 86400
    count_met = ledger["eligible_non_defer_count"] >= MIN_ELIGIBLE_NON_DEFER
    readout_state = "READOUT_ELIGIBLE_PENDING_HUMAN_GATE" if (time_met and count_met) else "READOUT_LOCKED"
    return {
        "contract_version": "RND0060S-operations-integrity-v1",
        "stream_id": STREAM_ID,
        "sealed_start_utc": SEALED_START_UTC,
        "as_of_utc": as_of_utc,
        "elapsed_calendar_days": elapsed_days,
        "minimum_calendar_days": MIN_CALENDAR_DAYS,
        "minimum_eligible_non_defer": MIN_ELIGIBLE_NON_DEFER,
        "tranche_count": ledger["tranche_count"],
        "eligible_non_defer_count": ledger["eligible_non_defer_count"],
        "defer_count": ledger["defer_count"],
        "recovered_tranche_count": ledger["recovered_tranche_count"],
        "gap_count": ledger["gap_count"],
        "time_requirement_met": time_met,
        "count_requirement_met": count_met,
        "readout_state": readout_state,
        "economic_outcomes_exposed": False,
        "q003_prospective_outcomes_open": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
