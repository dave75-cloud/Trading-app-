#!/usr/bin/env python3
"""Governed development-period launcher for RND-0035.

The frozen numerical trial plan remains immutable and globally fail-closed.
A separate authorization record may permit only the already-declared 2015-2019
REFERENCE/A/C/D/E/F development strategy outcomes. B concentration diagnostics,
G dependence resampling, validation/final data and all execution/capital
authority remain closed.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "rnd" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from oanda_historical_quarantine import _json, verify_existing_shard
from oanda_market_calendar import year_shards
from rnd0035_audit_enrichment import compact_historical_audit
from rnd0035_trial_dispatch import run_declared_trial_pair
from rnd0035_trial_plan import load_plan


PLAN_PATH = ROOT / "rnd" / "research" / "RND0035_TRIAL_PLAN.json"
AUTH_PATH = ROOT / "rnd" / "research" / "RND0035_DEVELOPMENT_OUTCOME_AUTHORIZATION.json"
DEVELOPMENT_YEARS = (2015, 2016, 2017, 2018, 2019)
STRATEGY_FAMILIES = (
    "A_LOCAL_PARAMETER",
    "C_SESSION",
    "D_COST_SLIPPAGE",
    "E_GAP_POLICY",
    "F_EXECUTION",
)
AUTHORIZED_FAMILIES = (
    "REFERENCE",
    "A_LOCAL_PARAMETER",
    "C_SESSION",
    "D_COST_SLIPPAGE",
    "E_GAP_POLICY",
    "F_EXECUTION",
)
CLOSED_FAMILIES = ("B_CONCENTRATION", "G_DEPENDENCE_RESAMPLING")


class RND0035DevelopmentRunnerError(ValueError):
    pass


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise RND0035DevelopmentRunnerError("report must remain outside repository")
    if path.exists():
        raise RND0035DevelopmentRunnerError("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _require(condition, message):
    if not condition:
        raise RND0035DevelopmentRunnerError(message)


def load_development_authorization(path=AUTH_PATH):
    auth = _json(Path(path))
    _require(auth.get("task_id") == "RND-0035", "authorization task id changed")
    _require(auth.get("status") == "ACTIVE", "development outcome authorization inactive")
    _require(
        auth.get("authorized_stage") == "DEVELOPMENT_2015_2019_ADVERSARIAL_STRATEGY_OUTCOMES",
        "authorization stage changed",
    )
    _require(
        auth.get("authorized_trial_plan_sha256") == _sha256(PLAN_PATH),
        "authorization does not bind current frozen trial plan",
    )
    _require(auth.get("authorized_years") == list(DEVELOPMENT_YEARS), "authorized years changed")
    _require(
        auth.get("authorized_symbols") == ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"],
        "authorized symbols changed",
    )
    _require(
        auth.get("authorized_families") == list(AUTHORIZED_FAMILIES),
        "authorized strategy family scope changed",
    )
    _require(auth.get("authorized_strategy_trial_count") == 36, "authorized trial count changed")
    _require(auth.get("closed_families") == list(CLOSED_FAMILIES), "B/G closure changed")

    authority = auth.get("authority", {})
    _require(authority.get("development_strategy_outcomes") is True, "development outcomes not authorized")
    for key in (
        "concentration_diagnostics",
        "dependence_resampling",
        "validation_open",
        "final_test_open",
        "strategy_selection",
        "portfolio_sizing",
        "broker_writes",
        "capital_authority",
        "automatic_promotion",
        "automatic_merge",
    ):
        _require(authority.get(key) is False, f"authorization boundary opened: {key}")
    _require(authority.get("promotion_authority") == "HUMAN_ONLY", "promotion authority changed")
    _require(authority.get("human_review_required") is True, "human review requirement removed")
    return auth


def _expected_identity(symbol, year, r32, r33):
    if year == 2015:
        return r32["per_symbol"][symbol]
    return r33["per_year"][str(year)]["per_symbol"][symbol]


def _identity_matches(manifest, expected):
    checks = {
        "aggregate_raw_bundle_sha256": expected["raw_bundle_sha256"],
        "canonical_rows_sha256": expected["canonical_rows_sha256"],
        "standard_schedule_sha256": expected["standard_schedule_sha256"],
        "row_count": expected["row_count"],
    }
    return all(manifest.get(key) == value for key, value in checks.items())


def _path_for(symbol, year, audusd_2015_shard, cross_pair_2015_root, development_root):
    if year == 2015 and symbol == "AUDUSD":
        return Path(audusd_2015_shard).expanduser().resolve()
    if year == 2015:
        return Path(cross_pair_2015_root).expanduser().resolve() / symbol / "2015"
    return Path(development_root).expanduser().resolve() / symbol / str(year)


def declared_strategy_trial_ids(plan):
    ids = ["R000"]
    for family_name in STRATEGY_FAMILIES:
        ids.extend(item["trial_id"] for item in plan["families"][family_name]["trials"])
    expected = plan["declared_strategy_variant_trials"]["total_including_reference"]
    if len(ids) != expected or len(ids) != len(set(ids)):
        raise RND0035DevelopmentRunnerError("frozen strategy trial accounting mismatch")
    return ids


def _verify_evidence(plan, audusd_2015_shard, cross_pair_2015_root, development_root, load_rows=False):
    acquisition = _json(
        ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"
    )
    calendar = _json(
        ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json"
    )
    r32 = _json(ROOT / "rnd" / "research" / "RND0032_CROSS_PAIR_2015_EVIDENCE_RECORD.json")
    r33 = _json(ROOT / "rnd" / "research" / "RND0033_DEVELOPMENT_HISTORY_EVIDENCE_RECORD.json")
    shard_by_year = {item["year"]: item for item in year_shards()}

    identities = {}
    rows_by_symbol = {} if load_rows else None
    verified = 0
    for symbol in plan["authorized_symbols"]:
        identities[symbol] = {}
        combined_rows = [] if load_rows else None
        for year in DEVELOPMENT_YEARS:
            path = _path_for(
                symbol, year, audusd_2015_shard, cross_pair_2015_root, development_root
            )
            if not verify_existing_shard(path, symbol, shard_by_year[year], acquisition, calendar):
                raise RND0035DevelopmentRunnerError(
                    f"{symbol}/{year} failed RND-0030 integrity verification"
                )
            manifest = _json(path / "quarantine_manifest.json")
            expected = _expected_identity(symbol, year, r32, r33)
            if not _identity_matches(manifest, expected):
                raise RND0035DevelopmentRunnerError(
                    f"{symbol}/{year} does not match repository-bound evidence"
                )
            identities[symbol][str(year)] = {
                "canonical_rows_sha256": manifest["canonical_rows_sha256"],
                "raw_bundle_sha256": manifest["aggregate_raw_bundle_sha256"],
                "standard_schedule_sha256": manifest["standard_schedule_sha256"],
                "row_count": manifest["row_count"],
                "integrity": "PASS",
                "repository_identity": "MATCH",
            }
            if load_rows:
                combined_rows.extend(_json(path / "canonical_rows.json"))
            verified += 1
        if load_rows:
            rows_by_symbol[symbol] = combined_rows

    return identities, verified, rows_by_symbol


def preflight(plan, audusd_2015_shard, cross_pair_2015_root, development_root):
    # The numerical plan itself deliberately remains globally closed; scoped
    # outcome authority lives only in the separate authorization record.
    if plan["outcomes_authorized"] or plan["execution_gate"]["new_outcomes_may_run"]:
        raise RND0035DevelopmentRunnerError("frozen numerical plan unexpectedly opened")
    if plan["validation_open"] or plan["final_test_open"]:
        raise RND0035DevelopmentRunnerError("validation/final authority unexpectedly open")
    if plan["broker_writes"] or plan["capital_authority"] or plan["strategy_selection"]:
        raise RND0035DevelopmentRunnerError("prohibited authority unexpectedly open")

    identities, verified, _ = _verify_evidence(
        plan, audusd_2015_shard, cross_pair_2015_root, development_root, load_rows=False
    )
    trial_ids = declared_strategy_trial_ids(plan)
    auth = load_development_authorization()
    return {
        "task_id": "RND-0035",
        "mode": "DEVELOPMENT_PREFLIGHT_NO_OUTCOMES",
        "authorized_years": list(DEVELOPMENT_YEARS),
        "authorized_symbols": list(plan["authorized_symbols"]),
        "verified_shards": verified,
        "expected_shards": len(DEVELOPMENT_YEARS) * len(plan["authorized_symbols"]),
        "evidence_identity_pass_match": f"{verified}/{len(DEVELOPMENT_YEARS) * len(plan['authorized_symbols'])}",
        "declared_strategy_trial_count": len(trial_ids),
        "declared_strategy_trial_ids": trial_ids,
        "trial_plan_sha256": _sha256(PLAN_PATH),
        "development_authorization_sha256": _sha256(AUTH_PATH),
        "development_outcomes_authorized_separately": auth["authority"]["development_strategy_outcomes"],
        "historical_outcomes_generated": False,
        "validation_open": False,
        "final_test_open": False,
        "strategy_selection": False,
        "broker_writes": False,
        "capital_authority": False,
        "promotion_authority": "HUMAN_ONLY",
        "evidence_identity": identities,
        "status": "PASS",
    }


def _trial_summary(trial_id, symbol, result):
    authority = result.get("authority", {})
    for key in (
        "strategy_selection",
        "portfolio_sizing",
        "broker_writes",
        "capital_authority",
        "automatic_promotion",
        "automatic_merge",
        "validation_open",
        "final_test_open",
    ):
        if authority.get(key, False):
            raise RND0035DevelopmentRunnerError(
                f"{trial_id}/{symbol}: prohibited authority opened: {key}"
            )

    audit = compact_historical_audit(result)
    return {
        "trial_id": trial_id,
        "symbol": symbol,
        "row_count": result["row_count"],
        "gap_count": result["gap_count"],
        "completed_trade_count": result["completed_trade_count"],
        "censored_trade_count": result["censored_trade_count"],
        "net_hit_rate": audit["net_hit_rate"],
        "completed_trade_gross_equity_index": result["completed_trade_gross_equity_index"],
        "completed_trade_gross_max_drawdown": result["completed_trade_gross_max_drawdown"],
        "completed_trade_net_equity_index": result["completed_trade_net_equity_index"],
        "completed_trade_net_max_drawdown": result["completed_trade_net_max_drawdown"],
        "total_execution_cost_drag": result["total_execution_cost_drag"],
        "audit": audit,
        "authority": {
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "validation_open": False,
            "final_test_open": False,
            "human_review_required": True,
        },
    }


def historical_outcomes(plan, audusd_2015_shard, cross_pair_2015_root, development_root, report):
    auth = load_development_authorization()
    trial_ids = declared_strategy_trial_ids(plan)
    _require(len(trial_ids) == auth["authorized_strategy_trial_count"], "authorization/trial count mismatch")

    identities, verified, rows_by_symbol = _verify_evidence(
        plan, audusd_2015_shard, cross_pair_2015_root, development_root, load_rows=True
    )
    expected_shards = len(DEVELOPMENT_YEARS) * len(plan["authorized_symbols"])
    _require(verified == expected_shards, "not all authorized evidence shards verified")

    outcomes = {trial_id: {} for trial_id in trial_ids}
    for symbol in plan["authorized_symbols"]:
        rows = rows_by_symbol[symbol]
        for trial_id in trial_ids:
            result = run_declared_trial_pair(trial_id, symbol, rows)
            outcomes[trial_id][symbol] = _trial_summary(trial_id, symbol, result)
            del result
            gc.collect()
        del rows_by_symbol[symbol]
        gc.collect()

    report_value = {
        "contract_version": "RND0035-development-adversarial-outcomes-v1",
        "task_id": "RND-0035",
        "mode": "DEVELOPMENT_2015_2019_ADVERSARIAL_STRATEGY_OUTCOMES",
        "authorized_years": list(DEVELOPMENT_YEARS),
        "authorized_symbols": list(plan["authorized_symbols"]),
        "trial_plan_sha256": _sha256(PLAN_PATH),
        "development_authorization_sha256": _sha256(AUTH_PATH),
        "evidence_identity_pass_match": f"{verified}/{expected_shards}",
        "evidence_identity": identities,
        "declared_strategy_trial_count": len(trial_ids),
        "executed_strategy_trial_count": len(trial_ids),
        "pair_trial_result_count": len(trial_ids) * len(plan["authorized_symbols"]),
        "executed_trial_ids": trial_ids,
        "closed_families": list(CLOSED_FAMILIES),
        "outcomes": outcomes,
        "historical_outcomes_generated": True,
        "authority": {
            "development_strategy_outcomes": True,
            "concentration_diagnostics": False,
            "dependence_resampling": False,
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
    output = _write_new(report, report_value)
    return report_value, output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument("--development-root", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run-outcomes", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args(argv)

    plan = load_plan(PLAN_PATH)
    paths = (
        args.audusd_2015_shard,
        args.cross_pair_2015_root,
        args.development_root,
    )
    if args.preflight:
        if args.report:
            raise RND0035DevelopmentRunnerError("--report prohibited in preflight mode")
        print(json.dumps(preflight(plan, *paths), sort_keys=True, indent=2))
        return 0

    if not args.report:
        parser.error("--report is required with --run-outcomes")
    value, output = historical_outcomes(plan, *paths, args.report)
    print("RND0035_DEVELOPMENT_ADVERSARIAL_OUTCOMES: COMPLETE")
    print(f"strategy_trials={value['executed_strategy_trial_count']}")
    print(f"pair_trial_results={value['pair_trial_result_count']}")
    print(f"evidence_identity={value['evidence_identity_pass_match']}")
    print("B_CONCENTRATION=FALSE")
    print("G_DEPENDENCE_RESAMPLING=FALSE")
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
