#!/usr/bin/env python3
"""Explicit human seal for RND-0036 2020 development evidence.

This tool seals structural evidence only after human confirmation. It does not
open strategy evaluation, validation/final data, broker writes, sizing, capital,
promotion or merge authority. The empirical 17:00 New York candidate remains
non-authoritative and canonical evidence remains unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rnd0036_seal_review import review as seal_review
from rnd0036_calendar_classification_review import review as calendar_review
from rnd0036_2020_development_acquisition import SYMBOLS, START_UTC, END_UTC

SEAL_REVIEW_SHA256 = "4906b75bbb034b27d885f773a547be3ba1e970fe0377278081e9ec7bf0d28055"
CLASSIFICATION_SHA256 = "d6a8f49f36b8e6d577ca7aa862ea626509f20c61e03455df5cb433b8963a8265"
CONFIRMATION = "I_AUTHORIZE_RND0036_EVIDENCE_SEAL"


class RND0036HumanSealError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0036HumanSealError(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0036HumanSealError("seal record exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def seal(root, seal_review_report, classification_report, confirmation):
    _require(confirmation == CONFIRMATION, "explicit human seal confirmation required")
    root = Path(root).expanduser().resolve()
    seal_review_report = Path(seal_review_report).expanduser().resolve()
    classification_report = Path(classification_report).expanduser().resolve()
    _require(_sha256_file(seal_review_report) == SEAL_REVIEW_SHA256, "seal-review report SHA mismatch")
    _require(_sha256_file(classification_report) == CLASSIFICATION_SHA256, "classification report SHA mismatch")

    s = seal_review(root)
    c = calendar_review(root)
    _require(s["verified_shards"] == 4 and s["boundary_pass"] is True, "identity/boundary review failed")
    _require(set(s["unresolved_symbols"]) == set(SYMBOLS), "unexpected authoritative-ledger state")
    _require(c["all_candidate_unexpected_zero"] is True, "candidate leaves unexpected timestamps")
    _require(c["shared_remaining_unexpected_timestamps"] == [], "shared residual unexpected timestamps remain")
    for symbol in SYMBOLS:
        item = c["per_symbol"][symbol]
        _require(item["candidate_unexpected_count"] == 0, f"{symbol}: residual unexpected timestamps remain")
        _require(item["boundary_status"] == "PASS", f"{symbol}: boundary not PASS")

    value = {
        "contract_version": "RND0036-development-evidence-seal-v1",
        "task_id": "RND-0036",
        "status": "SEALED_DEVELOPMENT_EVIDENCE_REQUIRES_SEPARATE_STRATEGY_AUTHORIZATION",
        "authorized_interval": {
            "start_inclusive_utc": START_UTC,
            "end_exclusive_utc": END_UTC,
        },
        "symbols": list(SYMBOLS),
        "verified_shards": 4,
        "boundary_pass": True,
        "authoritative_standard_schedule_ledgers_resolved": False,
        "seal_basis": (
            "Immutable canonical evidence is identity-verified and development-boundary-safe; "
            "all baseline unexpected candles are explained by the empirical historical 17:00 New York "
            "candidate across all four pairs; missing observations remain explicit and gap-aware."
        ),
        "candidate_1700_authority": "NONE",
        "documentary_calendar_authority": False,
        "calendar_modified": False,
        "canonical_evidence_modified": False,
        "synthetic_candles_allowed": False,
        "gap_aware_downstream_processing_required": True,
        "per_symbol": {
            symbol: {
                "row_count": s["per_symbol"][symbol]["row_count"],
                "raw_bundle_sha256": s["per_symbol"][symbol]["raw_bundle_sha256"],
                "canonical_rows_sha256": s["per_symbol"][symbol]["canonical_rows_sha256"],
                "standard_schedule_sha256": s["per_symbol"][symbol]["standard_schedule_sha256"],
                "baseline_missing_count": c["per_symbol"][symbol]["baseline_missing_count"],
                "baseline_unexpected_count": c["per_symbol"][symbol]["baseline_unexpected_count"],
                "candidate_unexpected_count": c["per_symbol"][symbol]["candidate_unexpected_count"],
                "residual_short_gap_bars": c["per_symbol"][symbol]["residual_short_gap_bars"],
                "closure_shaped_candidate_bars": c["per_symbol"][symbol]["closure_shaped_candidate_bars"],
                "unclassified_gap_bars": c["per_symbol"][symbol]["unclassified_gap_bars"],
                "boundary_proof": s["per_symbol"][symbol]["boundary_proof"],
            }
            for symbol in SYMBOLS
        },
        "source_receipts": {
            "seal_review_sha256": SEAL_REVIEW_SHA256,
            "calendar_classification_sha256": CLASSIFICATION_SHA256,
        },
        "authority": {
            "strategy_evaluation": False,
            "validation_open": False,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_seal_confirmed": True,
            "human_review_required_for_next_stage": True,
        },
    }
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--seal-review-report", required=True)
    parser.add_argument("--classification-report", required=True)
    parser.add_argument("--human-seal-confirmation", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    value = seal(
        args.root,
        args.seal_review_report,
        args.classification_report,
        args.human_seal_confirmation,
    )
    output = _write_new(args.report, value)
    print("RND0036_HUMAN_SEAL: COMPLETE")
    print("verified_shards=4/4")
    print("boundary_pass=TRUE")
    print("candidate_1700_authority=NONE")
    print("authoritative_standard_schedule_ledgers_resolved=FALSE")
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
