#!/usr/bin/env python3
import unittest
from graduation_dossier import build_dossier


class DossierTests(unittest.TestCase):
    def test_below_threshold_never_selects_outcome(self):
        ledger = {
            "summary": {"accepted_sessions": 9, "authoritative_events": 17},
            "safety": {"zero_recorded_safety_violations": True},
            "integrity": {"all_m006e2_hashes_match": True},
            "review": {"pending_review_days": []},
        }
        reliability = {
            "failure_taxonomy": {
                "contained_upstream": 9,
                "contained_local_concurrency": 1,
                "unclassified_raw_failures": 0,
            }
        }
        concurrency = {"incident": {"fail_closed": True}}
        data, _ = build_dossier(ledger, reliability, concurrency)
        self.assertFalse(data["minimum_thresholds_met"])
        self.assertIsNone(data["selected_outcome"])
        self.assertFalse(data["automatic_promotion"])
        self.assertTrue(data["human_decision_required"])

    def test_threshold_met_still_never_selects_outcome(self):
        ledger = {
            "summary": {"accepted_sessions": 25, "authoritative_events": 100},
            "safety": {"zero_recorded_safety_violations": True},
            "integrity": {"all_m006e2_hashes_match": True},
            "review": {"pending_review_days": []},
        }
        reliability = {"failure_taxonomy": {}}
        concurrency = {"incident": {"fail_closed": True}}
        data, _ = build_dossier(ledger, reliability, concurrency)
        self.assertTrue(data["minimum_thresholds_met"])
        self.assertIsNone(data["selected_outcome"])
        self.assertFalse(data["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
