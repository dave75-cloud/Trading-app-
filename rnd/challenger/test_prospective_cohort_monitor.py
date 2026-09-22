#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("prospective_cohort_monitor.py")
PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")

LEDGER_FIELDS = [
    "session_date_utc", "processed_at_utc", "provider_candidate",
    "reference_provider", "total_expected_bars", "total_compared_bars",
    "open_close_failure_rows", "high_low_only_failure_rows",
    "raw_signal_disagreements", "delayed_signal_disagreements",
    "volatility_eligibility_disagreements", "max_close_bps_diff",
    "max_any_ohlc_bps_diff", "session_pass", "canonical_m005_modified"
]

PAIR_FIELDS = [
    "session_date_utc", "pair", "session_utc", "expected_bars",
    "compared_bars", "open_close_failure_rows",
    "high_low_only_failure_rows", "raw_signal_disagreements",
    "delayed_signal_disagreements",
    "volatility_eligibility_disagreements",
    "median_close_bps_diff", "p95_close_bps_diff",
    "max_close_bps_diff", "max_any_ohlc_bps_diff", "pair_pass"
]

class MonitorTests(unittest.TestCase):
    def run_case(self, sessions, pair_rows):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline = root / "baseline.json"
            ledger = root / "ledger.csv"
            pairs = root / "pairs.csv"

            baseline.write_text(json.dumps({
                "cohort_start_utc": "2026-09-22",
                "provider_candidate": "twelve_data",
                "reference_provider": "polygon",
                "prospective_requirement_sessions": 10,
                "required_delayed_signal_disagreements": 0,
                "required_volatility_eligibility_disagreements": 0
            }))

            with ledger.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
                w.writeheader()
                w.writerows(sessions)

            with pairs.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=PAIR_FIELDS)
                w.writeheader()
                w.writerows(pair_rows)

            p = subprocess.run(
                ["python3", str(SCRIPT),
                 "--baseline", str(baseline),
                 "--ledger", str(ledger),
                 "--pair-ledger", str(pairs)],
                text=True, capture_output=True
            )
            return p, json.loads(p.stdout)

    def session(self, date, delayed=0, volatility=0, passed=True):
        return {
            "session_date_utc": date,
            "processed_at_utc": date + "T23:00:00+00:00",
            "provider_candidate": "twelve_data",
            "reference_provider": "polygon",
            "total_expected_bars": 108,
            "total_compared_bars": 108,
            "open_close_failure_rows": 0,
            "high_low_only_failure_rows": 0,
            "raw_signal_disagreements": 0,
            "delayed_signal_disagreements": delayed,
            "volatility_eligibility_disagreements": volatility,
            "max_close_bps_diff": 4.0,
            "max_any_ohlc_bps_diff": 6.0,
            "session_pass": passed,
            "canonical_m005_modified": False
        }

    def pair_rows(self, date):
        return [{
            "session_date_utc": date, "pair": p, "session_utc": "11:00-13:00",
            "expected_bars": 24, "compared_bars": 24,
            "open_close_failure_rows": 0, "high_low_only_failure_rows": 0,
            "raw_signal_disagreements": 0, "delayed_signal_disagreements": 0,
            "volatility_eligibility_disagreements": 0,
            "median_close_bps_diff": 1, "p95_close_bps_diff": 2,
            "max_close_bps_diff": 4, "max_any_ohlc_bps_diff": 6,
            "pair_pass": True
        } for p in PAIRS]

    def test_empty_fresh_cohort(self):
        p, r = self.run_case([], [])
        self.assertEqual(p.returncode, 0)
        self.assertEqual(r["prospective_sessions"], 0)
        self.assertFalse(r["evidence_requirement_met"])

    def test_ten_clean_sessions_meet_evidence_requirement(self):
        dates = [f"2026-10-{d:02d}" for d in range(1, 11)]
        sessions = [self.session(d) for d in dates]
        pairs = sum((self.pair_rows(d) for d in dates), [])
        p, r = self.run_case(sessions, pairs)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(r["evidence_requirement_met"])
        self.assertFalse(r["automatic_promotion"])
        self.assertTrue(r["human_review_required"])

    def test_one_disagreement_blocks_requirement(self):
        dates = [f"2026-10-{d:02d}" for d in range(1, 11)]
        sessions = [self.session(d) for d in dates]
        sessions[-1] = self.session(dates[-1], delayed=1, passed=False)
        pairs = sum((self.pair_rows(d) for d in dates), [])
        p, r = self.run_case(sessions, pairs)
        self.assertEqual(p.returncode, 0)
        self.assertFalse(r["evidence_requirement_met"])
        self.assertEqual(r["delayed_signal_disagreements"], 1)

    def test_incomplete_pair_evidence_fails_closed(self):
        d = "2026-10-01"
        p, r = self.run_case([self.session(d)], self.pair_rows(d)[:3])
        self.assertEqual(p.returncode, 1)
        self.assertTrue(r["integrity_errors"])
        self.assertFalse(r["evidence_requirement_met"])

if __name__ == "__main__":
    unittest.main()
