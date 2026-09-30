#!/usr/bin/env python3
"""Outcome-blind 2016-2019 development-history evidence for RND-0033."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from historical_calendar_evidence import evaluate_1700_hypothesis

TASK_ID = "RND-0033"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
YEARS = (2016, 2017, 2018, 2019)
OUTCOME_KEYS = {
    "signal", "position", "trade", "return", "pnl", "equity", "drawdown",
    "sharpe", "win_rate", "strategy_score", "parameter", "feature",
}


class DevelopmentHistoryEvidenceError(ValueError):
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
                raise DevelopmentHistoryEvidenceError("strategy outcome field prohibited")
            _reject_outcomes(child)
    elif isinstance(value, list):
        for child in value:
            _reject_outcomes(child)


def _bounds(year):
    return f"{year}-01-01T00:00:00Z", f"{year + 1}-01-01T00:00:00Z"


def load_structural_shard(path, expected_symbol, expected_year):
    if expected_symbol not in SYMBOLS or expected_year not in YEARS:
        raise DevelopmentHistoryEvidenceError("unsupported RND-0033 shard")
    root = Path(path)
    manifest = _json(root / "quarantine_manifest.json")
    ledger = _json(root / "discrepancy_ledger.json")
    rows = _json(root / "canonical_rows.json")
    schedule = _json(root / "standard_schedule.json")
    start_utc, end_utc = _bounds(expected_year)

    identity = {
        "contract_version": "RND-oanda-quarantine-shard-v0.1",
        "task_id": "RND-0030",
        "symbol": expected_symbol,
        "year": expected_year,
        "start_utc": start_utc,
        "end_utc": end_utc,
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
            raise DevelopmentHistoryEvidenceError(
                f"{expected_symbol}/{expected_year}: manifest {key} drift"
            )

    for key, filename in {
        "canonical_rows_file_sha256": "canonical_rows.json",
        "standard_schedule_file_sha256": "standard_schedule.json",
        "discrepancy_ledger_file_sha256": "discrepancy_ledger.json",
    }.items():
        if manifest.get(key) != _sha256_file(root / filename):
            raise DevelopmentHistoryEvidenceError(
                f"{expected_symbol}/{expected_year}: {filename} hash mismatch"
            )

    actual = []
    for row in rows:
        if not isinstance(row, dict) or "timestamp_utc" not in row:
            raise DevelopmentHistoryEvidenceError("malformed canonical row")
        actual.append(row["timestamp_utc"])

    if manifest.get("row_count") != len(actual):
        raise DevelopmentHistoryEvidenceError("row count mismatch")
    if manifest.get("expected_standard_session_count") != len(schedule):
        raise DevelopmentHistoryEvidenceError("schedule count mismatch")
    if manifest.get("missing_count") != ledger.get("missing_count"):
        raise DevelopmentHistoryEvidenceError("missing count mismatch")
    if manifest.get("unexpected_count") != ledger.get("unexpected_count"):
        raise DevelopmentHistoryEvidenceError("unexpected count mismatch")

    candidate = evaluate_1700_hypothesis(actual, schedule, start_utc, end_utc)
    return {
        "symbol": expected_symbol,
        "year": expected_year,
        "row_count": len(actual),
        "raw_page_count": manifest.get("raw_page_count"),
        "raw_bundle_sha256": manifest.get("aggregate_raw_bundle_sha256"),
        "canonical_rows_sha256": manifest.get("canonical_rows_sha256"),
        "standard_schedule_sha256": manifest.get("standard_schedule_sha256"),
        "baseline_missing_timestamps": list(ledger.get("missing_timestamps", [])),
        "baseline_unexpected_timestamps": list(ledger.get("unexpected_timestamps", [])),
        "candidate": candidate,
    }


def _intersection(values):
    sets = [set(v) for v in values]
    return sorted(set.intersection(*sets)) if sets else []


def _gap_bars(classes, key):
    return sum(item["bars"] for item in classes[key])


def compare_development_history(shards):
    if not isinstance(shards, list) or len(shards) != 16:
        raise DevelopmentHistoryEvidenceError("exactly sixteen structural shards required")
    by_key = {}
    for item in shards:
        if not isinstance(item, dict):
            raise DevelopmentHistoryEvidenceError("shard mapping required")
        key = (item.get("symbol"), item.get("year"))
        if key in by_key:
            raise DevelopmentHistoryEvidenceError("duplicate shard")
        by_key[key] = item
    expected = {(symbol, year) for symbol in SYMBOLS for year in YEARS}
    if set(by_key) != expected:
        raise DevelopmentHistoryEvidenceError("exact four-pair 2016-2019 matrix required")

    per_year = {}
    for year in YEARS:
        values = {symbol: by_key[(symbol, year)] for symbol in SYMBOLS}
        per_symbol = {}
        for symbol, item in values.items():
            cand = item["candidate"]
            classes = cand["missing_run_classes"]
            per_symbol[symbol] = {
                "row_count": item["row_count"],
                "raw_page_count": item["raw_page_count"],
                "raw_bundle_sha256": item["raw_bundle_sha256"],
                "canonical_rows_sha256": item["canonical_rows_sha256"],
                "standard_schedule_sha256": item["standard_schedule_sha256"],
                "baseline_missing_count": cand["baseline_missing_count"],
                "baseline_unexpected_count": cand["baseline_unexpected_count"],
                "candidate_missing_count": cand["candidate_missing_count"],
                "candidate_unexpected_count": cand["candidate_unexpected_count"],
                "explained_original_unexpected_count": cand["explained_original_unexpected_count"],
                "explained_original_unexpected_fraction": cand["explained_original_unexpected_fraction"],
                "remaining_unexpected_timestamps": cand["remaining_unexpected_timestamps"],
                "residual_short_gap_bars": _gap_bars(classes, "residual_short_gap"),
                "closure_shaped_candidate_bars": _gap_bars(classes, "closure_shaped_candidate"),
                "unclassified_gap_bars": _gap_bars(classes, "unclassified"),
            }

        shared_missing = _intersection(
            item["baseline_missing_timestamps"] for item in values.values()
        )
        shared_unexpected = _intersection(
            item["baseline_unexpected_timestamps"] for item in values.values()
        )
        shared_candidate_unexpected = _intersection(
            item["candidate"]["remaining_unexpected_timestamps"]
            for item in values.values()
        )
        per_year[str(year)] = {
            "per_symbol": per_symbol,
            "shared_baseline_missing_count": len(shared_missing),
            "shared_baseline_unexpected_count": len(shared_unexpected),
            "shared_candidate_unexpected_count": len(shared_candidate_unexpected),
            "shared_candidate_unexpected_timestamps": shared_candidate_unexpected,
            "all_pairs_candidate_unexpected_counts": {
                symbol: per_symbol[symbol]["candidate_unexpected_count"]
                for symbol in SYMBOLS
            },
        }

    signatures = {}
    for year in YEARS:
        y = per_year[str(year)]
        signatures[str(year)] = {
            "shared_candidate_unexpected_count": y["shared_candidate_unexpected_count"],
            "shared_candidate_unexpected_timestamps": y["shared_candidate_unexpected_timestamps"],
            "per_symbol_candidate_unexpected_counts": y["all_pairs_candidate_unexpected_counts"],
            "per_symbol_closure_shaped_candidate_bars": {
                symbol: y["per_symbol"][symbol]["closure_shaped_candidate_bars"]
                for symbol in SYMBOLS
            },
        }

    result = {
        "contract_version": "RND-0033-development-history-structural-v0.1",
        "task_id": TASK_ID,
        "symbols": list(SYMBOLS),
        "years": list(YEARS),
        "candidate_authority": "NONE",
        "calendar_modified": False,
        "strategy_evaluation": False,
        "documentary_calendar_authority": False,
        "per_year": per_year,
        "cross_year_structural_signatures": signatures,
        "regime_promotion_authority": False,
    }
    _reject_outcomes(result)
    return result
