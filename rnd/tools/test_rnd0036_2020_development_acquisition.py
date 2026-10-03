#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rnd0036_2020_development_acquisition as r36


class TestRND00362020DevelopmentAcquisition(unittest.TestCase):
    def test_boundary_proof_rejects_validation_row(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "canonical_rows.json").write_text(json.dumps([
                {"timestamp_utc": "2020-12-31T19:10:00Z"},
                {"timestamp_utc": "2020-12-31T19:15:00Z"},
            ]))
            with self.assertRaisesRegex(r36.RND0036AcquisitionError, "outside authorized development interval"):
                r36.boundary_proof(p, "AUDUSD")

    def test_boundary_proof_accepts_last_preboundary_row(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "canonical_rows.json").write_text(json.dumps([
                {"timestamp_utc": "2020-01-01T00:00:00Z"},
                {"timestamp_utc": "2020-12-31T19:10:00Z"},
            ]))
            out = r36.boundary_proof(p, "AUDUSD")
            self.assertEqual(out["last_canonical_timestamp_utc"], "2020-12-31T19:10:00Z")
            self.assertEqual(out["rows_at_or_after_validation_boundary"], 0)
            self.assertEqual(out["boundary_status"], "PASS")

    def test_authorization_preserves_all_prohibited_authorities(self):
        fake = {
            "task_id": "RND-0036",
            "status": "ACTIVE",
            "scope": "2020_DEVELOPMENT_ACQUISITION_AND_SEAL_ONLY",
            "authorized_interval": {
                "start_inclusive_utc": r36.START_UTC,
                "end_exclusive_utc": r36.END_UTC,
            },
            "symbols": list(r36.SYMBOLS),
            "granularity": "M5",
            "provider": "OANDA",
            "environment": "PRACTICE",
            "strategy_outcomes": False,
            "validation_open": False,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_review_required": True,
        }
        with patch.object(r36, "_json", return_value=fake):
            out = r36.load_authorization("unused")
        self.assertEqual(out["status"], "ACTIVE")

    def test_authorization_fails_if_validation_open(self):
        fake = {
            "task_id": "RND-0036",
            "status": "ACTIVE",
            "scope": "2020_DEVELOPMENT_ACQUISITION_AND_SEAL_ONLY",
            "authorized_interval": {
                "start_inclusive_utc": r36.START_UTC,
                "end_exclusive_utc": r36.END_UTC,
            },
            "symbols": list(r36.SYMBOLS),
            "granularity": "M5",
            "provider": "OANDA",
            "environment": "PRACTICE",
            "strategy_outcomes": False,
            "validation_open": True,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_review_required": True,
        }
        with patch.object(r36, "_json", return_value=fake):
            with self.assertRaisesRegex(r36.RND0036AcquisitionError, "validation_open"):
                r36.load_authorization("unused")


if __name__ == "__main__":
    unittest.main()
