#!/usr/bin/env python3
import json, tempfile, unittest
from pathlib import Path
from unittest import mock
import rnd0042_validation_candidate as r

class TestRND0042ValidationCandidate(unittest.TestCase):
    def test_authorization_is_fixed_candidate_only(self):
        a=r.authorization()
        self.assertEqual(a["candidate_threshold"],0.0006)
        self.assertTrue(a["validation_outcomes_authorized"])
        self.assertFalse(a["alternate_thresholds"])
        self.assertFalse(a["reserved_final_open"])
    def test_load_rows_rejects_final_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"AUDUSD"/"validation"; p.mkdir(parents=True)
            (p/"canonical_rows.json").write_text(json.dumps([{"timestamp_utc":"2023-01-01T09:40:00Z"}]))
            with self.assertRaises(r.RND0042Error): r.load_rows(tmp,"AUDUSD")
    def test_load_rows_accepts_fractional_validation_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"AUDUSD"/"validation"; p.mkdir(parents=True)
            (p/"canonical_rows.json").write_text(json.dumps([{"timestamp_utc":"2021-01-04T00:00:00.000000000Z"}]))
            self.assertEqual(len(r.load_rows(tmp,"AUDUSD")),1)

if __name__=="__main__": unittest.main()
