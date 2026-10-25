#!/usr/bin/env python3
"""Synthetic-only tests of RND-0074 session coverage; no actual archive or prices."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from rnd0074_session_coverage_audit import pilot_coverage, AuditError

UTC = timezone.utc

def z(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

class SessionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.shard = Path(self.tmp.name)
        self.shard.joinpath("standard_schedule.json").write_text("[]")
        self.shard.joinpath("discrepancy_ledger.json").write_text("{}")
        start = datetime(2019, 1, 1, tzinfo=UTC)
        # Synthetic two-day time-grid fixture; no actual market records.
        self.schedule = [z(start + timedelta(minutes=5*i)) for i in range(576)]
        self.ledger = {"missing_timestamps": [self.schedule[10]], "unexpected_timestamps": []}

    def audit(self):
        def fake_load(path):
            return self.ledger if Path(path).name == "discrepancy_ledger.json" else self.schedule
        with patch("rnd0074_session_coverage_audit.summarize", return_value={"hashes_checked":True}), \
             patch("rnd0074_session_coverage_audit.load_json", side_effect=fake_load):
            return pilot_coverage(self.shard, "EURUSD", 2019)[1]

    def test_six_predeclared_windows(self):
        r = self.audit()
        self.assertEqual(6, len(r))
        self.assertEqual(3, len({x["session"] for x in r}))
        self.assertEqual({"OPEN","CLOSE"}, {x["boundary"] for x in r})

    def test_reconciles_and_no_synthetic_prices(self):
        for x in self.audit():
            self.assertEqual(x["expected_baseline_m5"], x["present_baseline_m5"] + x["missing_baseline_m5"])
            self.assertGreaterEqual(x["present_baseline_m5"], 0)
            self.assertLessEqual(x["coverage_pct"], 100)

    def test_missing_eligible_timestamp_reduces_coverage(self):
        self.ledger["missing_timestamps"] = ["2019-01-02T00:00:00Z"]
        r = self.audit()
        tokyo_open = next(x for x in r if x["session"] == "TOKYO" and x["boundary"] == "OPEN")
        self.assertGreaterEqual(tokyo_open["missing_baseline_m5"], 1)

    def test_unexpected_timestamp_is_counted_separately(self):
        self.ledger["unexpected_timestamps"] = ["2019-01-02T00:00:00Z"]
        self.schedule.remove("2019-01-02T00:00:00Z")
        r = self.audit()
        tokyo_open = next(x for x in r if x["session"] == "TOKYO" and x["boundary"] == "OPEN")
        self.assertGreaterEqual(tokyo_open["unexpected_provider_timestamps_in_windows"], 1)

    def test_only_2019_accepted(self):
        with self.assertRaises(AuditError):
            pilot_coverage(self.shard, "EURUSD", 2018)

    def test_unapproved_instrument_rejected(self):
        with self.assertRaises(AuditError):
            pilot_coverage(self.shard, "USDCAD", 2019)

if __name__ == "__main__":
    unittest.main()
