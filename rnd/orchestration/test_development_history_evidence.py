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


class DevelopmentHistoryEvidenceRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        record_path = (
            Path(__file__).resolve().parents[1]
            / "research"
            / "RND0033_DEVELOPMENT_HISTORY_EVIDENCE_RECORD.json"
        )
        cls.record = json.loads(record_path.read_text(encoding="utf-8"))

    def test_bound_report_identity_and_scope(self):
        record = self.record
        self.assertEqual(
            "148f3809c34df0311349819ef49080a4c0343978f2da3b53bc3498f0c9e6283b",
            record["verification"]["report_sha256"],
        )
        self.assertEqual(16, record["verification"]["integrity_shards"])
        self.assertEqual([2016, 2017, 2018, 2019], record["evidence_scope"]["years"])
        self.assertEqual(16, record["evidence_scope"]["shard_count"])

    def test_cross_year_candidate_signature_is_bound(self):
        per_year = self.record["per_year"]
        self.assertEqual(
            {"2016": 0, "2017": 2, "2018": 0, "2019": 0},
            {year: value["shared_candidate_unexpected_count"]
             for year, value in per_year.items()},
        )
        self.assertEqual(
            ["2017-10-06T21:05:00Z", "2017-10-20T21:10:00Z"],
            per_year["2017"]["shared_candidate_unexpected_timestamps"],
        )

    def test_pair_specific_residuals_remain_explicit(self):
        y2019 = self.record["per_year"]["2019"]["per_symbol"]
        self.assertEqual(
            {"AUDUSD": 0, "EURUSD": 1, "GBPUSD": 5, "USDJPY": 16},
            {symbol: value["candidate_unexpected_count"]
             for symbol, value in y2019.items()},
        )
        self.assertEqual(1429, y2019["AUDUSD"]["residual_short_gap_bars"])
        self.assertEqual(196, y2019["AUDUSD"]["unclassified_gap_bars"])

    def test_bound_evidence_preserves_authority_boundary(self):
        authority = self.record["authority"]
        self.assertEqual("NONE", authority["candidate_authority"])
        self.assertFalse(authority["calendar_modified"])
        self.assertFalse(authority["documentary_calendar_authority"])
        self.assertFalse(authority["strategy_evaluation"])
        self.assertFalse(authority["regime_promotion_authority"])
        self.assertFalse(authority["seal_authority"])
        self.assertFalse(authority["expansion_authority"])
        self.assertTrue(authority["human_review_required"])


if __name__ == "__main__":
    unittest.main()
