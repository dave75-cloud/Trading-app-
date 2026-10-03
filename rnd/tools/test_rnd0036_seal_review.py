#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from rnd0036_seal_review import RND0036SealReviewError, _write_new


class TestRND0036SealReview(unittest.TestCase):
    def test_report_overwrite_is_prohibited(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "report.json"
            p.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(RND0036SealReviewError, "overwrite prohibited"):
                _write_new(p, {"status": "PASS"})

    def test_new_report_write_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "report.json"
            out = _write_new(p, {"status": "PASS"})
            self.assertEqual(out, p.resolve())
            self.assertTrue(p.is_file())


if __name__ == "__main__":
    unittest.main()
