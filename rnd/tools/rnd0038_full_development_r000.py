#!/usr/bin/env python3
"""Governed RND-0038 full-development R000 reference completion.

Runs only the already-frozen R000 configuration across governed 2015-2020
DEVELOPMENT evidence. No parameter search, higher-volatility follow-up,
validation/final access, broker writes, capital, sizing, promotion or merge
authority is granted.
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
    END_UTC as DEVELOPMENT_END,
    SHARD,
    ACQUISITION_PATH,
    CALENDAR_PATH,
    boundary_proof,
)
from rnd0038_reference_diagnostics_adapter import analyze_reference_results_2015_2020  # noqa: E402
from rnd0038_r000_kernel_adapter import reconstruct_pair_2015_2020  # noqa: E402
from oanda_historical_quarantine import _json, verify_existing_shard  # noqa: E402

AUTH_PATH = ROOT / "rnd" / "research" / "RND0038_R000_OUTCOME_AUTHORIZATION.json"
ASSEMBLY_RECEIPT_PATH = ROOT / "rnd" / "research" / "RND0037_DEVELOPMENT_ASSEMBLY_RECEIPT.json"
DEVELOPMENT_START = "2015-01-01T00:00:00Z"


class RND0038Error(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0038Error(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_authorization(path=AUTH_PATH):
    value = _json(path)
    _require(value.get("task_id") == "RND-0038", "authorization task changed")
    _require(value.get("status") == "ACTIVE", "RND-0038 authorization inactive")
    _require(value.get("scope") == "R000_FULL_DEVELOPMENT_2015_2020_REFERENCE_ONLY", "authorization scope changed")
    _require(value.get("authorized_interval") == {
        "start_inclusive_utc": DEVELOPMENT_START,
        "end_exclusive_utc": DEVELOPMENT_END,
    }, "authorization interval changed")
    _require(value.get("symbols") == list(SYMBOLS), "authorization symbols changed")
    _require(value.get("reference_configuration") == "R000", "reference configuration changed")
    _require(value.get("r000_development_outcomes") is True, "R000 outcomes not authorized")
    for key in (
        "higher_volatility_outcomes", "parameter_search", "strategy_selection",
        "validation_open", "final_test_open", "portfolio_sizing", "broker_writes",
        "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        _require(value.get(key) is False, f"prohibited authority opened: {key}")
    _require(value.get("human_review_required") is True, "human review requirement removed")
    return value


def _validate_assembly_report(path):
    receipt = _json(ASSEMBLY_RECEIPT_PATH)
    _require(receipt.get("status") == "COMPLETE", "RND-0037 assembly receipt incomplete")
    _require(receipt.get("pair_years") == "24/24", "RND-0037 pair-year receipt incomplete")
    _require(receipt.get("full_development_structural_evidence_complete") is True, "RND-0037 structural evidence incomplete")
    for key in ("strategy_evaluation", "validation_open", "final_test_open", "broker_writes", "capital_authority"):
        _require(receipt.get(key) is False, f"RND-0037 prohibited authority opened: {key}")
    report = Path(path).expanduser().resolve()
    _require(report.is_file(), "RND-0037 assembly report missing")
    _require(_sha256_file(report) == receipt.get("external_report_sha256"), "RND-0037 assembly report SHA mismatch")
    return receipt


def _load_2020_rows(root):
    acquisition = _json(ACQUISITION_PATH)
    calendar = _json(CALENDAR_PATH)
    root = Path(root).expanduser().resolve()
    rows_by_symbol = {}
    identities = {}
    for symbol in SYMBOLS:
        shard_root = root / symbol / "2020-development"
        _require(
            verify_existing_shard(shard_root, symbol, SHARD, acquisition, calendar),
            f"{symbol}: 2020 shard identity verification failed",
        )
        proof = boundary_proof(shard_root, symbol)
        _require(proof["rows_at_or_after_validation_boundary"] == 0, f"{symbol}: validation boundary breach")
        rows = _json(shard_root / "canonical_rows.json")
        _require(isinstance(rows, list) and rows, f"{symbol}: 2020 canonical rows missing")
        manifest = _json(shard_root / "quarantine_manifest.json")
        rows_by_symbol[symbol] = rows
        identities[symbol] = {
            "row_count": len(rows),
            "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
            "raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
            "boundary_proof": proof,
        }
    return identities, rows_by_symbol


def _summary(trades):
    count = len(trades)
    net_sum = sum(float(t["net_return"]) for t in trades)
    gross_sum = sum(float(t["gross_return"]) for t in trades)
    positives = sum(1 for t in trades if float(t["net_return"]) > 0.0)
    return {
        "trades": count,
        "net_return_sum": net_sum,
        "gross_return_sum": gross_sum,
        "mean_net_return": net_sum / count if count else None,
        "positive_trade_fraction": positives / count if count else None,
    }


def _year2020_contribution(per_symbol):
    out = {}
    combined = []
    for symbol in SYMBOLS:
        trades = [
            trade for trade in per_symbol[symbol]["trades"]
            if str(trade.get("exit_timestamp", "")).startswith("2020-")
        ]
        out[symbol] = _summary(trades)
        combined.extend(trades)
    return {
        "per_symbol": out,
        "combined": _summary(combined),
        "classification": "DEVELOPMENT_2020_CONTRIBUTION_DIAGNOSTIC",
        "strategy_selection_authority": False,
    }


def run(audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root,
        development_2020_root, rnd0037_assembly_report):
    load_authorization()
    _validate_assembly_report(rnd0037_assembly_report)

    plan = load_plan(PLAN_PATH)
    _require(plan.get("outcomes_authorized") is False, "frozen RND-0035 numerical plan unexpectedly opened")
    _require(plan.get("validation_open") is False and plan.get("final_test_open") is False, "validation/final unexpectedly open")

    identities_2015_2019, verified, historical_rows = _verify_evidence(
        plan,
        audusd_2015_shard,
        cross_pair_2015_root,
        development_2016_2019_root,
        load_rows=True,
    )
    _require(verified == 20, "2015-2019 evidence verification not 20/20")

    identities_2020, rows_2020 = _load_2020_rows(development_2020_root)
    full_rows = {}
    for symbol in SYMBOLS:
        rows = list(historical_rows[symbol]) + list(rows_2020[symbol])
        timestamps = [row["timestamp_utc"] for row in rows]
        _require(timestamps == sorted(timestamps), f"{symbol}: full-development rows not chronological")
        _require(len(timestamps) == len(set(timestamps)), f"{symbol}: duplicate full-development timestamps")
        _require(timestamps[0] >= DEVELOPMENT_START, f"{symbol}: pre-development row detected")
        _require(timestamps[-1] < DEVELOPMENT_END, f"{symbol}: validation row detected")
        full_rows[symbol] = rows

    per_symbol = {
        symbol: reconstruct_pair_2015_2020(symbol, full_rows[symbol])
        for symbol in SYMBOLS
    }
    diagnostics = analyze_reference_results_2015_2020(per_symbol)
    contribution_2020 = _year2020_contribution(per_symbol)

    pair_results = {}
    for symbol in SYMBOLS:
        result = per_symbol[symbol]
        pair_results[symbol] = {
            "row_count": len(full_rows[symbol]),
            "completed_trade_count": result.get("completed_trade_count"),
            "net_hit_rate": result.get("net_hit_rate"),
            "completed_trade_gross_equity_index": result.get("completed_trade_gross_equity_index"),
            "completed_trade_net_equity_index": result.get("completed_trade_net_equity_index"),
            "completed_trade_net_max_drawdown": result.get("completed_trade_net_max_drawdown"),
            "total_execution_cost_drag": result.get("total_execution_cost_drag"),
        }

    return {
        "contract_version": "RND0038-full-development-r000-v1",
        "task_id": "RND-0038",
        "mode": "R000_FULL_DEVELOPMENT_REFERENCE_COMPLETION",
        "development_interval": {
            "start_inclusive_utc": DEVELOPMENT_START,
            "end_exclusive_utc": DEVELOPMENT_END,
        },
        "evidence_identity": {
            "verified_2015_2019": "20/20",
            "verified_2020": "4/4",
            "pair_years": "24/24",
            "identities_2015_2019": identities_2015_2019,
            "identities_2020": identities_2020,
        },
        "R000_pair_results": pair_results,
        "R000_diagnostics": diagnostics,
        "development_2020_contribution": contribution_2020,
        "higher_volatility_outcomes": False,
        "parameter_search": False,
        "strategy_selection": False,
        "validation_open": False,
        "final_test_open": False,
        "portfolio_sizing": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0038Error("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument("--development-2016-2019-root", required=True)
    parser.add_argument("--development-2020-root", required=True)
    parser.add_argument("--rnd0037-assembly-report", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    value = run(
        args.audusd_2015_shard,
        args.cross_pair_2015_root,
        args.development_2016_2019_root,
        args.development_2020_root,
        args.rnd0037_assembly_report,
    )
    output = _write_new(args.report, value)
    print("RND0038_FULL_DEVELOPMENT_R000: COMPLETE")
    print("verified_2015_2019=20/20")
    print("verified_2020=4/4")
    print("pair_years=24/24")
    print("higher_volatility_outcomes=FALSE")
    print("strategy_selection=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={output}")
    print(f"report_sha256={_sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
