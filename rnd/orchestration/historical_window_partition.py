#!/usr/bin/env python3
"""Deterministic, outcome-blind historical partition controls for RND-0029."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

M5_SECONDS = 300
VERSION = "RND-historical-window-partition-v0.1"
TASK_ID = "RND-0029"
BASE_COMMIT = "f342a3b2aa4bca021346df7915f8e9aaed2f5cab"
SYMBOLS = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]
START = "2015-01-01T00:00:00Z"
END = "2025-01-01T00:00:00Z"
FRACTIONS = (Decimal("0.60"), Decimal("0.20"), Decimal("0.20"))
STRUCTURAL_FIELDS = {
    "timestamp_utc", "complete", "provider", "instrument", "granularity",
    "raw_sha256", "canonical_rows_sha256", "row_count", "gap_ledger",
}
OUTCOME_FIELDS = {
    "signal", "position", "trade", "return", "pnl", "equity", "drawdown",
    "sharpe", "win_rate", "strategy_score",
}
ALLOWED_SEALED_OPERATIONS = {
    "VERIFY_IDENTITY", "VERIFY_SHA256", "VERIFY_PROVENANCE", "VERIFY_STRUCTURE",
    "VERIFY_COMPLETENESS", "VERIFY_TIMESTAMP_GRID", "VERIFY_STORAGE_INTEGRITY",
    "READ_BOUNDARY",
}
PROHIBITED_SEALED_OPERATIONS = {
    "GENERATE_SIGNALS", "SIMULATE_TRADES", "CALCULATE_RETURNS", "CALCULATE_PNL",
    "CALCULATE_EQUITY", "CALCULATE_DRAWDOWN", "CALCULATE_SHARPE",
    "CALCULATE_WIN_RATE", "COMPARE_PARAMETERS", "RANK_STRATEGIES",
    "SELECT_FEATURES", "SELECT_THRESHOLDS",
}


class PartitionError(ValueError):
    pass


def _utc(value, role):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PartitionError(f"{role}: UTC timestamp ending Z required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PartitionError(f"{role}: invalid timestamp") from exc
    if int(dt.timestamp()) % M5_SECONDS:
        raise PartitionError(f"{role}: M5 grid required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _snap_forward_m5(dt):
    seconds = int(dt.timestamp())
    snapped = ((seconds + M5_SECONDS - 1) // M5_SECONDS) * M5_SECONDS
    return datetime.fromtimestamp(snapped, timezone.utc)


def calculate_partitions(start_utc=START, end_utc=END):
    start = _utc(start_utc, "horizon.start")
    end = _utc(end_utc, "horizon.end")
    if start >= end:
        raise PartitionError("horizon: start must precede end")
    total_us = int((end - start).total_seconds() * 1_000_000)
    dev_us = int(Decimal(total_us) * FRACTIONS[0])
    val_end_us = int(Decimal(total_us) * (FRACTIONS[0] + FRACTIONS[1]))
    dev_end = _snap_forward_m5(start + timedelta(microseconds=dev_us))
    val_end = _snap_forward_m5(start + timedelta(microseconds=val_end_us))
    if not (start < dev_end < val_end < end):
        raise PartitionError("partition: insufficient horizon")
    return {
        "development": {"start_utc": _z(start), "end_utc": _z(dev_end)},
        "validation": {"start_utc": _z(dev_end), "end_utc": _z(val_end)},
        "reserved_final_test": {"start_utc": _z(val_end), "end_utc": _z(end)},
    }


def validate_declaration(value):
    required = {
        "contract_version", "task_id", "base_commit", "status", "symbols",
        "timeframe", "requested_horizon", "coverage_policy", "partition_rule",
        "partitions", "warmup_contract", "acquisition_binding", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PartitionError("declaration: exact fields required")
    if (
        value["contract_version"] != VERSION
        or value["task_id"] != TASK_ID
        or value["base_commit"] != BASE_COMMIT
        or value["status"] != "PREDECLARED"
    ):
        raise PartitionError("declaration: identity/status mismatch")
    if value["symbols"] != SYMBOLS or value["timeframe"] != "M5":
        raise PartitionError("declaration: universe/timeframe drift")
    if value["requested_horizon"] != {"start_utc": START, "end_utc": END}:
        raise PartitionError("declaration: horizon drift")

    coverage = value["coverage_policy"]
    expected_coverage = {
        "require_full_horizon_all_symbols": True,
        "common_coverage_rule": "EXACT_REQUESTED_HORIZON_OR_FAIL",
        "outcome_dependent_fallback_allowed": False,
        "structural_fields_allowed": sorted(STRUCTURAL_FIELDS),
        "outcome_fields_prohibited": sorted(OUTCOME_FIELDS),
    }
    normalized = dict(coverage) if isinstance(coverage, dict) else {}
    if isinstance(normalized.get("structural_fields_allowed"), list):
        normalized["structural_fields_allowed"] = sorted(normalized["structural_fields_allowed"])
    if isinstance(normalized.get("outcome_fields_prohibited"), list):
        normalized["outcome_fields_prohibited"] = sorted(normalized["outcome_fields_prohibited"])
    if normalized != expected_coverage:
        raise PartitionError("declaration: coverage policy drift")

    rule = value["partition_rule"]
    expected_rule = {
        "basis": "ELAPSED_UTC_TIME",
        "development_fraction": "0.60",
        "validation_fraction": "0.20",
        "reserved_final_test_fraction": "0.20",
        "boundary_snap": "FORWARD_TO_NEXT_M5_GRID",
        "candle_count_partitioning": False,
        "outcome_dependent_partitioning": False,
    }
    if rule != expected_rule:
        raise PartitionError("declaration: partition rule drift")

    expected = calculate_partitions()
    parts = value["partitions"]
    if not isinstance(parts, dict) or set(parts) != set(expected):
        raise PartitionError("declaration: partition set mismatch")
    for name in ("development", "validation"):
        if parts[name] != {
            **expected[name],
            "strategy_access": "ALLOWED_LATER_NOT_IN_RND_0029",
        }:
            raise PartitionError(f"declaration: {name} boundary/access drift")
    final = parts["reserved_final_test"]
    expected_final = {
        **expected["reserved_final_test"],
        "state": "SEALED_BOUNDARY_BOUND",
        "strategy_metrics_allowed": False,
        "signal_generation_allowed": False,
        "trade_simulation_allowed": False,
        "parameter_selection_allowed": False,
        "human_open_gate_required": True,
    }
    if final != expected_final:
        raise PartitionError("declaration: reserved final-test drift")

    warmup = value["warmup_contract"]
    expected_warmup = {
        "maximum_prior_bars": 50,
        "source_partition_only": True,
        "warmup_rows_may_initialize_state": True,
        "warmup_rows_may_generate_trades": False,
        "warmup_rows_may_contribute_returns": False,
        "final_test_rows_may_not_be_used_as_warmup_for_earlier_partitions": True,
    }
    if warmup != expected_warmup:
        raise PartitionError("declaration: warm-up authority drift")

    binding = value["acquisition_binding"]
    if binding != {
        "source_declaration": "rnd/research/OANDA_HISTORICAL_ACQUISITION_DECLARATION.json",
        "required_state": "ACQUISITION_READY",
        "start_utc": START,
        "end_utc": END,
    }:
        raise PartitionError("declaration: acquisition binding drift")

    authority = value["authority"]
    if authority != {
        "strategy_selection": False, "broker_writes": False,
        "automatic_merge": False, "automatic_promotion": False,
        "capital_authority": False, "human_review_required": True,
    }:
        raise PartitionError("declaration: authority escalation")
    return True


def validate_structural_coverage(coverage_by_symbol):
    if not isinstance(coverage_by_symbol, dict) or set(coverage_by_symbol) != set(SYMBOLS):
        raise PartitionError("coverage: exact four symbols required")
    for symbol in SYMBOLS:
        item = coverage_by_symbol[symbol]
        if not isinstance(item, dict):
            raise PartitionError(f"coverage.{symbol}: object required")
        if set(item) - STRUCTURAL_FIELDS:
            raise PartitionError(f"coverage.{symbol}: outcome/nonstructural field prohibited")
        if item.get("complete") is not True:
            raise PartitionError(f"coverage.{symbol}: complete evidence required")
        if item.get("granularity") != "M5":
            raise PartitionError(f"coverage.{symbol}: M5 required")
        if item.get("start_utc") != START or item.get("end_utc") != END:
            raise PartitionError(f"coverage.{symbol}: exact requested horizon required")
    return True


def validate_partition_rows(partition_name, timestamps):
    parts = calculate_partitions()
    if partition_name not in parts:
        raise PartitionError("partition rows: unknown partition")
    if not isinstance(timestamps, list) or not timestamps:
        raise PartitionError("partition rows: non-empty timestamp list required")
    start = _utc(parts[partition_name]["start_utc"], "partition.start")
    end = _utc(parts[partition_name]["end_utc"], "partition.end")
    parsed = [_utc(x, "partition row") for x in timestamps]
    if len(set(parsed)) != len(parsed) or parsed != sorted(parsed):
        raise PartitionError("partition rows: unique ordered timestamps required")
    if any(ts < start or ts >= end for ts in parsed):
        raise PartitionError("partition rows: cross-boundary row prohibited")
    return True


def validate_warmup(partition_name, warmup_timestamps, evaluation_timestamps):
    if partition_name not in {"validation", "reserved_final_test"}:
        raise PartitionError("warm-up: only later partitions may use prior rows")
    if not isinstance(warmup_timestamps, list) or len(warmup_timestamps) > 50:
        raise PartitionError("warm-up: maximum 50 prior bars")
    validate_partition_rows(partition_name, evaluation_timestamps)
    boundary = _utc(calculate_partitions()[partition_name]["start_utc"], "partition boundary")
    parsed = [_utc(x, "warm-up row") for x in warmup_timestamps]
    if len(set(parsed)) != len(parsed) or parsed != sorted(parsed):
        raise PartitionError("warm-up: unique ordered timestamps required")
    if any(ts >= boundary for ts in parsed):
        raise PartitionError("warm-up: rows must precede partition boundary")
    if partition_name == "validation":
        dev_start = _utc(calculate_partitions()["development"]["start_utc"], "development start")
        if any(ts < dev_start for ts in parsed):
            raise PartitionError("warm-up: outside preceding partition")
    if partition_name == "reserved_final_test":
        val_start = _utc(calculate_partitions()["validation"]["start_utc"], "validation start")
        if any(ts < val_start for ts in parsed):
            raise PartitionError("warm-up: final test may use validation rows only")
    return True


def validate_reserved_test_operation(operation):
    if not isinstance(operation, str) or not operation.strip():
        raise PartitionError("reserved test: operation required")
    if operation in PROHIBITED_SEALED_OPERATIONS:
        raise PartitionError("reserved test: strategy/performance access prohibited")
    if operation not in ALLOWED_SEALED_OPERATIONS:
        raise PartitionError("reserved test: undeclared operation prohibited")
    return True
