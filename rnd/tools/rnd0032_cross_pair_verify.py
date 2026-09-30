#!/usr/bin/env python3
"""Verify and compare the four 2015 structural shards for RND-0032."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from cross_pair_2015_evidence import (  # noqa: E402
    ALL_SYMBOLS,
    NEW_SYMBOLS,
    compare_structural_shards,
    load_structural_shard,
)
from oanda_historical_quarantine import (  # noqa: E402
    _json,
    verify_existing_shard,
)
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
    parser.add_argument("--audusd-reference", required=True)
    parser.add_argument("--cross-pair-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    acquisition = _json(ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json")
    calendar = _json(ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json")
    shard = {item["year"]: item for item in year_shards()}[2015]

    paths = {"AUDUSD": Path(args.audusd_reference).expanduser().resolve()}
    root = Path(args.cross_pair_root).expanduser().resolve()
    for symbol in NEW_SYMBOLS:
        paths[symbol] = root / symbol / "2015"

    structural = []
    for symbol in ALL_SYMBOLS:
        path = paths[symbol]
        if not verify_existing_shard(path, symbol, shard, acquisition, calendar):
            raise SystemExit(f"FAIL_CLOSED: {symbol}/2015 failed RND-0030 integrity verification")
        structural.append(load_structural_shard(path, symbol))

    report = compare_structural_shards(structural)
    report["integrity_verification"] = {symbol: "PASS" for symbol in ALL_SYMBOLS}
    report["seal_authority"] = False
    report["expansion_authority"] = False
    report["human_review_required"] = True

    output = _write_new(args.report, report)
    print("RND0032_CROSS_PAIR_VERIFICATION: PASS")
    for symbol in ALL_SYMBOLS:
        item = report["per_symbol"][symbol]
        print(
            f"{symbol}: rows={item['row_count']} "
            f"baseline_missing={item['baseline_missing_count']} "
            f"baseline_unexpected={item['baseline_unexpected_count']} "
            f"candidate_missing={item['candidate_missing_count']} "
            f"candidate_unexpected={item['candidate_unexpected_count']} "
            f"explained={item['explained_original_unexpected_count']}"
        )
    print(f"shared_baseline_missing={len(report['shared_baseline_missing_timestamps'])}")
    print(f"shared_baseline_unexpected={len(report['shared_baseline_unexpected_timestamps'])}")
    print(f"shared_candidate_unexpected={len(report['shared_candidate_unexpected_timestamps'])}")
    print("calendar_promotion=FALSE")
    print("strategy_evaluation=FALSE")
    print("expansion_authority=FALSE")
    print(f"report={output}")


if __name__ == "__main__":
    main()
