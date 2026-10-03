#!/usr/bin/env python3
"""Boundary-aware acquisition wrapper for RND-0036.

Acquires structural OANDA PRACTICE M5 evidence for the remaining RND-0029
DEVELOPMENT interval only. No strategy evaluation, validation/final access,
orders, sizing, capital, promotion or merge authority.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from oanda_historical_quarantine import (  # noqa: E402
    _json,
    _write_json,
    acquire_shard,
    verify_existing_shard,
)

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
START_UTC = "2020-01-01T00:00:00Z"
END_UTC = "2020-12-31T19:15:00Z"
SHARD = {"year": 2020, "start_utc": START_UTC, "end_utc": END_UTC}
AUTH_PATH = ROOT / "rnd" / "research" / "RND0036_ACQUISITION_AUTHORIZATION.json"
ACQUISITION_PATH = ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"
CALENDAR_PATH = ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json"


class RND0036AcquisitionError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0036AcquisitionError(message)


def load_authorization(path=AUTH_PATH):
    value = _json(path)
    _require(value.get("task_id") == "RND-0036", "authorization task changed")
    _require(value.get("status") == "ACTIVE", "RND-0036 acquisition not active")
    _require(value.get("scope") == "2020_DEVELOPMENT_ACQUISITION_AND_SEAL_ONLY", "scope changed")
    _require(value.get("authorized_interval") == {
        "start_inclusive_utc": START_UTC,
        "end_exclusive_utc": END_UTC,
    }, "authorized interval changed")
    _require(value.get("symbols") == list(SYMBOLS), "symbol universe changed")
    _require(value.get("granularity") == "M5", "granularity changed")
    _require(value.get("provider") == "OANDA", "provider changed")
    _require(value.get("environment") == "PRACTICE", "environment changed")
    for key in (
        "strategy_outcomes", "validation_open", "final_test_open", "strategy_selection",
        "portfolio_sizing", "broker_writes", "capital_authority",
        "automatic_promotion", "automatic_merge",
    ):
        _require(value.get(key) is False, f"prohibited authority opened: {key}")
    _require(value.get("human_review_required") is True, "human review requirement removed")
    return value


def boundary_proof(path, symbol):
    root = Path(path)
    rows = _json(root / "canonical_rows.json")
    _require(isinstance(rows, list) and rows, f"{symbol}: canonical rows missing")
    timestamps = []
    previous = None
    for row in rows:
        _require(isinstance(row, dict) and isinstance(row.get("timestamp_utc"), str), f"{symbol}: malformed row")
        ts = row["timestamp_utc"]
        _require(START_UTC <= ts < END_UTC, f"{symbol}: row outside authorized development interval")
        if previous is not None:
            _require(ts > previous, f"{symbol}: canonical timestamps not strictly increasing")
        previous = ts
        timestamps.append(ts)
    return {
        "authorized_start_inclusive_utc": START_UTC,
        "authorized_end_exclusive_utc": END_UTC,
        "first_canonical_timestamp_utc": timestamps[0],
        "last_canonical_timestamp_utc": timestamps[-1],
        "canonical_row_count": len(timestamps),
        "rows_at_or_after_validation_boundary": 0,
        "boundary_status": "PASS",
    }


def acquire(output, resume=False, delay=0.6):
    load_authorization()
    if delay < 0.5 or delay > 5.0:
        raise RND0036AcquisitionError("request delay must be between 0.5 and 5.0 seconds")

    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    _require(bool(token and account_id), "required OANDA Practice runtime credentials are absent")

    output = Path(output).expanduser().resolve()
    _require(output != ROOT and ROOT not in output.parents, "output must remain outside repository")
    if output.exists() and not resume:
        raise RND0036AcquisitionError("output exists; use a new target or verified --resume")
    output.mkdir(parents=True, exist_ok=True)

    completed = []
    skipped = []
    evidence = {}
    for symbol in SYMBOLS:
        final = output / symbol / "2020-development"
        if final.exists():
            if resume and verify_existing_shard(final, symbol, SHARD, acquisition, calendar):
                proof = boundary_proof(final, symbol)
                skipped.append(symbol)
                manifest = _json(final / "quarantine_manifest.json")
                evidence[symbol] = {"manifest": manifest, "boundary_proof": proof}
                continue
            raise RND0036AcquisitionError(f"{symbol}: existing shard failed verification or resume not authorized")

        final.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".2020-development-stage-", dir=str(final.parent)))
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
        "contract_version": "RND0036-2020-development-acquisition-v1",
        "task_id": "RND-0036",
        "authorized_interval": {"start_inclusive_utc": START_UTC, "end_exclusive_utc": END_UTC},
        "symbols": list(SYMBOLS),
        "completed_symbols": completed,
        "verified_skipped_symbols": skipped,
        "evidence": evidence,
        "four_symbol_common_coverage_required": True,
        "strategy_evaluation": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "strategy_selection": False,
        "status": "ACQUIRED_QUARANTINED_REQUIRES_SEAL_REVIEW",
    }
    summary = output / "rnd0036-acquisition-summary.json"
    if summary.exists() and not resume:
        raise RND0036AcquisitionError("summary exists; overwrite prohibited")
    _write_json(summary, value)
    return value, summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--request-delay-seconds", type=float, default=0.6)
    args = parser.parse_args(argv)
    value, summary = acquire(args.output, args.resume, args.request_delay_seconds)
    print("RND0036_2020_DEVELOPMENT_ACQUISITION: COMPLETE")
    print(f"completed_symbols={len(value['completed_symbols'])}")
    print(f"verified_skipped_symbols={len(value['verified_skipped_symbols'])}")
    print("strategy_evaluation=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"summary={summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
