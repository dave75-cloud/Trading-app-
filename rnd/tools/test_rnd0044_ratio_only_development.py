#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import rnd0044_ratio_only_development as r


class TestRND0044RatioOnlyDevelopment(unittest.TestCase):
    def arm(self, net, terminal, dd=-0.05, positive_pairs=3, year_conc=0.5, loo=True):
        per_symbol = {}
        for i, s in enumerate(r.SYMBOLS):
            per_symbol[s] = {"net_equity_index": 1.01 if i < positive_pairs else 0.99}
        return {
            "portfolio_net_return_sum": net,
            "per_symbol": per_symbol,
            "max_positive_year_contribution_share": year_conc,
            "leave_one_out_vs_Q000": None if loo is None else {
                "year_majority_positive": loo,
                "pair_majority_positive": loo,
            },
            "diagnostics": {"G_four_pair_concurrent_reference": {
                "final_equal_unit_normalized_equity_index": terminal,
                "equal_unit_normalized_max_drawdown": dd,
            }},
        }

    def test_authorization_exact_scope(self):
        v = r.load_authorization()
        self.assertTrue(v["development_outcomes_authorized"])
        self.assertEqual(v["authorized_arms"], {
            "Q000": "FROZEN_R000_REFERENCE", "Q001": 3.0, "Q002": 5.0, "Q003": 8.0
        })
        self.assertFalse(v["validation_access"])
        self.assertFalse(v["reserved_final_open"])

    def test_candidate_freeze_review_classification(self):
        arms = {
            "Q000": self.arm(-0.25, 0.94, loo=None),
            "Q001": self.arm(-0.10, 0.98),
            "Q002": self.arm(-0.02, 0.995),
            "Q003": self.arm(0.04, 1.01, positive_pairs=3, year_conc=0.6),
        }
        c, d = r.classify(arms)
        self.assertEqual(c, "RATIO_ONLY_SUPPORTED_FOR_CANDIDATE_FREEZE_REVIEW")
        self.assertEqual(d["review_eligible_arms"], ["Q003"])

    def test_further_research_only_when_monotonic_but_not_positive(self):
        arms = {
            "Q000": self.arm(-0.25, 0.94, loo=None),
            "Q001": self.arm(-0.20, 0.95),
            "Q002": self.arm(-0.10, 0.97),
            "Q003": self.arm(-0.01, 0.99),
        }
        c, _ = r.classify(arms)
        self.assertEqual(c, "RATIO_ONLY_SUPPORTED_FOR_FURTHER_RESEARCH_ONLY")

    def test_mixed_when_improvement_non_monotonic(self):
        arms = {
            "Q000": self.arm(-0.25, 0.94, loo=None),
            "Q001": self.arm(-0.10, 0.98),
            "Q002": self.arm(-0.18, 0.96),
            "Q003": self.arm(-0.05, 0.99),
        }
        c, _ = r.classify(arms)
        self.assertEqual(c, "RATIO_ONLY_MIXED_OR_NON_MONOTONIC")

    def test_falsified_when_no_arm_improves_reference(self):
        arms = {
            "Q000": self.arm(-0.10, 0.97, loo=None),
            "Q001": self.arm(-0.12, 0.96),
            "Q002": self.arm(-0.15, 0.95),
            "Q003": self.arm(-0.20, 0.94),
        }
        c, _ = r.classify(arms)
        self.assertEqual(c, "RATIO_ONLY_FALSIFIED")

    def test_report_overwrite_prohibited(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "report.json"
            r.write_new(p, {"x": 1})
            with self.assertRaises(r.RND0044DevelopmentError):
                r.write_new(p, {"x": 2})


if __name__ == "__main__":
    unittest.main()
