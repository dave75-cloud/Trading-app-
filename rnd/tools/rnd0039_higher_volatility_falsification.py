#!/usr/bin/env python3
"""Governed RND-0039 two-point higher-volatility hypothesis falsification."""

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
from rnd0038_full_development_r000 import _load_2020_rows, _validate_assembly_report  # noqa: E402
from rnd0038_reference_diagnostics_adapter import analyze_reference_results_2015_2020  # noqa: E402
from rnd0039_threshold_kernel_adapter import reconstruct_pair_threshold_2015_2020  # noqa: E402
from oanda_historical_quarantine import _json  # noqa: E402

AUTH_PATH = ROOT / "rnd" / "research" / "RND0039_OUTCOME_AUTHORIZATION.json"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
DEVELOPMENT_START = "2015-01-01T00:00:00Z"
DEVELOPMENT_END = "2020-12-31T19:15:00Z"
REFERENCE = 0.0005
TREATMENT = 0.0006


class RND0039Error(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0039Error(message)


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_authorization(path=AUTH_PATH):
    v = _json(path)
    _require(v.get("task_id") == "RND-0039", "authorization task changed")
    _require(v.get("status") == "ACTIVE", "RND-0039 authorization inactive")
    _require(v.get("scope") == "TWO_POINT_HIGHER_VOLATILITY_HYPOTHESIS_FALSIFICATION_ONLY", "scope changed")
    _require(v.get("authorized_interval") == {"start_inclusive_utc": DEVELOPMENT_START, "end_exclusive_utc": DEVELOPMENT_END}, "interval changed")
    _require(v.get("symbols") == list(SYMBOLS), "symbol universe changed")
    _require(v.get("authorized_thresholds") == [REFERENCE, TREATMENT], "threshold set changed")
    _require(v.get("outcomes_authorized") is True, "outcomes not authorized")
    for key in (
        "parameter_search", "thresholds_above_0006", "intermediate_thresholds",
        "pair_specific_thresholds", "joint_parameter_search", "strategy_selection",
        "validation_open", "final_test_open", "portfolio_sizing", "broker_writes",
        "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        _require(v.get(key) is False, f"prohibited authority opened: {key}")
    _require(v.get("human_review_required") is True, "human review requirement removed")
    return v


def _summary(result):
    return {
        "trades": result["completed_trade_count"],
        "hit_rate": result["net_hit_rate"],
        "gross_equity_index": result["completed_trade_gross_equity_index"],
        "net_equity_index": result["completed_trade_net_equity_index"],
        "net_max_drawdown": result["completed_trade_net_max_drawdown"],
        "execution_cost_drag": result["total_execution_cost_drag"],
    }


def _difference(ref, trt):
    return {
        "trade_count": trt["trades"] - ref["trades"],
        "hit_rate": trt["hit_rate"] - ref["hit_rate"],
        "gross_equity_index": trt["gross_equity_index"] - ref["gross_equity_index"],
        "net_equity_index": trt["net_equity_index"] - ref["net_equity_index"],
        "net_max_drawdown": trt["net_max_drawdown"] - ref["net_max_drawdown"],
        "execution_cost_drag": trt["execution_cost_drag"] - ref["execution_cost_drag"],
    }


def _year2020(result):
    trades = [t for t in result["trades"] if str(t.get("exit_timestamp", "")).startswith("2020-")]
    return {
        "trades": len(trades),
        "net_return_sum": sum(float(t["net_return"]) for t in trades),
        "gross_return_sum": sum(float(t["gross_return"]) for t in trades),
        "positive_trade_fraction": (sum(1 for t in trades if float(t["net_return"]) > 0) / len(trades)) if trades else None,
    }


def run(audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root,
        development_2020_root, rnd0037_assembly_report):
    load_authorization()
    _validate_assembly_report(rnd0037_assembly_report)

    plan = load_plan(PLAN_PATH)
    _require(plan.get("validation_open") is False and plan.get("final_test_open") is False, "validation/final unexpectedly open")
    ids_old, verified, historical_rows = _verify_evidence(
        plan, audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root, load_rows=True
    )
    _require(verified == 20, "2015-2019 verification not 20/20")
    ids_2020, rows_2020 = _load_2020_rows(development_2020_root)

    full_rows = {}
    for symbol in SYMBOLS:
        rows = list(historical_rows[symbol]) + list(rows_2020[symbol])
        ts = [r["timestamp_utc"] for r in rows]
        _require(ts == sorted(ts) and len(ts) == len(set(ts)), f"{symbol}: row chronology/identity failure")
        _require(ts[0] >= DEVELOPMENT_START and ts[-1] < DEVELOPMENT_END, f"{symbol}: development boundary breach")
        full_rows[symbol] = rows

    arms = {}
    for label, threshold in (("R000_0005", REFERENCE), ("HV_0006", TREATMENT)):
        per_symbol = {
            symbol: reconstruct_pair_threshold_2015_2020(symbol, full_rows[symbol], threshold)
            for symbol in SYMBOLS
        }
        arms[label] = {
            "threshold": threshold,
            "per_symbol": {symbol: _summary(per_symbol[symbol]) for symbol in SYMBOLS},
            "diagnostics": analyze_reference_results_2015_2020(per_symbol),
            "year2020": {symbol: _year2020(per_symbol[symbol]) for symbol in SYMBOLS},
        }

    comparison = {}
    for symbol in SYMBOLS:
        comparison[symbol] = _difference(
            arms["R000_0005"]["per_symbol"][symbol],
            arms["HV_0006"]["per_symbol"][symbol],
        )

    return {
        "contract_version": "RND0039-two-point-higher-volatility-falsification-v1",
        "task_id": "RND-0039",
        "development_interval": {"start_inclusive_utc": DEVELOPMENT_START, "end_exclusive_utc": DEVELOPMENT_END},
        "evidence_identity": {
            "verified_2015_2019": "20/20",
            "verified_2020": "4/4",
            "pair_years": "24/24",
            "identities_2015_2019": ids_old,
            "identities_2020": ids_2020,
        },
        "arms": arms,
        "treatment_minus_reference": comparison,
        "parameter_search": False,
        "thresholds_tested": [REFERENCE, TREATMENT],
        "strategy_selection": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0039Error("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audusd-2015-shard", required=True)
    p.add_argument("--cross-pair-2015-root", required=True)
    p.add_argument("--development-2016-2019-root", required=True)
    p.add_argument("--development-2020-root", required=True)
    p.add_argument("--rnd0037-assembly-report", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args(argv)
    value = run(a.audusd_2015_shard, a.cross_pair_2015_root, a.development_2016_2019_root,
                a.development_2020_root, a.rnd0037_assembly_report)
    out = _write_new(a.report, value)
    print("RND0039_HIGHER_VOLATILITY_FALSIFICATION: COMPLETE")
    print("verified_2015_2019=20/20")
    print("verified_2020=4/4")
    print("pair_years=24/24")
    print("thresholds_tested=0.0005,0.0006")
    print("parameter_search=FALSE")
    print("strategy_selection=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={out}")
    print(f"report_sha256={_sha256_file(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
