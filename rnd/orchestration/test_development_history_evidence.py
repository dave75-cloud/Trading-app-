#!/usr/bin/env python3

import unittest

from development_history_evidence import (
    SYMBOLS, YEARS, DevelopmentHistoryEvidenceError, compare_development_history,
)


def shard(symbol, year, missing=None, unexpected=None, remaining=None):
    missing = missing or []
    unexpected = unexpected or []
    remaining = unexpected if remaining is None else remaining
    return {
        "symbol": symbol,
        "year": year,
        "row_count": 10,
        "raw_page_count": 1,
        "raw_bundle_sha256": (symbol.lower() + str(year)).ljust(64, "0")[:64],
        "canonical_rows_sha256": (symbol.lower() + str(year)).ljust(64, "1")[:64],
        "standard_schedule_sha256": "a" * 64,
        "baseline_missing_timestamps": missing,
        "baseline_unexpected_timestamps": unexpected,
        "candidate": {
            "baseline_missing_count": len(missing),
            "baseline_unexpected_count": len(unexpected),
            "candidate_missing_count": len(missing),
            "candidate_unexpected_count": len(remaining),
            "explained_original_unexpected_count": len(unexpected) - len(remaining),
            "explained_original_unexpected_fraction": (
                (len(unexpected) - len(remaining)) / len(unexpected)
                if unexpected else 0.0
            ),
            "remaining_unexpected_timestamps": remaining,
            "missing_run_classes": {
                "residual_short_gap": [],
                "closure_shaped_candidate": [],
                "unclassified": [],
            },
        },
    }


def matrix():
    return [shard(symbol, year) for symbol in SYMBOLS for year in YEARS]


class DevelopmentHistoryEvidenceTests(unittest.TestCase):
    def test_exact_sixteen_shards_required(self):
        result = compare_development_history(matrix())
        self.assertEqual(list(YEARS), result["years"])
        self.assertEqual(list(SYMBOLS), result["symbols"])

    def test_missing_shard_rejected(self):
        with self.assertRaisesRegex(DevelopmentHistoryEvidenceError, "sixteen"):
            compare_development_history(matrix()[:-1])

    def test_duplicate_shard_rejected(self):
        values = matrix()
        values[-1] = values[0]
        with self.assertRaises(DevelopmentHistoryEvidenceError):
            compare_development_history(values)

    def test_shared_missing_is_year_scoped_intersection(self):
        t = "2016-01-01T00:00:00Z"
        values = matrix()
        for item in values:
            if item["year"] == 2016:
                item["baseline_missing_timestamps"] = [t]
                item["candidate"]["baseline_missing_count"] = 1
                item["candidate"]["candidate_missing_count"] = 1
        result = compare_development_history(values)
        self.assertEqual(1, result["per_year"]["2016"]["shared_baseline_missing_count"])
        self.assertEqual(0, result["per_year"]["2017"]["shared_baseline_missing_count"])

    def test_candidate_unexpected_signature_preserves_shared_timestamp(self):
        t = "2018-08-31T21:05:00Z"
        values = matrix()
        for item in values:
            if item["year"] == 2018:
                item["baseline_unexpected_timestamps"] = [t]
                item["candidate"]["baseline_unexpected_count"] = 1
                item["candidate"]["candidate_unexpected_count"] = 1
                item["candidate"]["remaining_unexpected_timestamps"] = [t]
        result = compare_development_history(values)
        sig = result["cross_year_structural_signatures"]["2018"]
        self.assertEqual([t], sig["shared_candidate_unexpected_timestamps"])
        self.assertEqual(1, sig["shared_candidate_unexpected_count"])

    def test_gap_classes_are_counted_without_reclassification(self):
        values = matrix()
        target = next(x for x in values if x["symbol"] == "AUDUSD" and x["year"] == 2019)
        target["candidate"]["missing_run_classes"] = {
            "residual_short_gap": [{"bars": 2}],
            "closure_shaped_candidate": [{"bars": 20}],
            "unclassified": [{"bars": 5}],
        }
        p = compare_development_history(values)["per_year"]["2019"]["per_symbol"]["AUDUSD"]
        self.assertEqual(2, p["residual_short_gap_bars"])
        self.assertEqual(20, p["closure_shaped_candidate_bars"])
        self.assertEqual(5, p["unclassified_gap_bars"])

    def test_authority_remains_none(self):
        result = compare_development_history(matrix())
        self.assertEqual("NONE", result["candidate_authority"])
        self.assertFalse(result["calendar_modified"])
        self.assertFalse(result["strategy_evaluation"])
        self.assertFalse(result["documentary_calendar_authority"])
        self.assertFalse(result["regime_promotion_authority"])


if __name__ == "__main__":
    unittest.main()
