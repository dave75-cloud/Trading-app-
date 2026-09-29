#!/usr/bin/env python3

import json
from pathlib import Path
import unittest

from cross_pair_2015_evidence import (
    ALL_SYMBOLS,
    CrossPairEvidenceError,
    compare_structural_shards,
)


def shard(symbol, missing=None, unexpected=None):
    missing = missing or []
    unexpected = unexpected or []
    return {
        "symbol": symbol,
        "year": 2015,
        "row_count": 10,
        "raw_page_count": 1,
        "raw_bundle_sha256": symbol.lower().ljust(64, "0"),
        "canonical_rows_sha256": symbol.lower().ljust(64, "1"),
        "standard_schedule_sha256": "a" * 64,
        "baseline_missing_timestamps": missing,
        "baseline_unexpected_timestamps": unexpected,
        "candidate": {
            "candidate_authority": "NONE",
            "calendar_modified": False,
            "strategy_evaluation": False,
            "baseline_missing_count": len(missing),
            "baseline_unexpected_count": len(unexpected),
            "candidate_missing_count": len(missing),
            "candidate_unexpected_count": len(unexpected),
            "explained_original_unexpected_count": 0,
            "explained_original_unexpected_fraction": 0.0,
            "remaining_unexpected_timestamps": unexpected,
            "missing_run_classes": {
                "residual_short_gap": [],
                "closure_shaped_candidate": [],
                "unclassified": [],
            },
        },
    }


class CrossPair2015EvidenceTests(unittest.TestCase):
    def test_exact_four_pair_set_required(self):
        values = [shard(s) for s in ALL_SYMBOLS]
        self.assertEqual(list(ALL_SYMBOLS), compare_structural_shards(values)["symbols"])

    def test_missing_pair_rejected(self):
        with self.assertRaisesRegex(CrossPairEvidenceError, "exactly four"):
            compare_structural_shards([shard("AUDUSD")])

    def test_duplicate_pair_rejected(self):
        values = [shard("AUDUSD"), shard("AUDUSD"), shard("EURUSD"), shard("GBPUSD")]
        with self.assertRaisesRegex(CrossPairEvidenceError, "exact AUDUSD"):
            compare_structural_shards(values)

    def test_shared_missing_is_intersection_not_union(self):
        a = "2015-01-01T00:00:00Z"
        b = "2015-01-01T00:05:00Z"
        values = [
            shard("AUDUSD", [a, b]),
            shard("EURUSD", [a]),
            shard("GBPUSD", [a]),
            shard("USDJPY", [a]),
        ]
        self.assertEqual([a], compare_structural_shards(values)["shared_baseline_missing_timestamps"])

    def test_shared_unexpected_is_explicit(self):
        t = "2015-01-05T22:00:00Z"
        values = [shard(s, unexpected=[t]) for s in ALL_SYMBOLS]
        result = compare_structural_shards(values)
        self.assertEqual([t], result["shared_baseline_unexpected_timestamps"])

    def test_audusd_anomaly_recurrence_is_per_pair(self):
        t = "2015-08-28T21:05:00Z"
        values = [
            shard("AUDUSD", unexpected=[t]),
            shard("EURUSD"),
            shard("GBPUSD", unexpected=[t]),
            shard("USDJPY"),
        ]
        recurrence = compare_structural_shards(values)["audusd_2015_08_28_1705_recurrence"]
        self.assertEqual(
            {"AUDUSD": True, "EURUSD": False, "GBPUSD": True, "USDJPY": False},
            recurrence,
        )

    def test_authority_remains_none(self):
        result = compare_structural_shards([shard(s) for s in ALL_SYMBOLS])
        self.assertEqual("NONE", result["candidate_authority"])
        self.assertFalse(result["calendar_modified"])
        self.assertFalse(result["strategy_evaluation"])
        self.assertFalse(result["documentary_calendar_authority"])

    def test_gap_classes_are_counted_without_reclassification(self):
        values = [shard(s) for s in ALL_SYMBOLS]
        values[0]["candidate"]["missing_run_classes"] = {
            "residual_short_gap": [{"bars": 2, "start_utc": "x", "end_utc": "y"}],
            "closure_shaped_candidate": [{"bars": 20, "start_utc": "x", "end_utc": "y"}],
            "unclassified": [{"bars": 5, "start_utc": "x", "end_utc": "y"}],
        }
        p = compare_structural_shards(values)["per_symbol"]["AUDUSD"]
        self.assertEqual(2, p["residual_short_gap_bars"])
        self.assertEqual(20, p["closure_shaped_candidate_bars"])
        self.assertEqual(5, p["unclassified_gap_bars"])


class CrossPair2015EvidenceRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        record_path = (
            Path(__file__).resolve().parents[1]
            / "research"
            / "RND0032_CROSS_PAIR_2015_EVIDENCE_RECORD.json"
        )
        cls.record = json.loads(record_path.read_text(encoding="utf-8"))

    def test_bound_evidence_record_preserves_authority_boundary(self):
        record = self.record
        self.assertEqual(
            "8d594b9c0bbbdcd771acfa2be7fc032b827c8e246265459a5448a3f24cc436fe",
            record["verification"]["report_sha256"],
        )
        self.assertEqual(
            ["2015-08-28T21:05:00Z"],
            record["cross_pair"]["shared_candidate_unexpected_timestamps"],
        )
        self.assertEqual(
            {"AUDUSD": True, "EURUSD": True, "GBPUSD": True, "USDJPY": True},
            record["cross_pair"]["audusd_2015_08_28_1705_recurrence"],
        )
        self.assertEqual(
            {648},
            {
                values["closure_shaped_candidate_bars"]
                for values in record["per_symbol"].values()
            },
        )
        authority = record["authority"]
        self.assertEqual("NONE", authority["candidate_authority"])
        self.assertFalse(authority["calendar_modified"])
        self.assertFalse(authority["documentary_calendar_authority"])
        self.assertFalse(authority["strategy_evaluation"])
        self.assertFalse(authority["seal_authority"])
        self.assertFalse(authority["expansion_authority"])
        self.assertTrue(authority["human_review_required"])


if __name__ == "__main__":
    unittest.main()
