#!/usr/bin/env python3

import copy
import json
import tempfile
import unittest
from pathlib import Path

from oanda_market_calendar import (
    CalendarError,
    apply_exception_evidence,
    build_discrepancy_ledger,
    is_standard_session_start,
    schedule_sha256,
    standard_session_schedule,
    validate_declaration,
    validate_exception_evidence,
    validate_quarantine_target,
    year_shards,
)

ROOT = Path(__file__).resolve().parents[1]


def declaration():
    return json.loads(
        (ROOT / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json").read_text()
    )


def exception_evidence():
    return {
        "contract_version": "RND-calendar-exception-evidence-v0.1",
        "task_id": "RND-0030",
        "horizon": {
            "start_utc": "2015-01-01T00:00:00Z",
            "end_utc": "2025-01-01T00:00:00Z",
        },
        "exceptions": [
            {
                "exception_id": "EX-1",
                "start_utc": "2024-01-01T00:00:00Z",
                "end_utc": "2024-01-01T01:00:00Z",
                "reason": "officially documented holiday closure",
                "source_kind": "OFFICIAL_OANDA_TRADING_HOURS_NOTICE",
                "source_locator": "https://www.oanda.com/example-official-notice",
                "source_sha256": "a" * 64,
            }
        ],
        "authority": {
            "strategy_outcomes_allowed": False,
            "returned_candles_can_authorize_exception": False,
            "human_review_required": True,
        },
    }


class OandaMarketCalendarTests(unittest.TestCase):
    def test_repository_declaration_is_valid(self):
        self.assertTrue(validate_declaration(declaration()))

    def test_saturday_is_closed(self):
        self.assertFalse(is_standard_session_start("2024-06-01T12:00:00Z"))

    def test_sunday_before_new_york_open_is_closed(self):
        self.assertFalse(is_standard_session_start("2024-06-02T21:00:00Z"))

    def test_sunday_new_york_1705_is_open(self):
        self.assertTrue(is_standard_session_start("2024-06-02T21:05:00Z"))

    def test_friday_new_york_1655_is_last_expected_start(self):
        self.assertTrue(is_standard_session_start("2024-06-07T20:55:00Z"))

    def test_friday_new_york_1700_is_closed(self):
        self.assertFalse(is_standard_session_start("2024-06-07T21:00:00Z"))

    def test_monday_daily_1700_break_is_closed(self):
        self.assertFalse(is_standard_session_start("2024-06-03T21:00:00Z"))

    def test_monday_daily_1705_reopen_is_expected(self):
        self.assertTrue(is_standard_session_start("2024-06-03T21:05:00Z"))

    def test_spring_dst_moves_sunday_open_from_2205_to_2105_utc(self):
        self.assertTrue(is_standard_session_start("2024-03-03T22:05:00Z"))
        self.assertFalse(is_standard_session_start("2024-03-10T20:05:00Z"))
        self.assertTrue(is_standard_session_start("2024-03-10T21:05:00Z"))

    def test_autumn_dst_moves_sunday_open_from_2105_to_2205_utc(self):
        self.assertTrue(is_standard_session_start("2024-10-27T21:05:00Z"))
        self.assertFalse(is_standard_session_start("2024-11-03T21:05:00Z"))
        self.assertTrue(is_standard_session_start("2024-11-03T22:05:00Z"))

    def test_one_ordinary_session_day_has_287_m5_starts(self):
        rows = standard_session_schedule(
            "2024-06-03T21:05:00Z", "2024-06-04T21:05:00Z"
        )
        self.assertEqual(287, len(rows))
        self.assertEqual("2024-06-03T21:05:00Z", rows[0])
        self.assertEqual("2024-06-04T20:55:00Z", rows[-1])

    def test_schedule_is_unique_and_ordered(self):
        rows = standard_session_schedule(
            "2024-06-01T00:00:00Z", "2024-06-10T00:00:00Z"
        )
        self.assertEqual(rows, sorted(rows))
        self.assertEqual(len(rows), len(set(rows)))

    def test_schedule_rejects_off_grid_boundary(self):
        with self.assertRaisesRegex(CalendarError, "M5 grid"):
            standard_session_schedule(
                "2024-06-01T00:01:00Z", "2024-06-02T00:00:00Z"
            )

    def test_schedule_rejects_reverse_range(self):
        with self.assertRaisesRegex(CalendarError, "start must precede"):
            standard_session_schedule(
                "2024-06-02T00:00:00Z", "2024-06-01T00:00:00Z"
            )

    def test_year_shards_cover_exact_predeclared_horizon(self):
        shards = year_shards()
        self.assertEqual(10, len(shards))
        self.assertEqual("2015-01-01T00:00:00Z", shards[0]["start_utc"])
        self.assertEqual("2025-01-01T00:00:00Z", shards[-1]["end_utc"])

    def test_schedule_digest_is_deterministic_and_order_bound(self):
        rows = ["2024-06-03T21:05:00Z", "2024-06-03T21:10:00Z"]
        self.assertEqual(schedule_sha256(rows), schedule_sha256(copy.deepcopy(rows)))
        with self.assertRaisesRegex(CalendarError, "unique ordered"):
            schedule_sha256(list(reversed(rows)))

    def test_exact_match_discrepancy_is_resolved(self):
        rows = ["2024-06-03T21:05:00Z", "2024-06-03T21:10:00Z"]
        ledger = build_discrepancy_ledger(rows, rows)
        self.assertTrue(ledger["resolved"])
        self.assertTrue(ledger["seal_allowed"])

    def test_missing_timestamp_blocks_seal(self):
        expected = ["2024-06-03T21:05:00Z", "2024-06-03T21:10:00Z"]
        ledger = build_discrepancy_ledger(expected[:1], expected)
        self.assertEqual(["2024-06-03T21:10:00Z"], ledger["missing_timestamps"])
        self.assertFalse(ledger["seal_allowed"])

    def test_unexpected_timestamp_blocks_seal(self):
        expected = ["2024-06-03T21:05:00Z"]
        actual = expected + ["2024-06-03T21:10:00Z"]
        ledger = build_discrepancy_ledger(actual, expected)
        self.assertEqual(["2024-06-03T21:10:00Z"], ledger["unexpected_timestamps"])
        self.assertFalse(ledger["seal_allowed"])

    def test_actual_timestamp_duplicates_are_rejected(self):
        with self.assertRaisesRegex(CalendarError, "unique ordered"):
            build_discrepancy_ledger(
                ["2024-06-03T21:05:00Z", "2024-06-03T21:05:00Z"],
                ["2024-06-03T21:05:00Z"],
            )

    def test_exception_evidence_requires_official_oanda_source(self):
        value = exception_evidence()
        value["exceptions"][0]["source_kind"] = "RETURNED_CANDLE_GAP"
        with self.assertRaisesRegex(CalendarError, "official OANDA source"):
            validate_exception_evidence(value)

    def test_exception_evidence_requires_official_oanda_locator(self):
        value = exception_evidence()
        value["exceptions"][0]["source_locator"] = "https://example.com/calendar"
        with self.assertRaisesRegex(CalendarError, "official OANDA locator"):
            validate_exception_evidence(value)

    def test_exception_evidence_cannot_authorize_returned_candles(self):
        value = exception_evidence()
        value["authority"]["returned_candles_can_authorize_exception"] = True
        with self.assertRaisesRegex(CalendarError, "authority drift"):
            validate_exception_evidence(value)

    def test_exception_evidence_cannot_allow_strategy_outcomes(self):
        value = exception_evidence()
        value["authority"]["strategy_outcomes_allowed"] = True
        with self.assertRaisesRegex(CalendarError, "authority drift"):
            validate_exception_evidence(value)

    def test_overlapping_exception_intervals_are_rejected(self):
        value = exception_evidence()
        second = copy.deepcopy(value["exceptions"][0])
        second["exception_id"] = "EX-2"
        second["start_utc"] = "2024-01-01T00:30:00Z"
        second["end_utc"] = "2024-01-01T02:00:00Z"
        value["exceptions"].append(second)
        with self.assertRaisesRegex(CalendarError, "overlapping"):
            validate_exception_evidence(value)

    def test_exception_interval_must_be_m5_aligned(self):
        value = exception_evidence()
        value["exceptions"][0]["start_utc"] = "2024-01-01T00:01:00Z"
        with self.assertRaisesRegex(CalendarError, "M5 grid"):
            validate_exception_evidence(value)

    def test_exception_source_digest_is_required(self):
        value = exception_evidence()
        value["exceptions"][0]["source_sha256"] = "abc"
        with self.assertRaisesRegex(CalendarError, "SHA-256"):
            validate_exception_evidence(value)

    def test_apply_exception_removes_only_independently_declared_interval(self):
        expected = [
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:05:00Z",
            "2024-01-01T01:00:00Z",
        ]
        result = apply_exception_evidence(expected, exception_evidence())
        self.assertEqual(["2024-01-01T01:00:00Z"], result["adjusted_expected_timestamps"])
        self.assertEqual(2, len(result["removed"]))

    def test_unused_exception_interval_is_rejected(self):
        expected = ["2024-06-03T21:05:00Z"]
        with self.assertRaisesRegex(CalendarError, "removes no expected"):
            apply_exception_evidence(expected, exception_evidence())

    def test_declaration_cannot_enable_holiday_guessing(self):
        value = declaration()
        value["standard_session"]["public_holiday_exceptions_in_baseline"] = True
        with self.assertRaisesRegex(CalendarError, "standard-session drift"):
            validate_declaration(value)

    def test_declaration_cannot_enable_seal_with_unresolved_gaps(self):
        value = declaration()
        value["quarantine"]["sealing_allowed_with_unresolved_discrepancies"] = True
        with self.assertRaisesRegex(CalendarError, "quarantine drift"):
            validate_declaration(value)

    def test_declaration_cannot_open_reserved_final_test(self):
        value = declaration()
        value["reserved_final_test"]["signal_generation_allowed"] = True
        with self.assertRaisesRegex(CalendarError, "reserved-test drift"):
            validate_declaration(value)

    def test_declaration_cannot_escalate_broker_authority(self):
        value = declaration()
        value["authority"]["broker_writes"] = True
        with self.assertRaisesRegex(CalendarError, "authority escalation"):
            validate_declaration(value)

    def test_quarantine_target_inside_repo_is_rejected(self):
        with self.assertRaisesRegex(CalendarError, "outside repository"):
            validate_quarantine_target(ROOT / "evidence", ROOT.parent)

    def test_existing_quarantine_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing"
            target.mkdir()
            with self.assertRaisesRegex(CalendarError, "overwrite"):
                validate_quarantine_target(target, ROOT.parent)

    def test_new_external_quarantine_target_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "new"
            self.assertEqual(
                target.resolve(), validate_quarantine_target(target, ROOT.parent)
            )


if __name__ == "__main__":
    unittest.main()
