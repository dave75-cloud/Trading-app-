#!/usr/bin/env python3
"""Verify and compare RND-0033 four-pair 2016-2019 structural evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from development_history_evidence import (  # noqa: E402
    SYMBOLS, YEARS, compare_development_history, load_structural_shard,
)
from oanda_historical_quarantine import _json, verify_existing_shard  # noqa: E402
from oanda_market_calendar import year_shards  # noqa: E402


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise SystemExit("FAIL_CLOSED: report must remain outside repository")
    if path.exists():
        raise SystemExit("FAIL_CLOSED: report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    acquisition = _json(ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json")
    calendar = _json(ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json")
    shard_by_year = {item["year"]: item for item in year_shards()}
    root = Path(args.evidence_root).expanduser().resolve()

    structural = []
    for symbol in SYMBOLS:
        for year in YEARS:
            path = root / symbol / str(year)
            if not verify_existing_shard(
                path, symbol, shard_by_year[year], acquisition, calendar
            ):
                raise SystemExit(
                    f"FAIL_CLOSED: {symbol}/{year} failed RND-0030 integrity verification"
                )
            structural.append(load_structural_shard(path, symbol, year))

    report = compare_development_history(structural)
    report["integrity_verification"] = {
        f"{symbol}:{year}": "PASS" for symbol in SYMBOLS for year in YEARS
    }
    report["seal_authority"] = False
    report["expansion_authority"] = False
    report["human_review_required"] = True
    output = _write_new(args.report, report)

    print("RND0033_DEVELOPMENT_HISTORY_VERIFICATION: PASS")
    for year in YEARS:
        y = report["per_year"][str(year)]
        print(
            f"{year}: shared_missing={y['shared_baseline_missing_count']} "
            f"shared_unexpected={y['shared_baseline_unexpected_count']} "
            f"shared_candidate_unexpected={y['shared_candidate_unexpected_count']}"
        )
        for symbol in SYMBOLS:
            item = y["per_symbol"][symbol]
            print(
                f"  {symbol}: rows={item['row_count']} "
                f"baseline_missing={item['baseline_missing_count']} "
                f"baseline_unexpected={item['baseline_unexpected_count']} "
                f"candidate_missing={item['candidate_missing_count']} "
                f"candidate_unexpected={item['candidate_unexpected_count']} "
                f"explained={item['explained_original_unexpected_count']}"
            )
    print("calendar_promotion=FALSE")
    print("regime_promotion=FALSE")
    print("strategy_evaluation=FALSE")
    print("expansion_authority=FALSE")
    print(f"report={output}")


if __name__ == "__main__":
    main()
