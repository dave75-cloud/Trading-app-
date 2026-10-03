#!/usr/bin/env python3
"""Outcome-blind calendar classification review for RND-0036 2020 development evidence.

This classifies structural timestamp discrepancies only. The empirical 17:00
New York candidate remains non-authoritative and may not modify canonical rows,
calendar authority, strategy state or validation/final access.
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

from historical_calendar_evidence import evaluate_1700_hypothesis  # noqa: E402
from rnd0036_2020_development_acquisition import (  # noqa: E402
    SYMBOLS,
    START_UTC,
    END_UTC,
    boundary_proof,
)
from oanda_historical_quarantine import _json  # noqa: E402


class RND0036CalendarClassificationError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0036CalendarClassificationError(message)


def _sum_bars(classes, key):
    return sum(int(item["bars"]) for item in classes.get(key, []))


def classify_symbol(shard_root, symbol):
    shard_root = Path(shard_root)
    rows = _json(shard_root / "canonical_rows.json")
    schedule = _json(shard_root / "standard_schedule.json")
    _require(isinstance(rows, list) and rows, f"{symbol}: canonical rows required")
    _require(isinstance(schedule, list), f"{symbol}: standard schedule required")
    proof = boundary_proof(shard_root, symbol)
    actual = [row["timestamp_utc"] for row in rows]
    result = evaluate_1700_hypothesis(actual, schedule, START_UTC, END_UTC)
    classes = result["missing_run_classes"]
    return {
        "symbol": symbol,
        "row_count": len(rows),
        "boundary_status": proof["boundary_status"],
        "baseline_missing_count": result["baseline_missing_count"],
        "baseline_unexpected_count": result["baseline_unexpected_count"],
        "candidate_missing_count": result["candidate_missing_count"],
        "candidate_unexpected_count": result["candidate_unexpected_count"],
        "explained_original_unexpected_count": result["explained_original_unexpected_count"],
        "explained_original_unexpected_fraction": result["explained_original_unexpected_fraction"],
        "remaining_unexpected_timestamps": result["remaining_unexpected_timestamps"],
        "residual_short_gap_bars": _sum_bars(classes, "residual_short_gap"),
        "closure_shaped_candidate_bars": _sum_bars(classes, "closure_shaped_candidate"),
        "unclassified_gap_bars": _sum_bars(classes, "unclassified"),
        "missing_run_classes": classes,
        "candidate_authority": "NONE",
        "calendar_modified": False,
        "evidence_modified": False,
        "strategy_evaluation": False,
    }


def review(root):
    root = Path(root).expanduser().resolve()
    per_symbol = {}
    residual_sets = []
    for symbol in SYMBOLS:
        shard_root = root / symbol / "2020-development"
        item = classify_symbol(shard_root, symbol)
        per_symbol[symbol] = item
        residual_sets.append(set(item["remaining_unexpected_timestamps"]))

    shared_residual = sorted(set.intersection(*residual_sets)) if residual_sets else []
    all_zero_unexpected = all(x["candidate_unexpected_count"] == 0 for x in per_symbol.values())
    all_zero_unclassified = all(x["unclassified_gap_bars"] == 0 for x in per_symbol.values())

    return {
        "contract_version": "RND0036-calendar-classification-review-v1",
        "task_id": "RND-0036",
        "authorized_interval": {
            "start_inclusive_utc": START_UTC,
            "end_exclusive_utc": END_UTC,
        },
        "symbols": list(SYMBOLS),
        "per_symbol": per_symbol,
        "shared_remaining_unexpected_timestamps": shared_residual,
        "all_candidate_unexpected_zero": all_zero_unexpected,
        "all_unclassified_gap_bars_zero": all_zero_unclassified,
        "candidate_1700_authority": "NONE",
        "documentary_calendar_authority": False,
        "calendar_modified": False,
        "canonical_evidence_modified": False,
        "synthetic_candles_allowed": False,
        "seal_authority": False,
        "strategy_evaluation": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "strategy_selection": False,
        "status": "STRUCTURAL_CLASSIFICATION_COMPLETE_REQUIRES_HUMAN_REVIEW",
    }


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise RND0036CalendarClassificationError("report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    value = review(args.root)
    output = _write_new(args.report, value)
    print("RND0036_CALENDAR_CLASSIFICATION: COMPLETE_REQUIRES_HUMAN_REVIEW")
    for symbol in SYMBOLS:
        item = value["per_symbol"][symbol]
        print(
            f"{symbol} baseline_unexpected={item['baseline_unexpected_count']} "
            f"candidate_unexpected={item['candidate_unexpected_count']} "
            f"explained_fraction={item['explained_original_unexpected_fraction']:.6f} "
            f"short_gap_bars={item['residual_short_gap_bars']} "
            f"closure_candidate_bars={item['closure_shaped_candidate_bars']} "
            f"unclassified_gap_bars={item['unclassified_gap_bars']}"
        )
    print(f"shared_remaining_unexpected={len(value['shared_remaining_unexpected_timestamps'])}")
    print("candidate_1700_authority=NONE")
    print("calendar_modified=FALSE")
    print("strategy_evaluation=FALSE")
    print("validation_open=FALSE")
    print("final_test_open=FALSE")
    print(f"report={output}")
    print(f"report_sha256={_sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
