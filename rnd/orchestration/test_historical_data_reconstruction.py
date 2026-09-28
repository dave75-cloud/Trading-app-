#!/usr/bin/env python3

import hashlib
import json
import unittest
from pathlib import Path

from historical_data_reconstruction import (
    EXPECTED_M005_BEHAVIOUR,
    HistoricalDataError,
    validate_acquisition_plan,
    validate_candle_rows,
    validate_m005_reconstruction,
    validate_reserved_test_operation,
    validate_snapshot_manifest,
    verify_snapshot_bytes,
)


def manifest(raw=b"immutable snapshot"):
    return {
        "contract_version": "RND-historical-snapshot-v0.1",
        "snapshot_id": "OANDA-AUDUSD-M5-example",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "provider": "OANDA",
        "source_instrument": "AUD_USD",
        "symbol": "AUDUSD",
        "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "start_utc": "2020-01-01T00:00:00Z",
        "end_utc": "2020-01-02T00:00:00Z",
        "complete": True,
        "complete_candles_only": True,
        "timestamp_grid_seconds": 300,
        "row_count": 2,
        "provenance": "Synthetic fixture for contract tests only.",
        "acquired_utc": "2026-09-28T00:00:00Z",
        "immutable": True,
    }


def row(ts, complete=True):
    return {
        "timestamp_utc": ts,
        "complete": complete,
        "bid_open": 1.0000,
        "bid_high": 1.0010,
        "bid_low": 0.9990,
        "bid_close": 1.0005,
        "ask_open": 1.0002,
        "ask_high": 1.0012,
        "ask_low": 0.9992,
        "ask_close": 1.0007,
    }


def declaration():
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "research" / "M005_RECONSTRUCTION_DECLARATION.json").read_text()
    )


class HistoricalDataReconstructionTests(unittest.TestCase):
    def test_valid_snapshot_manifest(self):
        self.assertTrue(validate_snapshot_manifest(manifest()))

    def test_snapshot_mutation_is_rejected(self):
        value = manifest(b"original")
        with self.assertRaisesRegex(HistoricalDataError, "mutation"):
            verify_snapshot_bytes(value, b"changed")

    def test_exact_snapshot_bytes_are_accepted(self):
        raw = b"original"
        self.assertTrue(verify_snapshot_bytes(manifest(raw), raw))

    def test_mid_only_snapshot_is_rejected(self):
        value = manifest()
        value["price_components"] = ["mid"]
        with self.assertRaisesRegex(HistoricalDataError, "bid/ask"):
            validate_snapshot_manifest(value)

    def test_incomplete_snapshot_is_rejected(self):
        value = manifest()
        value["complete"] = False
        with self.assertRaisesRegex(HistoricalDataError, "complete"):
            validate_snapshot_manifest(value)

    def test_wrong_timeframe_is_rejected(self):
        value = manifest()
        value["timeframe"] = "H1"
        with self.assertRaisesRegex(HistoricalDataError, "M5"):
            validate_snapshot_manifest(value)

    def test_valid_candle_rows(self):
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
        self.assertTrue(validate_candle_rows(rows))

    def test_duplicate_timestamps_are_rejected(self):
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:00:00Z")]
        with self.assertRaisesRegex(HistoricalDataError, "duplicate"):
            validate_candle_rows(rows)

    def test_out_of_order_timestamps_are_rejected(self):
        rows = [row("2020-01-01T00:05:00Z"), row("2020-01-01T00:00:00Z")]
        with self.assertRaisesRegex(HistoricalDataError, "out of order"):
            validate_candle_rows(rows)

    def test_incomplete_candle_is_rejected(self):
        with self.assertRaisesRegex(HistoricalDataError, "incomplete candle"):
            validate_candle_rows([row("2020-01-01T00:00:00Z", complete=False)])

    def test_off_grid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(HistoricalDataError, "off M5 grid"):
            validate_candle_rows([row("2020-01-01T00:01:00Z")])

    def test_expected_timestamp_gap_is_rejected(self):
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:10:00Z")]
        expected = [
            "2020-01-01T00:00:00Z",
            "2020-01-01T00:05:00Z",
            "2020-01-01T00:10:00Z",
        ]
        with self.assertRaisesRegex(HistoricalDataError, "missing or unexpected"):
            validate_candle_rows(rows, expected)

    def test_reserved_integrity_operation_is_allowed(self):
        self.assertTrue(validate_reserved_test_operation("VERIFY_SHA256"))

    def test_reserved_performance_metric_is_blocked(self):
        with self.assertRaisesRegex(HistoricalDataError, "prohibited"):
            validate_reserved_test_operation("CALCULATE_PNL")

    def test_reserved_signal_generation_is_blocked(self):
        with self.assertRaisesRegex(HistoricalDataError, "prohibited"):
            validate_reserved_test_operation("GENERATE_SIGNALS")

    def test_repository_m005_declaration_is_valid(self):
        self.assertTrue(validate_m005_reconstruction(declaration()))

    def test_m005_behaviour_drift_is_rejected(self):
        value = declaration()
        value["fixed_behaviour"]["fast_ma"] = 21
        with self.assertRaisesRegex(HistoricalDataError, "behaviour drift"):
            validate_m005_reconstruction(value)

    def test_m005_search_space_is_rejected(self):
        value = declaration()
        value["search_space"] = {"fast_ma": [20, 21]}
        value["declared_trial_count"] = 2
        with self.assertRaisesRegex(HistoricalDataError, "search/tuning"):
            validate_m005_reconstruction(value)

    def test_m005_authority_escalation_is_rejected(self):
        value = declaration()
        value["authority"]["strategy_selection"] = True
        with self.assertRaisesRegex(HistoricalDataError, "authority escalation"):
            validate_m005_reconstruction(value)

    def test_repository_acquisition_plan_is_valid_and_blocked(self):
        root = Path(__file__).resolve().parents[1]
        value = json.loads(
            (root / "research" / "HISTORICAL_DATA_ACQUISITION_PLAN.json").read_text()
        )
        self.assertTrue(validate_acquisition_plan(value))


if __name__ == "__main__":
    unittest.main()
