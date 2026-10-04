#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import rnd0041_validation_structural_seal as r


class TestRND0041ValidationStructuralSeal(unittest.TestCase):
    def test_outcome_fields_are_rejected(self):
        with self.assertRaises(r.RND0041SealError):
            r._forbid_outcome_fields({"nested": {"equity": 1.0}})

    def test_non_outcome_structural_fields_are_allowed(self):
        r._forbid_outcome_fields({
            "row_count": 10,
            "missing_count": 2,
            "canonical_rows_sha256": "abc",
            "boundary_proof": {"boundary_status": "PASS"},
        })

    def test_write_new_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seal.json"
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(r.RND0041SealError):
                r._write_new(path, {"x": 1})

    def test_frozen_validation_interval(self):
        self.assertEqual(r.START_UTC, "2020-12-31T19:15:00Z")
        self.assertEqual(r.END_UTC, "2023-01-01T09:40:00Z")
        self.assertEqual(tuple(r.SYMBOLS), ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY"))


if __name__ == "__main__":
    unittest.main()
