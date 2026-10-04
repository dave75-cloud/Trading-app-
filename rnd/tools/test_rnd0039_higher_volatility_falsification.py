#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import rnd0039_higher_volatility_falsification as r


class TestRND0039HigherVolatilityFalsification(unittest.TestCase):
    def test_repository_authorization_is_exact_two_point_and_bounded(self):
        v = r.load_authorization()
        self.assertEqual(v["authorized_thresholds"], [0.0005, 0.0006])
        self.assertTrue(v["outcomes_authorized"])
        self.assertFalse(v["parameter_search"])
        self.assertFalse(v["thresholds_above_0006"])
        self.assertFalse(v["intermediate_thresholds"])
        self.assertFalse(v["pair_specific_thresholds"])
        self.assertFalse(v["strategy_selection"])
        self.assertFalse(v["validation_open"])
        self.assertFalse(v["final_test_open"])

    def test_difference_is_treatment_minus_reference(self):
        ref = {"trades": 10, "hit_rate": .4, "gross_equity_index": .9, "net_equity_index": .8,
               "net_max_drawdown": -.2, "execution_cost_drag": .1}
        trt = {"trades": 7, "hit_rate": .5, "gross_equity_index": 1.0, "net_equity_index": .95,
               "net_max_drawdown": -.1, "execution_cost_drag": .06}
        d = r._difference(ref, trt)
        self.assertEqual(d["trade_count"], -3)
        self.assertAlmostEqual(d["net_equity_index"], .15)
        self.assertAlmostEqual(d["execution_cost_drag"], -.04)

    def test_write_new_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.json"
            p.write_text("{}\n")
            with self.assertRaises(r.RND0039Error):
                r._write_new(p, {"x": 1})


if __name__ == "__main__":
    unittest.main()
