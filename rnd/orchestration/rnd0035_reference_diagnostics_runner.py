#!/usr/bin/env python3
"""Fail-closed RND-0035 R000 reference diagnostics runner.

B concentration, D break-even cost diagnostics, G per-pair stationary bootstrap,
and the observed four-pair timestamped concurrent reference aggregation are
staged here. Execution remains prohibited until the separate diagnostics gate
is explicitly opened after local validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gap_aware_m005_reconstruction import reconstruct_pair
from rnd0035_concentration_diagnostics import concentration_diagnostics
from rnd0035_concurrent_reference_stats import concurrent_reference_statistics
from rnd0035_cost_diagnostics import cost_bridge
from rnd0035_development_runner import (
    DEVELOPMENT_YEARS,
    PLAN_PATH,
    ROOT,
    _sha256,
    _verify_evidence,
)
from rnd0035_stationary_bootstrap import (
    bootstrap_configuration,
    declared_configuration_grid,
)
from rnd0035_trial_plan import load_plan


GATE_PATH = ROOT / "rnd" / "research" / "RND0035_REFERENCE_DIAGNOSTICS_GATE.json"


class RND0035ReferenceDiagnosticsError(ValueError):
    pass


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require(condition, message):
    if not condition:
        raise RND0035ReferenceDiagnosticsError(message)


def load_gate(require_open=False):
    gate = _json(GATE_PATH)
    _require(gate.get("task_id") == "RND-0035", "diagnostics gate task changed")
    _require(gate.get("scope") == "R000_REFERENCE_DIAGNOSTICS_ONLY", "diagnostics scope changed")
    authority = gate.get("authority", {})
    for key in (
        "validation_open", "final_test_open", "strategy_selection", "portfolio_sizing",
        "broker_writes", "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        _require(authority.get(key) is False, f"prohibited authority opened: {key}")
    _require(authority.get("promotion_authority") == "HUMAN_ONLY", "promotion authority changed")
    _require(authority.get("human_review_required") is True, "human review requirement removed")
    if require_open:
        _require(gate.get("status") == "ACTIVE", "RND-0035 reference diagnostics gate remains closed")
        for name in (
            "B_CONCENTRATION", "D_BREAK_EVEN_COST_DIAGNOSTICS",
            "G_DEPENDENCE_RESAMPLING", "G_CONCURRENT_REFERENCE_AGGREGATION",
        ):
            _require(gate.get("families", {}).get(name) is True, f"diagnostic family closed: {name}")
    return gate


def _ledger_sha(trades):
    payload = json.dumps(trades, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def analyze_reference_results(per_symbol):
    _require(set(per_symbol) == {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}, "exact four-pair R000 result set required")
    all_trades = []
    per_pair_cost = {}
    per_pair_bootstrap = {}
    ledger_sha = {}

    for symbol in ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY"):
        result = per_symbol[symbol]
        _require(result.get("symbol") == symbol, f"R000 symbol mismatch: {symbol}")
        trades = result.get("trades")
        _require(isinstance(trades, list), f"R000 trade ledger missing: {symbol}")
        all_trades.extend(trades)
        ledger_sha[symbol] = _ledger_sha(trades)
        per_pair_cost[symbol] = cost_bridge(trades)

        stream = [
            {"symbol": symbol, "net_return": trade["net_return"]}
            for trade in trades
        ]
        per_pair_bootstrap[symbol] = [
            bootstrap_configuration(
                stream,
                config["seed"],
                config["expected_block_length_trades"],
            )
            for config in declared_configuration_grid()
        ]

    all_trades.sort(key=lambda trade: trade["exit_timestamp"])
    return {
        "contract_version": "RND0035-reference-diagnostics-v1",
        "B_concentration": concentration_diagnostics(all_trades),
        "D_cost_diagnostics_by_pair": per_pair_cost,
        "G_per_pair_stationary_bootstrap": per_pair_bootstrap,
        "G_four_pair_concurrent_reference": concurrent_reference_statistics(per_symbol),
        "R000_trade_ledger_sha256_by_pair": ledger_sha,
        "authority": {
            "validation_open": False,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "promotion_authority": "HUMAN_ONLY",
            "human_review_required": True,
        },
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise RND0035ReferenceDiagnosticsError("report must remain outside repository")
    if path.exists():
        raise RND0035ReferenceDiagnosticsError("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def historical_reference_diagnostics(audusd_2015_shard, cross_pair_2015_root, development_root, report):
    gate = load_gate(require_open=True)
    plan = load_plan(PLAN_PATH)
    _require(plan["outcomes_authorized"] is False, "frozen numerical plan unexpectedly open")
    _require(plan["validation_open"] is False and plan["final_test_open"] is False, "validation/final unexpectedly open")

    identities, verified, rows_by_symbol = _verify_evidence(
        plan, audusd_2015_shard, cross_pair_2015_root, development_root, load_rows=True
    )
    _require(verified == 20, "authorized evidence identity verification not 20/20")

    per_symbol = {
        symbol: reconstruct_pair(symbol, rows_by_symbol[symbol])
        for symbol in plan["authorized_symbols"]
    }
    diagnostics = analyze_reference_results(per_symbol)
    value = {
        "task_id": "RND-0035",
        "mode": "R000_REFERENCE_B_D_G_DIAGNOSTICS",
        "authorized_years": list(DEVELOPMENT_YEARS),
        "authorized_symbols": list(plan["authorized_symbols"]),
        "trial_plan_sha256": _sha256(PLAN_PATH),
        "diagnostics_gate_sha256": _sha256(GATE_PATH),
        "evidence_identity_pass_match": "20/20",
        "evidence_identity": identities,
        "diagnostics": diagnostics,
        "gate": {
            "status": gate["status"],
            "scope": gate["scope"],
        },
        "authority": diagnostics["authority"],
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }
    output = _write_new(report, value)
    return value, output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument("--development-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    value, output = historical_reference_diagnostics(
        args.audusd_2015_shard,
        args.cross_pair_2015_root,
        args.development_root,
        args.report,
    )
    print("RND0035_REFERENCE_DIAGNOSTICS: COMPLETE")
    print("evidence_identity=20/20")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print("strategy_selection=FALSE")
    print(f"report={output}")
    print(f"report_sha256={_sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
