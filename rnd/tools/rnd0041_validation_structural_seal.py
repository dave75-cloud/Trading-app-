#!/usr/bin/env python3
"""Outcome-blind structural seal for RND-0041 validation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from oanda_historical_quarantine import _json, verify_existing_shard  # noqa: E402
from rnd0041_validation_acquisition import (  # noqa: E402
    ACQUISITION_PATH,
    CALENDAR_PATH,
    END_UTC,
    SHARD,
    START_UTC,
    SYMBOLS,
    boundary_proof,
    require_acquisition_authority,
)


class RND0041SealError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0041SealError(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _forbid_outcome_fields(value, role="root"):
    forbidden = {
        "signal", "position", "trade", "trades", "return", "returns", "pnl",
        "equity", "drawdown", "sharpe", "win_rate", "hit_rate", "strategy_score",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            _require(str(key).lower() not in forbidden, f"{role}: outcome field prohibited: {key}")
            _forbid_outcome_fields(child, f"{role}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _forbid_outcome_fields(child, f"{role}[{i}]")


def seal(evidence_root):
    require_acquisition_authority()
    evidence_root = Path(evidence_root).expanduser().resolve()
    summary_path = evidence_root / "rnd0041-validation-acquisition-summary.json"
    _require(summary_path.is_file(), "acquisition summary missing")
    summary = _json(summary_path)
    _forbid_outcome_fields(summary, "acquisition_summary")

    _require(summary.get("task_id") == "RND-0041", "summary task changed")
    _require(summary.get("authorized_interval") == {
        "start_inclusive_utc": START_UTC,
        "end_exclusive_utc": END_UTC,
    }, "summary interval changed")
    _require(summary.get("symbols") == list(SYMBOLS), "summary symbol universe changed")
    _require(summary.get("completed_symbols") == list(SYMBOLS), "summary not complete 4/4")
    _require(summary.get("verified_skipped_symbols") == [], "unexpected skipped symbols in initial acquisition")
    for key in (
        "strategy_evaluation", "candidate_evaluation", "reserved_final_open",
        "broker_writes", "capital_authority", "strategy_selection",
    ):
        _require(summary.get(key) is False, f"prohibited authority opened in summary: {key}")

    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    sealed = {}
    for symbol in SYMBOLS:
        shard_root = evidence_root / symbol / "validation"
        _require(
            verify_existing_shard(shard_root, symbol, SHARD, acquisition, calendar),
            f"{symbol}: validation shard identity verification failed",
        )
        proof = boundary_proof(shard_root, symbol)
        _require(proof["rows_at_or_after_reserved_final_boundary"] == 0, f"{symbol}: reserved-final boundary breach")
        manifest = _json(shard_root / "quarantine_manifest.json")
        _forbid_outcome_fields(manifest, f"{symbol}.manifest")
        sealed[symbol] = {
            "row_count": manifest.get("row_count"),
            "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
            "aggregate_raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
            "missing_count": manifest.get("missing_count"),
            "unexpected_count": manifest.get("unexpected_count"),
            "quarantine_status": manifest.get("status"),
            "boundary_proof": proof,
        }

    return {
        "contract_version": "RND0041-validation-structural-seal-v1",
        "task_id": "RND-0041",
        "status": "STRUCTURALLY_SEALED_REQUIRES_HUMAN_REVIEW",
        "authorized_interval": {
            "start_inclusive_utc": START_UTC,
            "end_exclusive_utc": END_UTC,
        },
        "symbols": list(SYMBOLS),
        "verified_symbols": "4/4",
        "acquisition_summary_sha256": _sha256_file(summary_path),
        "sealed_evidence": sealed,
        "strategy_evaluation": False,
        "candidate_evaluation": False,
        "parameter_search": False,
        "strategy_selection": False,
        "reserved_final_open": False,
        "portfolio_sizing": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
        "human_review_required": True,
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0041SealError("seal report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-root", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args(argv)
    value = seal(a.evidence_root)
    out = _write_new(a.report, value)
    print("RND0041_VALIDATION_STRUCTURAL_SEAL: COMPLETE")
    print("verified_symbols=4/4")
    print("strategy_evaluation=FALSE")
    print("candidate_evaluation=FALSE")
    print("reserved_final_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={out}")
    print(f"report_sha256={_sha256_file(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
