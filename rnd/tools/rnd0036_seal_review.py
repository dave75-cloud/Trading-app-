#!/usr/bin/env python3
"""Outcome-blind seal review for RND-0036 2020 development evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rnd0036_2020_development_acquisition import (
    SYMBOLS,
    START_UTC,
    END_UTC,
    SHARD,
    ACQUISITION_PATH,
    CALENDAR_PATH,
    boundary_proof,
)
from oanda_historical_quarantine import _json, verify_existing_shard


class RND0036SealReviewError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0036SealReviewError(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def review(root):
    root = Path(root).expanduser().resolve()
    summary = _json(root / "rnd0036-acquisition-summary.json")
    _require(summary.get("task_id") == "RND-0036", "summary task mismatch")
    _require(summary.get("authorized_interval") == {
        "start_inclusive_utc": START_UTC,
        "end_exclusive_utc": END_UTC,
    }, "summary interval mismatch")
    _require(summary.get("symbols") == list(SYMBOLS), "summary symbol universe mismatch")
    _require(summary.get("strategy_evaluation") is False, "strategy evaluation unexpectedly open")
    for key in ("validation_open", "final_test_open", "broker_writes", "capital_authority", "strategy_selection"):
        _require(summary.get(key) is False, f"prohibited authority opened: {key}")

    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    per_symbol = {}
    unresolved_symbols = []

    for symbol in SYMBOLS:
        shard_root = root / symbol / "2020-development"
        _require(
            verify_existing_shard(shard_root, symbol, SHARD, acquisition, calendar),
            f"{symbol}: shard identity verification failed",
        )
        manifest = _json(shard_root / "quarantine_manifest.json")
        proof = boundary_proof(shard_root, symbol)
        discrepancy = _json(shard_root / "discrepancy_ledger.json")
        _require(proof["rows_at_or_after_validation_boundary"] == 0, f"{symbol}: validation boundary breach")
        _require(manifest.get("row_count") == proof["canonical_row_count"], f"{symbol}: row count mismatch")
        unresolved = not bool(discrepancy.get("resolved"))
        if unresolved:
            unresolved_symbols.append(symbol)
        per_symbol[symbol] = {
            "status": manifest.get("status"),
            "row_count": manifest.get("row_count"),
            "raw_page_count": manifest.get("raw_page_count"),
            "raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
            "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
            "standard_schedule_sha256": manifest.get("standard_schedule_sha256"),
            "missing_count": manifest.get("missing_count"),
            "unexpected_count": manifest.get("unexpected_count"),
            "discrepancy_resolved": not unresolved,
            "boundary_proof": proof,
        }

    status = "PASS_READY_FOR_HUMAN_SEAL" if not unresolved_symbols else "HOLD_UNRESOLVED_QUARANTINE_DISCREPANCIES"
    return {
        "contract_version": "RND0036-seal-review-v1",
        "task_id": "RND-0036",
        "authorized_interval": {
            "start_inclusive_utc": START_UTC,
            "end_exclusive_utc": END_UTC,
        },
        "symbols": list(SYMBOLS),
        "verified_shards": 4,
        "boundary_pass": True,
        "unresolved_symbols": unresolved_symbols,
        "per_symbol": per_symbol,
        "strategy_evaluation": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "strategy_selection": False,
        "status": status,
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0036SealReviewError("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    value = review(args.root)
    output = _write_new(args.report, value)
    print("RND0036_SEAL_REVIEW:", value["status"])
    print("verified_shards=4/4")
    print("boundary_pass=TRUE")
    print(f"unresolved_symbols={len(value['unresolved_symbols'])}")
    print("strategy_evaluation=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print("strategy_selection=FALSE")
    print(f"report={output}")
    print(f"report_sha256={_sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
