#!/usr/bin/env python3
"""Pure-local historical-data and fixed-M005 guards for RND-0027.

No network access, file writes, strategy search, reserved-test scoring, broker
access, promotion authority or capital authority.
"""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime


SNAPSHOT_VERSION = "RND-historical-snapshot-v0.1"
M005_VERSION = "RND-m005-reconstruction-v0.1"
ACQUISITION_VERSION = "RND-historical-acquisition-plan-v0.1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_M005_BEHAVIOUR = {
    "pairs": ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"],
    "timeframe": "M5",
    "fast_ma": 20,
    "slow_ma": 50,
    "vol_window": 12,
    "vol_ddof": 0,
    "vol_threshold": 0.0005,
    "sessions_utc": {
        "AUDUSD": [11, 14],
        "EURUSD": [11, 13],
        "GBPUSD": [11, 13],
        "USDJPY": [11, 13],
    },
    "signal_delay_bars": 1,
    "minimum_hold_bars": 3,
}
EXPECTED_RESERVED_TEST = {
    "state": "SEALED",
    "strategy_metrics_allowed": False,
    "signal_generation_allowed": False,
    "trade_simulation_allowed": False,
    "parameter_selection_allowed": False,
    "human_open_gate_required": True,
}
EXPECTED_EXECUTION = {
    "bid_ask_required": True,
    "explicit_entries_exits": True,
    "overlapping_positions": True,
    "mark_to_market": True,
    "currency_exposure": True,
    "synthetic_return_clipping": False,
    "future_bar_access": False,
}
EXPECTED_AUTHORITY = {
    "strategy_selection": False,
    "broker_writes": False,
    "automatic_merge": False,
    "automatic_promotion": False,
    "capital_authority": False,
    "human_review_required": True,
}
ALLOWED_SEALED_OPERATIONS = {
    "VERIFY_IDENTITY",
    "VERIFY_SHA256",
    "VERIFY_PROVENANCE",
    "VERIFY_STRUCTURE",
    "VERIFY_COMPLETENESS",
    "VERIFY_TIMESTAMP_GRID",
    "VERIFY_STORAGE_INTEGRITY",
}
PROHIBITED_SEALED_OPERATIONS = {
    "GENERATE_SIGNALS",
    "SIMULATE_TRADES",
    "CALCULATE_RETURNS",
    "CALCULATE_PNL",
    "CALCULATE_EQUITY",
    "CALCULATE_DRAWDOWN",
    "CALCULATE_SHARPE",
    "CALCULATE_WIN_RATE",
    "COMPARE_PARAMETERS",
    "RANK_STRATEGIES",
    "SELECT_FEATURES",
    "SELECT_THRESHOLDS",
}

SNAPSHOT_FIELDS = {
    "contract_version",
    "snapshot_id",
    "sha256",
    "provider",
    "source_instrument",
    "symbol",
    "timeframe",
    "price_components",
    "start_utc",
    "end_utc",
    "complete",
    "complete_candles_only",
    "timestamp_grid_seconds",
    "row_count",
    "provenance",
    "acquired_utc",
    "immutable",
}
CANDLE_FIELDS = {
    "timestamp_utc",
    "complete",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
}


class HistoricalDataError(ValueError):
    pass


def _exact(value, fields, role):
    if not isinstance(value, dict) or set(value) != fields:
        raise HistoricalDataError(f"{role}: exact fields required")


def _text(value, role):
    if not isinstance(value, str) or not value.strip():
        raise HistoricalDataError(f"{role}: expected non-empty string")
    return value.strip()


