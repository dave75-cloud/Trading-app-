import unittest

import rnd0045_cross_pair_heterogeneity as h


SYMBOLS = h.SYMBOLS
YEARS = h.YEARS


def arm(pair_net, yearly, equity=None, dd=None, cost=None, trades=None):
    equity = equity or {s: 1.0 + pair_net[s] for s in SYMBOLS}
    dd = dd or {s: -0.05 for s in SYMBOLS}
    cost = cost or {s: 0.02 for s in SYMBOLS}
    trades = trades or {s: 100 for s in SYMBOLS}
    return {
        "per_symbol": {
            s: {
                "net_return_sum": pair_net[s],
                "net_equity_index": equity[s],
                "net_max_drawdown": dd[s],
                "execution_cost_drag": cost[s],
                "trades": trades[s],
            }
            for s in SYMBOLS
        },
        "year_pair_net_return_sum": {
            y: {s: yearly[y][s] for s in SYMBOLS}
            for y in YEARS
        },
    }


def zero_arm():
    return arm(
        {s: 0.0 for s in SYMBOLS},
        {y: {s: 0.0 for s in SYMBOLS} for y in YEARS},
    )


class RND0045Tests(unittest.TestCase):
    def test_candidate_review_fixture(self):
        base = zero_arm()
        pair = {"AUDUSD": 0.03, "EURUSD": 0.04, "GBPUSD": 0.05, "USDJPY": 0.02}
        yearly = {
            y: {"AUDUSD": 0.005, "EURUSD": 0.007, "GBPUSD": 0.008, "USDJPY": 0.003}
            for y in YEARS
        }
        result = h.analyze(base, arm(pair, yearly))
        self.assertEqual(result["classification"], "COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW")
        self.assertEqual(result["sign_coherence_positive_pair_count"], 4)
        self.assertTrue(all(v > 0 for v in result["leave_one_pair_out_aggregate_treatment_effect"].values()))

    def test_supported_with_material_heterogeneity_fixture(self):
        base = zero_arm()
        pair = {"AUDUSD": -0.01, "EURUSD": 0.05, "GBPUSD": 0.04, "USDJPY": 0.03}
        yearly = {}
        for i, y in enumerate(YEARS):
            if i < 3:
                yearly[y] = {"AUDUSD": -0.004, "EURUSD": 0.012, "GBPUSD": 0.010, "USDJPY": 0.008}
            else:
                yearly[y] = {"AUDUSD": 0.001, "EURUSD": -0.002, "GBPUSD": 0.002, "USDJPY": 0.001}
        result = h.analyze(base, arm(pair, yearly))
        self.assertEqual(result["classification"], "COMMON_MECHANISM_SUPPORTED_WITH_MATERIAL_HETEROGENEITY")
        self.assertEqual(result["classification_details"]["positive_full_period_pair_count"], 3)

    def test_pair_dependent_fixture(self):
        base = zero_arm()
        pair = {"AUDUSD": -0.05, "EURUSD": 0.08, "GBPUSD": 0.04, "USDJPY": -0.01}
        yearly = {
            y: {"AUDUSD": -0.008, "EURUSD": 0.014, "GBPUSD": 0.007, "USDJPY": -0.002}
            for y in YEARS
        }
        result = h.analyze(base, arm(pair, yearly))
        self.assertEqual(result["classification"], "PAIR_DEPENDENT_MECHANISM")
        self.assertEqual(result["classification_details"]["positive_full_period_pair_count"], 2)

    def test_falsified_fixture(self):
        base = zero_arm()
        pair = {"AUDUSD": -0.03, "EURUSD": 0.01, "GBPUSD": -0.02, "USDJPY": 0.005}
        yearly = {
            y: {"AUDUSD": -0.005, "EURUSD": 0.002, "GBPUSD": -0.004, "USDJPY": 0.001}
            for y in YEARS
        }
        result = h.analyze(base, arm(pair, yearly))
        self.assertEqual(result["classification"], "COMMON_MECHANISM_FALSIFIED")
        self.assertLessEqual(result["aggregate_treatment_effect"], 0)

    def test_pair_concentration_can_force_pair_dependent(self):
        base = zero_arm()
        pair = {"AUDUSD": 0.001, "EURUSD": 0.001, "GBPUSD": 0.098, "USDJPY": -0.001}
        yearly = {
            y: {"AUDUSD": 0.0002, "EURUSD": 0.0002, "GBPUSD": 0.016, "USDJPY": -0.0001}
            for y in YEARS
        }
        result = h.analyze(base, arm(pair, yearly))
        self.assertEqual(result["classification"], "PAIR_DEPENDENT_MECHANISM")
        self.assertGreater(result["max_positive_pair_share"], 0.70)

    def test_leave_one_year_out_is_pair_specific(self):
        base = zero_arm()
        pair = {s: 0.06 for s in SYMBOLS}
        yearly = {y: {s: 0.01 for s in SYMBOLS} for y in YEARS}
        result = h.analyze(base, arm(pair, yearly))
        self.assertAlmostEqual(result["pair_metrics"]["EURUSD"]["leave_one_year_out_treatment_effect"]["2017"], 0.05)

    def test_schema_rejects_missing_pair(self):
        base = zero_arm()
        treatment = zero_arm()
        del treatment["per_symbol"]["AUDUSD"]
        with self.assertRaises(h.RND0045DiagnosticError):
            h.analyze(base, treatment)

    def test_schema_rejects_missing_year(self):
        base = zero_arm()
        treatment = zero_arm()
        del treatment["year_pair_net_return_sum"]["2020"]
        with self.assertRaises(h.RND0045DiagnosticError):
            h.analyze(base, treatment)

    def test_authority_remains_closed(self):
        result = h.analyze(zero_arm(), zero_arm())
        self.assertFalse(result["authority"]["development_outcomes"])
        self.assertFalse(result["authority"]["pair_dropping"])
        self.assertFalse(result["authority"]["validation_access"])
        self.assertFalse(result["authority"]["reserved_final_open"])
        self.assertFalse(result["authority"]["broker_writes"])
        self.assertFalse(result["authority"]["capital_authority"])


if __name__ == "__main__":
    unittest.main()
