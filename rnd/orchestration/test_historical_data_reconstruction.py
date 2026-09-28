#!/usr/bin/env python3

import hashlib
import json
import unittest
from pathlib import Path

from historical_data_reconstruction import (
    EXPECTED_M005_BEHAVIOUR,
    HistoricalDataError,
    canonical_rows_sha256,
    validate_acquisition_plan,
    validate_candle_rows,
    validate_m005_reconstruction,
    validate_reserved_test_operation,
    validate_snapshot_evidence,
    validate_snapshot_manifest,
    verify_snapshot_bytes,
)


def manifest(raw=b"immutable snapshot"):
    fixture_rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
    return {
        "contract_version": "RND-historical-snapshot-v0.1",
        "snapshot_id": "OANDA-AUDUSD-M5-example",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_rows_sha256": canonical_rows_sha256(fixture_rows),
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
        "mid_open": 1.0001,
        "mid_high": 1.0011,
        "mid_low": 0.9991,
        "mid_close": 1.0006,
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

    def test_bid_ask_without_mid_snapshot_is_rejected(self):
        value = manifest()
        value["price_components"] = ["bid", "ask"]
        with self.assertRaisesRegex(HistoricalDataError, "bid/ask/mid"):
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

    def test_provider_decimal_strings_are_valid_candle_prices(self):
        value = row("2020-01-01T00:00:00Z")
        for key in tuple(value):
            if key.endswith(("_open", "_high", "_low", "_close")):
                value[key] = format(value[key], ".5f")
        self.assertTrue(validate_candle_rows([value]))

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

    def test_snapshot_row_count_is_bound_to_rows(self):
        raw = b"original"
        value = manifest(raw)
        value["row_count"] = 3
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
        expected = ["2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z"]
        with self.assertRaisesRegex(HistoricalDataError, "row_count"):
            validate_snapshot_evidence(value, raw, rows, expected)

    def test_snapshot_rows_must_stay_inside_declared_coverage(self):
        raw = b"original"
        value = manifest(raw)
        value["start_utc"] = "2020-01-01T00:05:00Z"
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
        expected = ["2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z"]
        with self.assertRaisesRegex(HistoricalDataError, "outside declared coverage"):
            validate_snapshot_evidence(value, raw, rows, expected)

    def test_snapshot_evidence_requires_expected_market_schedule(self):
        raw = b"original"
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
        with self.assertRaisesRegex(HistoricalDataError, "market-calendar"):
            validate_snapshot_evidence(manifest(raw), raw, rows)

    def test_parsed_row_hash_mismatch_is_rejected(self):
        raw = b"original"
        value = manifest(raw)
        rows = [row("2020-01-01T00:00:00Z"), row("2020-01-01T00:05:00Z")]
        rows[1]["ask_close"] = 1.0008
        expected = ["2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z"]
        with self.assertRaisesRegex(HistoricalDataError, "parsed-row hash"):
            validate_snapshot_evidence(value, raw, rows, expected)

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

    def test_reserved_boundary_cannot_be_silently_bound(self):
        value = declaration()
        value["reserved_test"]["start_utc"] = "2024-01-01T00:00:00Z"
        with self.assertRaisesRegex(HistoricalDataError, "seal mismatch"):
            validate_m005_reconstruction(value)

    def test_m005_output_contract_cannot_be_weakened(self):
        value = declaration()
        value["output_contract"]["mark_to_market_equity"] = False
        with self.assertRaisesRegex(HistoricalDataError, "output contract"):
            validate_m005_reconstruction(value)

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
