#!/usr/bin/env python3
"""Boundary-aware, outcome-blind validation evidence acquisition for RND-0041."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from oanda_historical_acquisition import _utc  # noqa: E402
from oanda_historical_quarantine import (  # noqa: E402
    _json,
    _write_json,
    acquire_shard,
    verify_existing_shard,
)

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
START_UTC = "2020-12-31T19:15:00Z"
END_UTC = "2023-01-01T09:40:00Z"
SHARD = {"year": "validation-2021-2022", "start_utc": START_UTC, "end_utc": END_UTC}
DECLARATION_PATH = ROOT / "rnd" / "research" / "RND0041_VALIDATION_EVIDENCE_ACQUISITION_DECLARATION.json"
AUTHORIZATION_PATH = ROOT / "rnd" / "research" / "RND0041_VALIDATION_ACQUISITION_AUTHORIZATION.json"
ACQUISITION_PATH = ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"
CALENDAR_PATH = ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json"


class RND0041AcquisitionError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0041AcquisitionError(message)


def load_declaration(path=DECLARATION_PATH):
    value = _json(path)
    _require(value.get("task_id") == "RND-0041", "declaration task changed")
    _require(value.get("scope") == "VALIDATION_EVIDENCE_ACQUISITION_AND_STRUCTURAL_SEAL_ONLY", "scope changed")
    _require(value.get("authorized_interval") == {
        "start_inclusive_utc": START_UTC,
        "end_exclusive_utc": END_UTC,
    }, "validation interval changed")
    _require(value.get("symbols") == list(SYMBOLS), "symbol universe changed")
    _require(value.get("granularity") == "M5", "granularity changed")
    _require(value.get("provider") == "OANDA", "provider changed")
    _require(value.get("environment") == "PRACTICE", "environment changed")
    for key in (
        "strategy_outcomes", "candidate_evaluation", "parameter_search",
        "strategy_selection", "reserved_final_open", "portfolio_sizing",
        "broker_writes", "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        _require(value.get(key) is False, f"prohibited authority opened: {key}")
    _require(value.get("human_review_required") is True, "human review requirement removed")
    _require(value.get("status") == "PREDECLARED_NOT_AUTHORIZED_TO_ACQUIRE", "predeclaration state changed")
    _require(value.get("acquisition_authorized") is False, "predeclaration acquisition gate changed")
    return value


def load_authorization(path=AUTHORIZATION_PATH):
    value = _json(path)
    _require(value.get("task_id") == "RND-0041", "authorization task changed")
    _require(value.get("status") == "ACTIVE", "RND-0041 acquisition authorization inactive")
    _require(value.get("scope") == "VALIDATION_EVIDENCE_ACQUISITION_ONLY", "authorization scope changed")
    _require(value.get("authorized_interval") == {
        "start_inclusive_utc": START_UTC,
        "end_exclusive_utc": END_UTC,
    }, "authorization interval changed")
    _require(value.get("symbols") == list(SYMBOLS), "authorization symbols changed")
    _require(value.get("acquisition_authorized") is True, "acquisition not authorized")
    for key in (
        "strategy_outcomes", "candidate_evaluation", "parameter_search",
        "strategy_selection", "reserved_final_open", "portfolio_sizing",
        "broker_writes", "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        _require(value.get(key) is False, f"prohibited authority opened: {key}")
    _require(value.get("human_review_required") is True, "human review requirement removed")
    return value


def require_acquisition_authority():
    declaration = load_declaration()
    authorization = load_authorization()
    _require(
        authorization.get("authorized_interval") == declaration.get("authorized_interval"),
        "authorization/declaration interval mismatch",
    )
    _require(authorization.get("symbols") == declaration.get("symbols"), "authorization/declaration symbol mismatch")
    return declaration, authorization


def boundary_proof(path, symbol):
    rows = _json(Path(path) / "canonical_rows.json")
    _require(isinstance(rows, list) and rows, f"{symbol}: canonical rows missing")
    start = _utc(START_UTC, "validation.start_utc")
    end = _utc(END_UTC, "validation.end_utc")
    previous = None
    first = last = None
    for row in rows:
        ts = row.get("timestamp_utc") if isinstance(row, dict) else None
        _require(isinstance(ts, str), f"{symbol}: malformed timestamp")
        instant = _utc(ts, f"{symbol}.timestamp_utc")
        _require(start <= instant < end, f"{symbol}: row outside validation interval")
        if previous is not None:
            _require(instant > previous, f"{symbol}: timestamps not strictly increasing")
        if first is None:
            first = ts
        last = ts
        previous = instant
    return {
        "authorized_start_inclusive_utc": START_UTC,
        "authorized_end_exclusive_utc": END_UTC,
        "first_canonical_timestamp_utc": first,
        "last_canonical_timestamp_utc": last,
        "canonical_row_count": len(rows),
        "rows_at_or_after_reserved_final_boundary": 0,
        "boundary_status": "PASS",
    }


def acquire(output, resume=False, delay=0.6):
    require_acquisition_authority()
    _require(0.5 <= delay <= 5.0, "request delay must be between 0.5 and 5.0 seconds")

    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    _require(bool(token and account_id), "required OANDA Practice runtime credentials are absent")

    output = Path(output).expanduser().resolve()
    _require(output != ROOT and ROOT not in output.parents, "output must remain outside repository")
    if output.exists() and not resume:
        raise RND0041AcquisitionError("output exists; use a new target or verified --resume")
    output.mkdir(parents=True, exist_ok=True)

    completed, skipped, evidence = [], [], {}
    for symbol in SYMBOLS:
        final = output / symbol / "validation"
        if final.exists():
            if resume and verify_existing_shard(final, symbol, SHARD, acquisition, calendar):
                proof = boundary_proof(final, symbol)
                skipped.append(symbol)
                evidence[symbol] = {
                    "manifest": _json(final / "quarantine_manifest.json"),
                    "boundary_proof": proof,
                }
                continue
            raise RND0041AcquisitionError(f"{symbol}: existing validation shard failed verification or resume not authorized")

        final.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".validation-stage-", dir=str(final.parent)))
        try:
            manifest = acquire_shard(
                acquisition, calendar, symbol, SHARD, token, account_id, stage, delay
            )
            proof = boundary_proof(stage, symbol)
            stage.rename(final)
            completed.append(symbol)
            evidence[symbol] = {"manifest": manifest, "boundary_proof": proof}
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise

    value = {
        "contract_version": "RND0041-validation-acquisition-v1",
        "task_id": "RND-0041",
        "authorized_interval": {"start_inclusive_utc": START_UTC, "end_exclusive_utc": END_UTC},
        "symbols": list(SYMBOLS),
        "completed_symbols": completed,
        "verified_skipped_symbols": skipped,
        "evidence": evidence,
        "strategy_evaluation": False,
        "candidate_evaluation": False,
        "reserved_final_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "strategy_selection": False,
        "status": "ACQUIRED_QUARANTINED_REQUIRES_STRUCTURAL_REVIEW",
    }
    summary = output / "rnd0041-validation-acquisition-summary.json"
    if summary.exists():
        raise RND0041AcquisitionError("summary exists; overwrite prohibited")
    _write_json(summary, value)
    return value, summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--request-delay-seconds", type=float, default=0.6)
    args = parser.parse_args(argv)
    value, summary = acquire(args.output, args.resume, args.request_delay_seconds)
    print("RND0041_VALIDATION_ACQUISITION: COMPLETE")
    print(f"completed_symbols={len(value['completed_symbols'])}")
    print(f"verified_skipped_symbols={len(value['verified_skipped_symbols'])}")
    print("strategy_evaluation=FALSE")
    print("candidate_evaluation=FALSE")
    print("reserved_final_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"summary={summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
