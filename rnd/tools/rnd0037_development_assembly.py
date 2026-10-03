#!/usr/bin/env python3
"""Governed structural assembly of the complete 2015-2020 development evidence.

No strategy evaluation or outcome generation is permitted.
"""

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

from rnd0035_development_runner import PLAN_PATH, _verify_evidence  # noqa: E402
from rnd0035_trial_plan import load_plan  # noqa: E402
from rnd0036_2020_development_acquisition import (  # noqa: E402
    SYMBOLS,
    START_UTC as START_2020,
    END_UTC as DEVELOPMENT_END,
    SHARD,
    ACQUISITION_PATH,
    CALENDAR_PATH,
    boundary_proof,
)
from oanda_historical_quarantine import _json, verify_existing_shard  # noqa: E402

DEVELOPMENT_START = "2015-01-01T00:00:00Z"
SEAL_RECEIPT = ROOT / "rnd" / "research" / "RND0036_HUMAN_SEAL_RECEIPT.json"


class RND0037AssemblyError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0037AssemblyError(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def assemble(audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root,
             development_2020_root, rnd0036_seal_report):
    plan = load_plan(PLAN_PATH)
    _require(plan.get("validation_open") is False, "validation unexpectedly open")
    _require(plan.get("final_test_open") is False, "final test unexpectedly open")

    identities, verified, _ = _verify_evidence(
        plan,
        audusd_2015_shard,
        cross_pair_2015_root,
        development_2016_2019_root,
        load_rows=False,
    )
    _require(verified == 20, "2015-2019 evidence identity verification not 20/20")

    receipt = _json(SEAL_RECEIPT)
    _require(receipt.get("task_id") == "RND-0036", "RND-0036 seal receipt task mismatch")
    _require(receipt.get("status") == "HUMAN_EVIDENCE_SEAL_COMPLETE", "RND-0036 human seal incomplete")
    _require(receipt.get("boundary_pass") is True, "RND-0036 boundary did not pass")
    for key in ("strategy_evaluation", "validation_open", "final_test_open", "broker_writes", "capital_authority", "strategy_selection"):
        _require(receipt.get(key) is False, f"RND-0036 prohibited authority opened: {key}")

    seal_report = Path(rnd0036_seal_report).expanduser().resolve()
    _require(seal_report.is_file(), "RND-0036 seal report missing")
    _require(_sha256_file(seal_report) == receipt.get("report_sha256"), "RND-0036 seal report SHA mismatch")

    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    root2020 = Path(development_2020_root).expanduser().resolve()
    evidence_2020 = {}
    for symbol in SYMBOLS:
        shard_root = root2020 / symbol / "2020-development"
        _require(
            verify_existing_shard(shard_root, symbol, SHARD, acquisition, calendar),
            f"{symbol}: 2020 shard identity verification failed",
        )
        proof = boundary_proof(shard_root, symbol)
        _require(proof["rows_at_or_after_validation_boundary"] == 0, f"{symbol}: validation boundary breach")
        manifest = _json(shard_root / "quarantine_manifest.json")
        evidence_2020[symbol] = {
            "row_count": manifest.get("row_count"),
            "raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
            "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
            "standard_schedule_sha256": manifest.get("standard_schedule_sha256"),
            "boundary_proof": proof,
        }

    return {
        "contract_version": "RND0037-development-assembly-v1",
        "task_id": "RND-0037",
        "development_interval": {
            "start_inclusive_utc": DEVELOPMENT_START,
            "end_exclusive_utc": DEVELOPMENT_END,
        },
        "symbols": list(SYMBOLS),
        "pair_year_count": 24,
        "evidence_2015_2019": {
            "verified_pair_years": 20,
            "identity_records": identities,
        },
        "evidence_2020": {
            "verified_pair_years": 4,
            "segment_start_utc": START_2020,
            "segment_end_exclusive_utc": DEVELOPMENT_END,
            "human_seal_report_sha256": receipt["report_sha256"],
            "per_symbol": evidence_2020,
        },
        "full_development_structural_evidence_complete": True,
        "strategy_evaluation": False,
        "validation_open": False,
        "final_test_open": False,
        "strategy_selection": False,
        "portfolio_sizing": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
        "status": "PASS_COMPLETE_DEVELOPMENT_EVIDENCE_REQUIRES_HUMAN_REVIEW",
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0037AssemblyError("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument("--development-2016-2019-root", required=True)
    parser.add_argument("--development-2020-root", required=True)
    parser.add_argument("--rnd0036-seal-report", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    value = assemble(
        args.audusd_2015_shard,
        args.cross_pair_2015_root,
        args.development_2016_2019_root,
        args.development_2020_root,
        args.rnd0036_seal_report,
    )
    output = _write_new(args.report, value)
    print("RND0037_DEVELOPMENT_ASSEMBLY: COMPLETE")
    print("verified_2015_2019=20/20")
    print("verified_2020=4/4")
    print("pair_years=24/24")
    print("full_development_structural_evidence_complete=TRUE")
    print("strategy_evaluation=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={output}")
    print(f"report_sha256={_sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
