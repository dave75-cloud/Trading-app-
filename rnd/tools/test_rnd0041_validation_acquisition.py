#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import rnd0041_validation_acquisition as r


class TestRND0041ValidationAcquisition(unittest.TestCase):
    def test_repository_declaration_remains_outcome_closed(self):
        value = r.load_declaration()
        self.assertFalse(value["strategy_outcomes"])
        self.assertFalse(value["candidate_evaluation"])
        self.assertFalse(value["reserved_final_open"])
        self.assertFalse(value["broker_writes"])
        self.assertFalse(value["capital_authority"])

    def test_repository_authorization_is_acquisition_only(self):
        value = r.load_authorization()
        self.assertTrue(value["acquisition_authorized"])
        self.assertFalse(value["candidate_evaluation_authorized"])
        self.assertFalse(value["strategy_outcomes_authorized"])
        self.assertFalse(value["parameter_search"])
        self.assertFalse(value["strategy_selection"])
        self.assertFalse(value["reserved_final_open"])
        self.assertFalse(value["broker_writes"])
        self.assertFalse(value["capital_authority"])

    def test_boundary_proof_accepts_validation_rows_before_final_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [
                {"timestamp_utc": "2020-12-31T19:15:00Z"},
                {"timestamp_utc": "2021-01-04T00:00:00Z"},
                {"timestamp_utc": "2023-01-01T09:35:00Z"},
            ]
            (root / "canonical_rows.json").write_text(json.dumps(rows))
            proof = r.boundary_proof(root, "AUDUSD")
            self.assertEqual(proof["boundary_status"], "PASS")
            self.assertEqual(proof["rows_at_or_after_reserved_final_boundary"], 0)
            self.assertEqual(proof["last_canonical_timestamp_utc"], "2023-01-01T09:35:00Z")

    def test_boundary_proof_rejects_reserved_final_boundary_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [
                {"timestamp_utc": "2023-01-01T09:35:00Z"},
                {"timestamp_utc": "2023-01-01T09:40:00Z"},
            ]
            (root / "canonical_rows.json").write_text(json.dumps(rows))
            with self.assertRaises(r.RND0041AcquisitionError):
                r.boundary_proof(root, "EURUSD")

    def test_exact_cross_year_shard_is_frozen(self):
        self.assertEqual(r.SHARD, {
            "year": "validation-2021-2022",
            "start_utc": "2020-12-31T19:15:00Z",
            "end_utc": "2023-01-01T09:40:00Z",
        })


if __name__ == "__main__":
    unittest.main()
