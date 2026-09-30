#!/usr/bin/env python3
"""Run the bounded RND-0034 2015-2019 fixed-M005 reconstruction locally."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from gap_aware_m005_reconstruction import SYMBOLS, reconstruct_pair  # noqa: E402
from oanda_historical_quarantine import _json, verify_existing_shard  # noqa: E402
from oanda_market_calendar import year_shards  # noqa: E402

PILOT_YEARS = (2015,)
DEVELOPMENT_YEARS = (2015, 2016, 2017, 2018, 2019)


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise SystemExit("FAIL_CLOSED: research report must remain outside repository")
    if path.exists():
        raise SystemExit("FAIL_CLOSED: report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    return path


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


def _path_for(symbol, year, args):
    if year == 2015 and symbol == "AUDUSD":
        return Path(args.audusd_2015_shard).expanduser().resolve()
    if year == 2015:
        return Path(args.cross_pair_2015_root).expanduser().resolve() / symbol / "2015"
    return Path(args.development_root).expanduser().resolve() / symbol / str(year)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audusd-2015-shard", required=True)
    parser.add_argument("--cross-pair-2015-root", required=True)
    parser.add_argument(
        "--mode",
        choices=("pilot-2015", "development-2015-2019"),
        required=True,
    )
    parser.add_argument("--development-root")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    years = PILOT_YEARS if args.mode == "pilot-2015" else DEVELOPMENT_YEARS
    if args.mode == "development-2015-2019" and not args.development_root:
        parser.error("--development-root is required for development-2015-2019")
    if args.mode == "pilot-2015" and args.development_root:
        raise SystemExit(
            "FAIL_CLOSED: --development-root is prohibited in pilot-2015 mode"
        )

    acquisition = _json(
        ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"
    )
    calendar = _json(
        ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json"
    )
    r32 = _json(ROOT / "rnd" / "research" / "RND0032_CROSS_PAIR_2015_EVIDENCE_RECORD.json")
    r33 = _json(ROOT / "rnd" / "research" / "RND0033_DEVELOPMENT_HISTORY_EVIDENCE_RECORD.json")
    shard_by_year = {item["year"]: item for item in year_shards()}

    results = {}
    identities = {}
    for symbol in SYMBOLS:
        combined_rows = []
        identities[symbol] = {}
        for year in years:
            path = _path_for(symbol, year, args)
            if not verify_existing_shard(
                path, symbol, shard_by_year[year], acquisition, calendar
            ):
                raise SystemExit(
                    f"FAIL_CLOSED: {symbol}/{year} failed RND-0030 integrity verification"
                )
            manifest = _json(path / "quarantine_manifest.json")
            expected = _expected_identity(symbol, year, r32, r33)
            if not _identity_matches(manifest, expected):
                raise SystemExit(
                    f"FAIL_CLOSED: {symbol}/{year} does not match bound repository evidence"
                )
            rows = _json(path / "canonical_rows.json")
            combined_rows.extend(rows)
            identities[symbol][str(year)] = {
                "canonical_rows_sha256": manifest["canonical_rows_sha256"],
                "raw_bundle_sha256": manifest["aggregate_raw_bundle_sha256"],
                "standard_schedule_sha256": manifest["standard_schedule_sha256"],
                "row_count": manifest["row_count"],
                "integrity": "PASS",
                "repository_identity": "MATCH",
            }

        results[symbol] = reconstruct_pair(symbol, combined_rows)

    report = {
        "contract_version": "RND-0034-development-reconstruction-report-v0.2",
        "task_id": "RND-0034",
        "run_mode": args.mode,
        "evidence_class": (
            "TECHNICAL_INTEGRATION_PILOT"
            if args.mode == "pilot-2015"
            else "DEVELOPMENT_RECONSTRUCTION"
        ),
        "years": list(years),
        "symbols": list(SYMBOLS),
        "trial_count": 1,
        "portfolio_sizing": False,
        "evidence_identity": identities,
        "per_symbol": results,
        "authority": {
            "strategy_selection": False,
            "validation_open": False,
            "final_test_open": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_review_required": True,
        },
    }
    output = _write_new(args.report, report)

    print(
        "RND0034_2015_TECHNICAL_PILOT: COMPLETE"
        if args.mode == "pilot-2015"
        else "RND0034_DEVELOPMENT_RECONSTRUCTION: COMPLETE"
    )
    for symbol in SYMBOLS:
        value = results[symbol]
        hit = value["net_hit_rate"]
        hit_text = "NA" if hit is None else f"{hit:.6f}"
        print(
            f"{symbol}: rows={value['row_count']} "
            f"episodes={value['contiguous_episode_count']} "
            f"gaps={value['gap_count']} "
            f"trades={value['completed_trade_count']} "
            f"censored={value['censored_trade_count']} "
            f"hit_rate={hit_text} "
            f"net_equity_index={value['completed_trade_net_equity_index']:.8f} "
            f"net_max_dd={value['completed_trade_net_max_drawdown']:.8f} "
            f"cost_drag={value['total_execution_cost_drag']:.8f}"
        )
    print("strategy_search=FALSE")
    print("portfolio_sizing=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={output}")


if __name__ == "__main__":
    main()
