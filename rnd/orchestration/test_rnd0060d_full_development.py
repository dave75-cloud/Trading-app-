import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from rnd0060d_full_development import classify, _declaration
from rnd0060_research_firewall import validate_research_declaration

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


def symbol_result(equity=1.02, net=0.04, annual=None):
    if annual is None:
        annual = {2015: 0.01, 2016: 0.01, 2017: 0.01, 2018: 0.01, 2019: 0.0, 2020: 0.0}
    return {
        "terminal_net_equity": equity,
        "realized_net_sum": net,
        "annual_realized_net": dict(annual),
    }


def results(**overrides):
    out = {symbol: symbol_result() for symbol in SYMBOLS}
    for symbol, value in overrides.items():
        out[symbol] = value
    return out


def portfolio(**overrides):
    out = {
        "final_equal_unit_normalized_equity_index": 1.03,
        "realized_completed_trade_net_return_sum": 0.16,
        "equal_unit_normalized_max_drawdown": -0.03,
        "status": "PASS",
    }
    out.update(overrides)
    return out


class TestRND0060DFullDevelopment(unittest.TestCase):
    def test_frozen_declaration_passes_independent_research_firewall(self):
        self.assertEqual(
            validate_research_declaration(_declaration())["status"],
            "INDEPENDENT_RESEARCH_DECLARATION_ACCEPTED",
        )

    def test_all_predeclared_criteria_pass_only_to_candidate_review_eligibility(self):
        out = classify(results(), portfolio())
        self.assertEqual(out["classification"], "ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW")
        self.assertTrue(all(out["criteria"].values()))

    def test_terminal_portfolio_equity_failure_falsifies(self):
        self.assertEqual(
            classify(results(), portfolio(final_equal_unit_normalized_equity_index=1.0))["classification"],
            "DEVELOPMENT_FALSIFIED",
        )

    def test_realized_net_failure_falsifies(self):
        self.assertEqual(
            classify(results(), portfolio(realized_completed_trade_net_return_sum=0.0))["classification"],
            "DEVELOPMENT_FALSIFIED",
        )

    def test_fewer_than_three_positive_pairs_falsifies(self):
        values = results(AUDUSD=symbol_result(equity=0.99), EURUSD=symbol_result(equity=0.99))
        out = classify(values, portfolio())
        self.assertFalse(out["criteria"]["at_least_3_of_4_pair_terminal_equities_gte_1"])
        self.assertEqual(out["classification"], "DEVELOPMENT_FALSIFIED")

    def test_drawdown_failure_falsifies(self):
        self.assertEqual(
            classify(results(), portfolio(equal_unit_normalized_max_drawdown=-0.100001))["classification"],
            "DEVELOPMENT_FALSIFIED",
        )

    def test_fewer_than_four_positive_years_falsifies(self):
        annual = {2015: 0.01, 2016: 0.01, 2017: 0.01, 2018: -0.01, 2019: -0.01, 2020: -0.01}
        values = {symbol: symbol_result(annual=annual) for symbol in SYMBOLS}
        out = classify(values, portfolio())
        self.assertFalse(out["criteria"]["at_least_4_of_6_positive_development_years"])
        self.assertEqual(out["classification"], "DEVELOPMENT_FALSIFIED")

    def test_leave_one_pair_out_failure_falsifies(self):
        values = results(
            AUDUSD=symbol_result(net=0.12),
            EURUSD=symbol_result(net=-0.03),
            GBPUSD=symbol_result(net=-0.03),
            USDJPY=symbol_result(net=-0.03),
        )
        out = classify(values, portfolio(realized_completed_trade_net_return_sum=0.03))
        self.assertFalse(out["criteria"]["every_leave_one_pair_out_realized_net_sum_gt_0"])
        self.assertEqual(out["classification"], "DEVELOPMENT_FALSIFIED")

    def test_integrity_failure_falsifies(self):
        self.assertEqual(
            classify(results(), portfolio(status="FAIL"))["classification"],
            "DEVELOPMENT_FALSIFIED",
        )

    def test_classifier_has_no_extend_rescue_or_promotion_outcome(self):
        allowed = {
            classify(results(), portfolio())["classification"],
            classify(results(), portfolio(status="FAIL"))["classification"],
        }
        self.assertEqual(allowed, {"ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW", "DEVELOPMENT_FALSIFIED"})


if __name__ == "__main__":
    unittest.main()
