#!/usr/bin/env python3

import copy
import json
import unittest
from pathlib import Path

from historical_window_partition import (
    END,
    START,
    PartitionError,
    calculate_partitions,
    validate_declaration,
    validate_partition_rows,
    validate_reserved_test_operation,
    validate_structural_coverage,
    validate_warmup,
)

ROOT = Path(__file__).resolve().parents[1]


def declaration():
    return json.loads(
        (ROOT / "research" / "HISTORICAL_WINDOW_PARTITION_DECLARATION.json").read_text()
    )


def structural_item(symbol):
    instruments = {
        "AUDUSD": "AUD_USD",
        "EURUSD": "EUR_USD",
        "GBPUSD": "GBP_USD",
        "USDJPY": "USD_JPY",
    }
    return {
        "start_utc": START,
        "end_utc": END,
        "complete": True,
        "provider": "OANDA",
        "instrument": instruments[symbol],
        "granularity": "M5",
        "raw_sha256": "a" * 64,
        "canonical_rows_sha256": "b" * 64,
        "row_count": 1,
        "gap_ledger": {"complete": True},
    }


class HistoricalWindowPartitionTests(unittest.TestCase):
    def test_repository_declaration_is_valid(self):
        self.assertTrue(validate_declaration(declaration()))

    def test_boundaries_are_deterministic_from_elapsed_time(self):
        parts = calculate_partitions()
        self.assertEqual(
            {"start_utc": "2015-01-01T00:00:00Z", "end_utc": "2020-12-31T19:15:00Z"},
            parts["development"],
        )
        self.assertEqual(
            {"start_utc": "2020-12-31T19:15:00Z", "end_utc": "2023-01-01T09:40:00Z"},
            parts["validation"],
        )
        self.assertEqual(
            {"start_utc": "2023-01-01T09:40:00Z", "end_utc": "2025-01-01T00:00:00Z"},
            parts["reserved_final_test"],
        )

    def test_horizon_drift_is_rejected(self):
        value = declaration()
        value["requested_horizon"]["start_utc"] = "2016-01-01T00:00:00Z"
        with self.assertRaisesRegex(PartitionError, "horizon drift"):
            validate_declaration(value)

    def test_outcome_dependent_partition_rule_is_rejected(self):
        value = declaration()
        value["partition_rule"]["outcome_dependent_partitioning"] = True
        with self.assertRaisesRegex(PartitionError, "partition rule drift"):
            validate_declaration(value)

    def test_candle_count_partition_rule_is_rejected(self):
        value = declaration()
        value["partition_rule"]["candle_count_partitioning"] = True
        with self.assertRaisesRegex(PartitionError, "partition rule drift"):
            validate_declaration(value)

    def test_boundary_movement_is_rejected(self):
        value = declaration()
        value["partitions"]["reserved_final_test"]["start_utc"] = "2023-01-02T00:00:00Z"
        with self.assertRaisesRegex(PartitionError, "reserved final-test drift"):
            validate_declaration(value)

    def test_unsealing_final_test_is_rejected(self):
        value = declaration()
        value["partitions"]["reserved_final_test"]["signal_generation_allowed"] = True
        with self.assertRaisesRegex(PartitionError, "reserved final-test drift"):
            validate_declaration(value)

    def test_authority_escalation_is_rejected(self):
        value = declaration()
        value["authority"]["broker_writes"] = True
        with self.assertRaisesRegex(PartitionError, "authority escalation"):
            validate_declaration(value)

    def test_exact_full_structural_coverage_is_accepted(self):
        coverage = {symbol: structural_item(symbol) for symbol in ("AUDUSD","EURUSD","GBPUSD","USDJPY")}
        self.assertTrue(validate_structural_coverage(coverage))

    def test_missing_symbol_is_rejected(self):
        coverage = {symbol: structural_item(symbol) for symbol in ("AUDUSD","EURUSD","GBPUSD")}
        with self.assertRaisesRegex(PartitionError, "exact four symbols"):
            validate_structural_coverage(coverage)

    def test_shorter_coverage_is_rejected_not_intersected(self):
        coverage = {symbol: structural_item(symbol) for symbol in ("AUDUSD","EURUSD","GBPUSD","USDJPY")}
        coverage["GBPUSD"]["start_utc"] = "2016-01-01T00:00:00Z"
        with self.assertRaisesRegex(PartitionError, "exact requested horizon"):
            validate_structural_coverage(coverage)

    def test_outcome_field_in_structural_coverage_is_rejected(self):
        coverage = {symbol: structural_item(symbol) for symbol in ("AUDUSD","EURUSD","GBPUSD","USDJPY")}
        coverage["AUDUSD"]["return"] = 0.10
        with self.assertRaisesRegex(PartitionError, "outcome/nonstructural"):
            validate_structural_coverage(coverage)

    def test_incomplete_structural_evidence_is_rejected(self):
        coverage = {symbol: structural_item(symbol) for symbol in ("AUDUSD","EURUSD","GBPUSD","USDJPY")}
        coverage["USDJPY"]["complete"] = False
        with self.assertRaisesRegex(PartitionError, "complete evidence"):
            validate_structural_coverage(coverage)

    def test_partition_rows_cannot_cross_boundary(self):
        with self.assertRaisesRegex(PartitionError, "cross-boundary"):
            validate_partition_rows(
                "validation",
                ["2020-12-31T19:10:00Z", "2020-12-31T19:15:00Z"],
            )

    def test_partition_rows_must_be_unique_and_ordered(self):
        with self.assertRaisesRegex(PartitionError, "unique ordered"):
            validate_partition_rows(
                "validation",
                ["2020-12-31T19:20:00Z", "2020-12-31T19:20:00Z"],
            )

    def test_valid_partition_rows_are_accepted(self):
        self.assertTrue(
            validate_partition_rows(
                "validation",
                ["2020-12-31T19:15:00Z", "2020-12-31T19:20:00Z"],
            )
        )

    def test_warmup_is_limited_to_50_prior_bars(self):
        warmup = [f"2020-12-31T{h:02d}:{m:02d}:00Z" for h in range(14,19) for m in range(0,60,5)]
        warmup = warmup[-51:]
        with self.assertRaisesRegex(PartitionError, "maximum 50"):
            validate_warmup(
                "validation", warmup, ["2020-12-31T19:15:00Z"], warmup
            )

    def test_warmup_must_be_exact_tail_of_preceding_partition(self):
        tail = ["2020-12-31T19:00:00Z", "2020-12-31T19:05:00Z", "2020-12-31T19:10:00Z"]
        with self.assertRaisesRegex(PartitionError, "exact trailing bars"):
            validate_warmup(
                "validation",
                ["2020-12-31T19:00:00Z", "2020-12-31T19:10:00Z"],
                ["2020-12-31T19:15:00Z"],
                tail,
            )

    def test_validation_warmup_from_exact_development_tail_is_accepted(self):
        tail = ["2020-12-31T19:00:00Z", "2020-12-31T19:05:00Z", "2020-12-31T19:10:00Z"]
        self.assertTrue(
            validate_warmup(
                "validation", tail[-2:], ["2020-12-31T19:15:00Z"], tail
            )
        )

    def test_final_test_warmup_cannot_reach_back_into_development(self):
        tail = ["2020-12-31T19:10:00Z", "2023-01-01T09:35:00Z"]
        with self.assertRaisesRegex(PartitionError, "validation rows only"):
            validate_warmup(
                "reserved_final_test", tail, ["2023-01-01T09:40:00Z"], tail
            )

    def test_reserved_structural_operation_is_allowed(self):
        self.assertTrue(validate_reserved_test_operation("VERIFY_SHA256"))

    def test_reserved_boundary_read_is_allowed(self):
        self.assertTrue(validate_reserved_test_operation("READ_BOUNDARY"))

    def test_reserved_signal_generation_is_blocked(self):
        with self.assertRaisesRegex(PartitionError, "strategy/performance"):
            validate_reserved_test_operation("GENERATE_SIGNALS")

    def test_reserved_performance_metric_is_blocked(self):
        with self.assertRaisesRegex(PartitionError, "strategy/performance"):
            validate_reserved_test_operation("CALCULATE_SHARPE")

    def test_undeclared_reserved_operation_is_blocked(self):
        with self.assertRaisesRegex(PartitionError, "undeclared"):
            validate_reserved_test_operation("EXPORT_PRICES_FOR_RESEARCH")

    def test_warmup_contract_cannot_be_weakened(self):
        value = declaration()
        value["warmup_contract"]["warmup_rows_may_contribute_returns"] = True
        with self.assertRaisesRegex(PartitionError, "warm-up authority drift"):
            validate_declaration(value)


if __name__ == "__main__":
    unittest.main()
