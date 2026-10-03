#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import rnd0038_full_development_r000 as r


class TestRND0038FullDevelopmentR000(unittest.TestCase):
    def test_repository_authorization_is_bounded(self):
        value = r.load_authorization()
        self.assertTrue(value["r000_development_outcomes"])
        self.assertFalse(value["higher_volatility_outcomes"])
        self.assertFalse(value["parameter_search"])
        self.assertFalse(value["strategy_selection"])
        self.assertFalse(value["validation_open"])
        self.assertFalse(value["final_test_open"])
        self.assertFalse(value["broker_writes"])
        self.assertFalse(value["capital_authority"])

    def test_2020_contribution_filters_only_exit_year_2020(self):
        per_symbol = {}
        for symbol in r.SYMBOLS:
            per_symbol[symbol] = {
                "trades": [
                    {"exit_timestamp": "2019-12-31T12:00:00Z", "gross_return": 0.02, "net_return": 0.01},
                    {"exit_timestamp": "2020-01-02T12:00:00Z", "gross_return": 0.03, "net_return": 0.02},
                    {"exit_timestamp": "2020-02-03T12:00:00Z", "gross_return": -0.01, "net_return": -0.015},
                ]
            }
        out = r._year2020_contribution(per_symbol)
        self.assertEqual(out["combined"]["trades"], 8)
        self.assertAlmostEqual(out["combined"]["net_return_sum"], 0.02)
        for symbol in r.SYMBOLS:
            self.assertEqual(out["per_symbol"][symbol]["trades"], 2)
        self.assertFalse(out["strategy_selection_authority"])

    def test_write_new_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text("{}\n")
            with self.assertRaises(r.RND0038Error):
                r._write_new(path, {"x": 1})

    def test_summary_handles_empty_trade_set(self):
        out = r._summary([])
        self.assertEqual(out["trades"], 0)
        self.assertEqual(out["net_return_sum"], 0)
        self.assertIsNone(out["mean_net_return"])
        self.assertIsNone(out["positive_trade_fraction"])


if __name__ == "__main__":
    unittest.main()
