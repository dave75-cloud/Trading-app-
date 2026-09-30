#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "rnd" / "tools" / "rnd0033_acquire_development_history.py"
spec = importlib.util.spec_from_file_location("rnd0033_launcher", TOOL)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class RND0033BoundedLauncherTests(unittest.TestCase):
    def test_scope_is_exact_four_pairs_four_years(self):
        self.assertEqual(("AUDUSD", "EURUSD", "GBPUSD", "USDJPY"), launcher.SYMBOLS)
        self.assertEqual((2016, 2017, 2018, 2019), launcher.YEARS)

    def test_command_hardcodes_exact_scope(self):
        command = launcher.build_command("/tmp/evidence", 0.6)
        pairs = [command[i + 1] for i, x in enumerate(command[:-1]) if x == "--symbol"]
        years = [command[i + 1] for i, x in enumerate(command[:-1]) if x == "--year"]
        self.assertEqual(list(launcher.SYMBOLS), pairs)
        self.assertEqual([str(x) for x in launcher.YEARS], years)
        self.assertNotIn("2015", years)
        self.assertNotIn("2020", years)

    def test_resume_is_explicit(self):
        self.assertNotIn("--resume", launcher.build_command("/tmp/evidence", 0.6))
        self.assertIn("--resume", launcher.build_command("/tmp/evidence", 0.6, True))


if __name__ == "__main__":
    unittest.main()
