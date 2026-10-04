#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import rnd0043_signal_friction_development as r


class TestRND0043SignalFrictionDevelopment(unittest.TestCase):
    def test_authorization_exact_predeclared_scope(self):
        a = r.load_authorization()
        self.assertEqual(a["authorized_arms"], {"F000": None, "F001": 3.0, "F002": 5.0, "F003": 8.0})
        self.assertTrue(a["development_outcomes_authorized"])
        self.assertFalse(a["validation_access"])
        self.assertFalse(a["reserved_final_open"])
        self.assertFalse(a["broker_writes"])

    def test_ratio_summary(self):
        s = r.ratio_summary([8.0, 3.0, 5.0, 4.0])
        self.assertEqual(s["count"], 4)
        self.assertEqual(s["min"], 3.0)
        self.assertEqual(s["max"], 8.0)
        self.assertEqual(s["median"], 4.5)

    def test_write_new_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "report.json"
            r.write_new(p, {"x": 1})
            with self.assertRaises(r.RND0043DevelopmentError):
                r.write_new(p, {"x": 2})

    def _arm(self, net, dd, pair_eq, year_share=0.5, year_ok=True, pair_ok=True):
        return {
            "portfolio_net_return_sum": net,
            "per_symbol": {s: {"net_equity_index": pair_eq[i]} for i, s in enumerate(r.SYMBOLS)},
            "max_positive_year_contribution_share": year_share,
            "diagnostics": {"G_four_pair_concurrent_reference": {"equal_unit_normalized_max_drawdown": dd}},
            "leave_one_out_vs_F000": None if net == 0 else {
                "year_majority_positive": year_ok,
                "pair_majority_positive": pair_ok,
            },
        }

    def test_classify_supported(self):
        arms = {
            "F000": self._arm(0.0, -0.08, [1.0, 1.0, 1.0, 1.0]),
            "F001": self._arm(0.02, -0.07, [1.01, 1.01, 1.00, 0.99]),
            "F002": self._arm(0.04, -0.06, [1.02, 1.01, 1.01, 0.99]),
            "F003": self._arm(0.03, -0.07, [1.01, 1.00, 1.00, 0.99]),
        }
        c, d = r.classify(arms)
        self.assertEqual(c, "MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH")
        self.assertEqual(d["best_coherent_arm"], "F002")

    def test_classify_mixed(self):
        arms = {
            "F000": self._arm(0.0, -0.08, [1.0, 1.0, 1.0, 1.0]),
            "F001": self._arm(-0.01, -0.07, [0.99, 1.00, 1.00, 1.00]),
            "F002": self._arm(0.04, -0.06, [1.02, 0.99, 0.99, 0.99]),
            "F003": self._arm(-0.02, -0.09, [0.98, 1.00, 1.00, 1.00]),
        }
        c, _ = r.classify(arms)
        self.assertEqual(c, "MECHANISM_MIXED_OR_NON_MONOTONIC")

    def test_classify_falsified(self):
        arms = {
            "F000": self._arm(0.0, -0.08, [1.0, 1.0, 1.0, 1.0]),
            "F001": self._arm(-0.01, -0.07, [0.99, 1.00, 1.00, 1.00]),
            "F002": self._arm(-0.02, -0.06, [0.98, 1.00, 1.00, 1.00]),
            "F003": self._arm(-0.03, -0.05, [0.97, 1.00, 1.00, 1.00]),
        }
        c, d = r.classify(arms)
        self.assertEqual(c, "MECHANISM_FALSIFIED")
        self.assertIsNone(d["best_coherent_arm"])


if __name__ == "__main__":
    unittest.main()
