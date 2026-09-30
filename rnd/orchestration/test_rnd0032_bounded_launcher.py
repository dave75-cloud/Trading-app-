#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "rnd" / "tools" / "rnd0032_acquire_2015.py"
spec = importlib.util.spec_from_file_location("rnd0032_acquire_2015", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RND0032BoundedLauncherTests(unittest.TestCase):
    def test_command_is_exactly_three_pairs_and_2015(self):
        command = module.build_command("/tmp/evidence", 0.6)
        self.assertEqual(1, command.count("2015"))
        self.assertNotIn("AUDUSD", command)
        for symbol in ("EURUSD", "GBPUSD", "USDJPY"):
            self.assertIn(symbol, command)

    def test_no_other_year_is_exposed_by_builder(self):
        command = module.build_command("/tmp/evidence", 0.6)
        for year in range(2016, 2025):
            self.assertNotIn(str(year), command)

    def test_resume_is_explicit(self):
        self.assertNotIn("--resume", module.build_command("/tmp/evidence", 0.6))
        self.assertIn("--resume", module.build_command("/tmp/evidence", 0.6, True))


if __name__ == "__main__":
    unittest.main()
