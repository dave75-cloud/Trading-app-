#!/usr/bin/env python3

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "rnd" / "tools" / "rnd0034_reconstruct_development.py"
spec = importlib.util.spec_from_file_location("rnd0034_runner", TOOL)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RND0034BoundedRunnerTests(unittest.TestCase):
    def test_scope_separates_2015_pilot_from_development_run(self):
        self.assertEqual((2015,), runner.PILOT_YEARS)
        self.assertEqual(
            (2015, 2016, 2017, 2018, 2019),
            runner.DEVELOPMENT_YEARS,
        )
        self.assertNotIn(2016, runner.PILOT_YEARS)
        self.assertNotIn(2020, runner.DEVELOPMENT_YEARS)

    def test_2015_paths_are_explicit_and_2016_plus_share_development_root(self):
        args = SimpleNamespace(
            audusd_2015_shard="/e/aud",
            cross_pair_2015_root="/e/cross",
            development_root="/e/dev",
        )
        self.assertEqual(
            Path("/e/aud"),
            runner._path_for("AUDUSD", 2015, args),
        )
        self.assertEqual(
            Path("/e/cross/EURUSD/2015"),
            runner._path_for("EURUSD", 2015, args),
        )
        self.assertEqual(
            Path("/e/dev/USDJPY/2019"),
            runner._path_for("USDJPY", 2019, args),
        )

    def test_pilot_path_resolution_never_requires_development_root(self):
        args = SimpleNamespace(
            audusd_2015_shard="/e/aud",
            cross_pair_2015_root="/e/cross",
            development_root=None,
        )
        for symbol in runner.SYMBOLS:
            path = runner._path_for(symbol, 2015, args)
            self.assertNotIn("/e/dev", str(path))

    def test_bound_identity_requires_all_hashes_and_row_count(self):
        manifest = {
            "aggregate_raw_bundle_sha256": "a" * 64,
            "canonical_rows_sha256": "b" * 64,
            "standard_schedule_sha256": "c" * 64,
            "row_count": 10,
        }
        expected = {
            "raw_bundle_sha256": "a" * 64,
            "canonical_rows_sha256": "b" * 64,
            "standard_schedule_sha256": "c" * 64,
            "row_count": 10,
        }
        self.assertTrue(runner._identity_matches(manifest, expected))
        manifest["row_count"] = 9
        self.assertFalse(runner._identity_matches(manifest, expected))


if __name__ == "__main__":
    unittest.main()
