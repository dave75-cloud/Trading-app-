#!/usr/bin/env python3
"""Governed development-period launcher for RND-0035.

Stage 1 supports a no-outcome preflight over the already-authorized 2015-2019
RND-0031/32/33 evidence. It verifies the frozen trial matrix, input identities,
and authority boundaries while the historical outcome gate remains closed.

Historical strategy outcomes remain fail-closed until the repository trial plan
is explicitly advanced to an outcome-authorized stage after local validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from oanda_historical_quarantine import _json, verify_existing_shard
from oanda_market_calendar import year_shards
from rnd0035_trial_plan import load_plan


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "rnd" / "research" / "RND0035_TRIAL_PLAN.json"
DEVELOPMENT_YEARS = (2015, 2016, 2017, 2018, 2019)
STRATEGY_FAMILIES = (
    "A_LOCAL_PARAMETER",
    "C_SESSION",
    "D_COST_SLIPPAGE",
    "E_GAP_POLICY",
    "F_EXECUTION",
)


class RND0035DevelopmentRunnerError(ValueError):
    pass


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def preflight(plan, audusd_2015_shard, cross_pair_2015_root, development_root):
    if plan["outcomes_authorized"] or plan["execution_gate"]["new_outcomes_may_run"]:
        raise RND0035DevelopmentRunnerError(
            "preflight requires historical outcome gate to remain closed"
        )
    if plan["validation_open"] or plan["final_test_open"]:
        raise RND0035DevelopmentRunnerError("validation/final authority unexpectedly open")
    if plan["broker_writes"] or plan["capital_authority"] or plan["strategy_selection"]:
        raise RND0035DevelopmentRunnerError("prohibited authority unexpectedly open")

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
    verified = 0
    for symbol in plan["authorized_symbols"]:
        identities[symbol] = {}
        for year in DEVELOPMENT_YEARS:
            path = _path_for(
                symbol,
                year,
                audusd_2015_shard,
                cross_pair_2015_root,
                development_root,
            )
            if not verify_existing_shard(
                path, symbol, shard_by_year[year], acquisition, calendar
            ):
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
            verified += 1

    trial_ids = declared_strategy_trial_ids(plan)
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
        "historical_outcomes_generated": False,
        "outcome_gate_open": False,
        "validation_open": False,
        "final_test_open": False,
        "strategy_selection": False,
        "broker_writes": False,
        "capital_authority": False,
        "promotion_authority": "HUMAN_ONLY",
        "evidence_identity": identities,
        "status": "PASS",
    }


def historical_outcomes(plan, *args, **kwargs):
    if not plan["execution_gate"]["new_outcomes_may_run"]:
        raise RND0035DevelopmentRunnerError(
            "historical RND-0035 outcomes prohibited: execution gate remains closed"
        )
    raise RND0035DevelopmentRunnerError(
        "outcome-authorized historical execution not implemented in preflight stage"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument("--development-root", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run-outcomes", action="store_true")
    args = parser.parse_args(argv)

    plan = load_plan(PLAN_PATH)
    paths = (
        args.audusd_2015_shard,
        args.cross_pair_2015_root,
        args.development_root,
    )
    if args.preflight:
        print(json.dumps(preflight(plan, *paths), sort_keys=True, indent=2))
        return 0
    historical_outcomes(plan, *paths)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