def _utc(value, role):
    value = _text(value, role)
    if not value.endswith("Z"):
        raise HistoricalDataError(f"{role}: expected UTC timestamp ending Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HistoricalDataError(f"{role}: invalid UTC timestamp") from exc


def validate_snapshot_manifest(value):
    _exact(value, SNAPSHOT_FIELDS, "snapshot")
    if value["contract_version"] != SNAPSHOT_VERSION:
        raise HistoricalDataError("snapshot: unsupported contract version")
    for field in ("snapshot_id", "provider", "source_instrument", "symbol", "provenance"):
        _text(value[field], "snapshot." + field)
    if not SHA256_RE.fullmatch(_text(value["sha256"], "snapshot.sha256")):
        raise HistoricalDataError("snapshot.sha256: invalid")
    if value["timeframe"] != "M5":
        raise HistoricalDataError("snapshot.timeframe: M5 required")
    components = value["price_components"]
    if (
        not isinstance(components, list)
        or len(set(components)) != len(components)
        or not {"bid", "ask"}.issubset(set(components))
        or not all(x in {"bid", "ask", "mid"} for x in components)
    ):
        raise HistoricalDataError("snapshot: execution-grade bid/ask required")
    start = _utc(value["start_utc"], "snapshot.start_utc")
    end = _utc(value["end_utc"], "snapshot.end_utc")
    if start >= end:
        raise HistoricalDataError("snapshot: start must precede end")
    _utc(value["acquired_utc"], "snapshot.acquired_utc")
    if value["complete"] is not True or value["complete_candles_only"] is not True:
        raise HistoricalDataError("snapshot: complete candles required")
    if value["timestamp_grid_seconds"] != 300:
        raise HistoricalDataError("snapshot: M5 timestamp grid must be 300 seconds")
    if not isinstance(value["row_count"], int) or isinstance(value["row_count"], bool) or value["row_count"] < 1:
        raise HistoricalDataError("snapshot.row_count: positive integer required")
    if value["immutable"] is not True:
        raise HistoricalDataError("snapshot: immutable must be true")
    return True


def verify_snapshot_bytes(manifest, raw_bytes):
    validate_snapshot_manifest(manifest)
    if not isinstance(raw_bytes, bytes):
        raise HistoricalDataError("raw_bytes: bytes required")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != manifest["sha256"]:
        raise HistoricalDataError("snapshot mutation/hash mismatch")
    return True


def _price(value, role):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise HistoricalDataError(f"{role}: positive finite price required")
    return float(value)


def validate_candle_rows(rows, expected_timestamps=None):
    if not isinstance(rows, list) or not rows:
        raise HistoricalDataError("rows: non-empty list required")
    parsed = []
    for i, row in enumerate(rows):
        _exact(row, CANDLE_FIELDS, f"rows[{i}]")
        ts = _utc(row["timestamp_utc"], f"rows[{i}].timestamp_utc")
        if int(ts.timestamp()) % 300 != 0:
            raise HistoricalDataError(f"rows[{i}]: timestamp off M5 grid")
        if row["complete"] is not True:
            raise HistoricalDataError(f"rows[{i}]: incomplete candle")
        prices = {}
        for component in ("bid", "ask"):
            for field in ("open", "high", "low", "close"):
                key = f"{component}_{field}"
                prices[key] = _price(row[key], f"rows[{i}].{key}")
            if prices[f"{component}_high"] < max(
                prices[f"{component}_open"],
                prices[f"{component}_close"],
                prices[f"{component}_low"],
            ):
                raise HistoricalDataError(f"rows[{i}]: invalid {component} high")
            if prices[f"{component}_low"] > min(
                prices[f"{component}_open"],
                prices[f"{component}_close"],
                prices[f"{component}_high"],
            ):
                raise HistoricalDataError(f"rows[{i}]: invalid {component} low")
        parsed.append(ts)

    if len(set(parsed)) != len(parsed):
        raise HistoricalDataError("rows: duplicate timestamps")
    if parsed != sorted(parsed):
        raise HistoricalDataError("rows: timestamps out of order")

    if expected_timestamps is not None:
        if not isinstance(expected_timestamps, list) or not expected_timestamps:
            raise HistoricalDataError("expected_timestamps: non-empty list required")
        expected = [_utc(x, "expected timestamp") for x in expected_timestamps]
        if len(set(expected)) != len(expected) or expected != sorted(expected):
            raise HistoricalDataError("expected_timestamps: invalid ordering/duplicates")
        if parsed != expected:
            raise HistoricalDataError("rows: missing or unexpected M5 candles")
    return True


def validate_reserved_test_operation(operation):
    operation = _text(operation, "reserved operation")
    if operation in PROHIBITED_SEALED_OPERATIONS:
        raise HistoricalDataError("reserved test: strategy/performance access prohibited")
    if operation not in ALLOWED_SEALED_OPERATIONS:
        raise HistoricalDataError("reserved test: undeclared operation prohibited")
    return True


def validate_m005_reconstruction(value):
    required = {
        "contract_version", "task_id", "base_commit", "status",
        "fixed_behaviour", "search_space", "declared_trial_count",
        "reserved_test", "execution_contract", "authority",
    }
    _exact(value, required, "M005 reconstruction")
    if value["contract_version"] != M005_VERSION or value["task_id"] != "RND-0027":
        raise HistoricalDataError("M005 reconstruction: identity mismatch")
    if value["fixed_behaviour"] != EXPECTED_M005_BEHAVIOUR:
        raise HistoricalDataError("M005 reconstruction: frozen behaviour drift")
    if value["search_space"] != {} or value["declared_trial_count"] != 1:
        raise HistoricalDataError("M005 reconstruction: search/tuning authority prohibited")
    if value["status"] != "BLOCKED_DATA_NOT_BOUND":
        raise HistoricalDataError("M005 reconstruction: must remain blocked in RND-0027")
    if value["reserved_test"] != EXPECTED_RESERVED_TEST:
        raise HistoricalDataError("M005 reconstruction: reserved-test seal mismatch")
    if value["execution_contract"] != EXPECTED_EXECUTION:
        raise HistoricalDataError("M005 reconstruction: execution contract mismatch")
    if value["authority"] != EXPECTED_AUTHORITY:
        raise HistoricalDataError("M005 reconstruction: authority escalation")
    return True


def validate_acquisition_plan(value):
    required = {
        "contract_version", "task_id", "base_commit", "status",
        "preferred_source", "required_snapshots", "acquisition_rules", "next_gate",
    }
    _exact(value, required, "acquisition plan")
    if value["contract_version"] != ACQUISITION_VERSION or value["task_id"] != "RND-0027":
        raise HistoricalDataError("acquisition plan: identity mismatch")
    if value["status"] != "BLOCKED_DATA_NOT_BOUND":
        raise HistoricalDataError("acquisition plan: must remain blocked")
    source = value["preferred_source"]
    source_fields = {
        "provider", "mode", "timeframe", "required_price_components",
        "complete_candles_only", "broker_order_endpoints_allowed",
        "credentials_committed_to_repository",
    }
    _exact(source, source_fields, "preferred_source")
    if source["mode"] != "READ_ONLY_HISTORICAL_CANDLES" or source["timeframe"] != "M5":
        raise HistoricalDataError("preferred_source: read-only M5 required")
    if not {"bid", "ask"}.issubset(set(source["required_price_components"])):
        raise HistoricalDataError("preferred_source: bid/ask required")
    if source["complete_candles_only"] is not True:
        raise HistoricalDataError("preferred_source: complete candles required")
    if source["broker_order_endpoints_allowed"] is not False:
        raise HistoricalDataError("preferred_source: order endpoints prohibited")
    if source["credentials_committed_to_repository"] is not False:
        raise HistoricalDataError("preferred_source: credentials must not be committed")
    snapshots = value["required_snapshots"]
    expected = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]
    if not isinstance(snapshots, list) or [x.get("symbol") for x in snapshots if isinstance(x, dict)] != expected:
        raise HistoricalDataError("required_snapshots: exact four-pair order required")
    for item in snapshots:
        if set(item) != {"symbol", "status"} or item["status"] != "MISSING":
            raise HistoricalDataError("required_snapshots: absent data must remain MISSING")
    rules = value["acquisition_rules"]
    if not isinstance(rules, list) or not rules or not all(isinstance(x, str) and x.strip() for x in rules):
        raise HistoricalDataError("acquisition_rules: non-empty rules required")
    _text(value["next_gate"], "next_gate")
    return True
