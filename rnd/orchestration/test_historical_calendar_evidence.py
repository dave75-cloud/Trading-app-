#!/usr/bin/env python3

import copy
import json
import unittest
from pathlib import Path

from historical_calendar_evidence import (
    HistoricalCalendarError,
    classify_missing_runs,
    discrepancy,
    evaluate_1700_hypothesis,
    historical_1700_candidate_schedule,
    record_sha256,
    validate_pilot_record,
)

ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "research" / "RND0031_PILOT_EVIDENCE_RECORD.json").read_text())


class HistoricalCalendarEvidenceTests(unittest.TestCase):
    def test_repository_pilot_record_is_valid(self):
        self.assertTrue(validate_pilot_record(record()))

    def test_record_digest_is_deterministic(self):
        self.assertEqual(record_sha256(record()), record_sha256(copy.deepcopy(record())))

    def test_candidate_adds_monday_1700_new_york_without_removing_standard(self):
        standard = ["2015-01-05T21:55:00Z", "2015-01-05T22:05:00Z"]
        candidate = historical_1700_candidate_schedule(
            standard, "2015-01-05T21:55:00Z", "2015-01-05T22:10:00Z"
        )
        self.assertEqual(
            ["2015-01-05T21:55:00Z", "2015-01-05T22:00:00Z", "2015-01-05T22:05:00Z"],
            candidate,
        )

    def test_candidate_adds_sunday_1700_new_york(self):
        candidate = historical_1700_candidate_schedule(
            [], "2015-01-04T21:55:00Z", "2015-01-04T22:10:00Z"
        )
        self.assertEqual(["2015-01-04T22:00:00Z"], candidate)

    def test_candidate_does_not_add_friday_1700(self):
        candidate = historical_1700_candidate_schedule(
            [], "2015-01-02T21:55:00Z", "2015-01-02T22:10:00Z"
        )
        self.assertEqual([], candidate)

    def test_candidate_is_dst_aware(self):
        winter = historical_1700_candidate_schedule(
            [], "2015-01-05T21:55:00Z", "2015-01-05T22:05:00Z"
        )
        summer = historical_1700_candidate_schedule(
            [], "2015-06-01T20:55:00Z", "2015-06-01T21:05:00Z"
        )
        self.assertEqual(["2015-01-05T22:00:00Z"], winter)
        self.assertEqual(["2015-06-01T21:00:00Z"], summer)

    def test_candidate_never_removes_authoritative_timestamp(self):
        standard = ["2015-01-05T21:55:00Z", "2015-01-05T22:05:00Z"]
        candidate = historical_1700_candidate_schedule(
            standard, "2015-01-05T21:55:00Z", "2015-01-05T22:10:00Z"
        )
        self.assertTrue(set(standard).issubset(set(candidate)))

    def test_synthetic_1700_hypothesis_explains_only_matching_unexpected(self):
        standard = ["2015-01-05T21:55:00Z", "2015-01-05T22:05:00Z"]
        actual = [
            "2015-01-05T21:55:00Z",
            "2015-01-05T22:00:00Z",
            "2015-01-05T22:05:00Z",
        ]
        result = evaluate_1700_hypothesis(
            actual, standard, "2015-01-05T21:55:00Z", "2015-01-05T22:10:00Z"
        )
        self.assertEqual(1, result["baseline_unexpected_count"])
        self.assertEqual(0, result["candidate_unexpected_count"])
        self.assertEqual("NONE", result["candidate_authority"])
        self.assertFalse(result["calendar_modified"])

    def test_non_1700_unexpected_is_preserved(self):
        standard = ["2015-08-28T20:55:00Z"]
        actual = ["2015-08-28T20:55:00Z", "2015-08-28T21:05:00Z"]
        result = evaluate_1700_hypothesis(
            actual, standard, "2015-08-28T20:55:00Z", "2015-08-28T21:10:00Z"
        )
        self.assertEqual(["2015-08-28T21:05:00Z"], result["remaining_unexpected_timestamps"])

    def test_short_missing_runs_are_residual_not_holidays(self):
        missing = [
            "2015-05-18T00:00:00Z",
            "2015-05-18T00:05:00Z",
            "2015-05-18T00:20:00Z",
        ]
        classes = classify_missing_runs(missing)
        self.assertEqual(2, len(classes["residual_short_gap"]))
        self.assertEqual([], classes["closure_shaped_candidate"])

    def test_large_run_is_only_closure_shaped_candidate(self):
        missing = [f"2015-01-01T00:{m:02d}:00Z" for m in range(0, 60, 5)]
        classes = classify_missing_runs(missing)
        self.assertEqual(1, len(classes["closure_shaped_candidate"]))
        self.assertEqual([], classes["residual_short_gap"])

    def test_mid_sized_run_stays_unclassified(self):
        missing = [f"2015-01-01T00:{m:02d}:00Z" for m in range(0, 30, 5)]
        classes = classify_missing_runs(missing)
        self.assertEqual(1, len(classes["unclassified"]))

    def test_discrepancy_rejects_duplicate_actual(self):
        with self.assertRaisesRegex(HistoricalCalendarError, "unique ordered"):
            discrepancy(
                ["2015-01-01T00:00:00Z", "2015-01-01T00:00:00Z"],
                ["2015-01-01T00:00:00Z"],
            )

    def test_record_rejects_strategy_outcome_field(self):
        value = record()
        value["candidate_1700_falsification"]["pnl"] = 1
        with self.assertRaisesRegex(HistoricalCalendarError, "strategy outcome"):
            validate_pilot_record(value)

    def test_record_rejects_calendar_authority(self):
        value = record()
        value["candidate_1700_falsification"]["candidate_authority"] = "PROMOTE"
        with self.assertRaisesRegex(HistoricalCalendarError, "candidate authority"):
            validate_pilot_record(value)

    def test_record_rejects_zero_gap_requirement(self):
        value = record()
        value["future_acceptance_policy"]["zero_unexplained_gap_required"] = True
        with self.assertRaisesRegex(HistoricalCalendarError, "acceptance policy"):
            validate_pilot_record(value)

    def test_record_rejects_synthetic_candles(self):
        value = record()
        value["future_acceptance_policy"]["synthetic_candles_allowed"] = True
        with self.assertRaisesRegex(HistoricalCalendarError, "acceptance policy"):
            validate_pilot_record(value)

    def test_record_rejects_bad_evidence_hash(self):
        value = record()
        value["integrity"]["canonical_rows_sha256"] = "abc"
        with self.assertRaisesRegex(HistoricalCalendarError, "invalid canonical_rows_sha256"):
            validate_pilot_record(value)


if __name__ == "__main__":
    unittest.main()
