#!/usr/bin/env python3
"""Outcome-blind cross-pair structural evidence for RND-0032."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from historical_calendar_evidence import evaluate_1700_hypothesis

TASK_ID = "RND-0032"
YEAR = 2015
REFERENCE = "AUDUSD"
NEW_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
ALL_SYMBOLS = (REFERENCE,) + NEW_SYMBOLS
START_UTC = "2015-01-01T00:00:00Z"
END_UTC = "2016-01-01T00:00:00Z"
OUTCOME_KEYS = {
    "signal", "position", "trade", "return", "pnl", "equity", "drawdown",
    "sharpe", "win_rate", "strategy_score", "parameter", "feature",
}


class CrossPairEvidenceError(ValueError):
    pass


def _json(path):
    return json.loads(Path(path).read_text())


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _reject_outcomes(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in OUTCOME_KEYS:
                raise CrossPairEvidenceError("strategy outcome field prohibited")
            _reject_outcomes(child)
    elif isinstance(value, list):
        for child in value:
            _reject_outcomes(child)


def load_structural_shard(path, expected_symbol):
    """Load and bind a verified quarantine shard, extracting timestamps only."""
    if expected_symbol not in ALL_SYMBOLS:
        raise CrossPairEvidenceError("unsupported RND-0032 symbol")
    root = Path(path)
    manifest = _json(root / "quarantine_manifest.json")
    ledger = _json(root / "discrepancy_ledger.json")
    rows = _json(root / "canonical_rows.json")
    schedule = _json(root / "standard_schedule.json")

    identity = {
        "contract_version": "RND-oanda-quarantine-shard-v0.1",
        "task_id": "RND-0030",
        "symbol": expected_symbol,
        "year": YEAR,
        "start_utc": START_UTC,
        "end_utc": END_UTC,
        "provider": "OANDA",
        "environment": "PRACTICE",
        "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "complete_candles_only": True,
        "seal_allowed": False,
        "account_identity_recorded": False,
        "credentials_recorded": False,
    }
    for key, expected in identity.items():
        if manifest.get(key) != expected:
            raise CrossPairEvidenceError(f"{expected_symbol}: manifest {key} drift")

    file_bindings = {
        "canonical_rows_file_sha256": "canonical_rows.json",
        "standard_schedule_file_sha256": "standard_schedule.json",
        "discrepancy_ledger_file_sha256": "discrepancy_ledger.json",
    }
    for key, filename in file_bindings.items():
        if manifest.get(key) != _sha256_file(root / filename):
            raise CrossPairEvidenceError(f"{expected_symbol}: {filename} hash mismatch")

    actual = []
    for row in rows:
        if not isinstance(row, dict) or "timestamp_utc" not in row:
            raise CrossPairEvidenceError(f"{expected_symbol}: malformed canonical row")
        actual.append(row["timestamp_utc"])

    if manifest.get("row_count") != len(actual):
        raise CrossPairEvidenceError(f"{expected_symbol}: row count mismatch")
    if manifest.get("expected_standard_session_count") != len(schedule):
        raise CrossPairEvidenceError(f"{expected_symbol}: schedule count mismatch")
    if manifest.get("missing_count") != ledger.get("missing_count"):
        raise CrossPairEvidenceError(f"{expected_symbol}: missing count mismatch")
    if manifest.get("unexpected_count") != ledger.get("unexpected_count"):
        raise CrossPairEvidenceError(f"{expected_symbol}: unexpected count mismatch")

    result = evaluate_1700_hypothesis(actual, schedule, START_UTC, END_UTC)
    return {
        "symbol": expected_symbol,
        "year": YEAR,
        "manifest_status": manifest.get("status"),
        "row_count": len(actual),
        "raw_page_count": manifest.get("raw_page_count"),
        "raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
        "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
        "standard_schedule_sha256": manifest.get("standard_schedule_sha256"),
        "baseline_missing_timestamps": list(ledger.get("missing_timestamps", [])),
        "baseline_unexpected_timestamps": list(ledger.get("unexpected_timestamps", [])),
        "candidate": result,
    }


def _intersection(values):
    sets = [set(v) for v in values]
    return sorted(set.intersection(*sets)) if sets else []


def compare_structural_shards(shards):
    if not isinstance(shards, list) or len(shards) != 4:
        raise CrossPairEvidenceError("exactly four 2015 structural shards required")
    by_symbol = {item.get("symbol"): item for item in shards if isinstance(item, dict)}
    if set(by_symbol) != set(ALL_SYMBOLS):
        raise CrossPairEvidenceError("exact AUDUSD/EURUSD/GBPUSD/USDJPY set required")

    candidate_missing = {
        s: by_symbol[s]["candidate"]["missing_run_classes"] for s in ALL_SYMBOLS
    }
    candidate_unexpected = {
        s: by_symbol[s]["candidate"]["remaining_unexpected_timestamps"] for s in ALL_SYMBOLS
    }
    baseline_unexpected = {
        s: by_symbol[s]["baseline_unexpected_timestamps"] for s in ALL_SYMBOLS
    }

    shared_baseline_unexpected = _intersection(baseline_unexpected.values())
    shared_candidate_unexpected = _intersection(candidate_unexpected.values())

    baseline_missing = {
        s: by_symbol[s]["baseline_missing_timestamps"] for s in ALL_SYMBOLS
    }
    shared_baseline_missing = _intersection(baseline_missing.values())

    per_symbol = {}
    for symbol in ALL_SYMBOLS:
        cand = by_symbol[symbol]["candidate"]
        classes = candidate_missing[symbol]
        per_symbol[symbol] = {
            "row_count": by_symbol[symbol]["row_count"],
            "raw_page_count": by_symbol[symbol]["raw_page_count"],
            "raw_bundle_sha256": by_symbol[symbol]["raw_bundle_sha256"],
            "canonical_rows_sha256": by_symbol[symbol]["canonical_rows_sha256"],
            "standard_schedule_sha256": by_symbol[symbol]["standard_schedule_sha256"],
            "baseline_missing_count": cand["baseline_missing_count"],
            "baseline_unexpected_count": cand["baseline_unexpected_count"],
            "candidate_missing_count": cand["candidate_missing_count"],
            "candidate_unexpected_count": cand["candidate_unexpected_count"],
            "explained_original_unexpected_count": cand["explained_original_unexpected_count"],
            "explained_original_unexpected_fraction": cand["explained_original_unexpected_fraction"],
            "remaining_unexpected_timestamps": cand["remaining_unexpected_timestamps"],
            "residual_short_gap_bars": sum(x["bars"] for x in classes["residual_short_gap"]),
            "closure_shaped_candidate_bars": sum(x["bars"] for x in classes["closure_shaped_candidate"]),
            "unclassified_gap_bars": sum(x["bars"] for x in classes["unclassified"]),
        }

    result = {
        "contract_version": "RND-0032-cross-pair-structural-v0.1",
        "task_id": TASK_ID,
        "year": YEAR,
        "symbols": list(ALL_SYMBOLS),
        "candidate_authority": "NONE",
        "calendar_modified": False,
        "strategy_evaluation": False,
        "documentary_calendar_authority": False,
        "per_symbol": per_symbol,
        "shared_baseline_missing_timestamps": shared_baseline_missing,
        "shared_baseline_unexpected_timestamps": shared_baseline_unexpected,
        "shared_candidate_unexpected_timestamps": shared_candidate_unexpected,
        "audusd_2015_08_28_1705_recurrence": {
            s: "2015-08-28T21:05:00Z" in candidate_unexpected[s] for s in ALL_SYMBOLS
        },
    }
    _reject_outcomes(result)
    return result
