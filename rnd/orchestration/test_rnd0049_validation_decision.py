import unittest

from rnd0049_validation_decision import classify_validation, RND0049DecisionError, CANDIDATE_FINGERPRINT, SYMBOLS


def evidence(**overrides):
    base = {
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "elapsed_calendar_days": 180,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "all_post_freeze": True,
        "all_sha_bound": True,
        "chronology_valid": True,
        "all_four_symbols": True,
        "m5_bid_ask_mid_complete_only": True,
        "no_synthetic_fill": True,
        "integrity_verifiers_pass": True,
        "candidate_mechanics_unchanged": True,
    }
    base.update(overrides)
    return base


def passing_metrics(**overrides):
    base = {
        "portfolio_terminal_equity": 1.04,
        "portfolio_realized_net_sum": 0.04,
        "pair_terminal_net_equity": {"AUDUSD": 1.01, "EURUSD": 1.02, "GBPUSD": 1.01, "USDJPY": 0.99},
        "portfolio_max_drawdown": -0.04,
        "positive_pair_contributions": {"AUDUSD": 0.01, "EURUSD": 0.02, "GBPUSD": 0.01, "USDJPY": 0.0},
        "positive_month_contributions": {"2026-10": 0.01, "2026-11": 0.01, "2026-12": 0.01, "2027-01": 0.01},
        "reconciliation_integrity_pass": True,
        "observed_bid_ask_costs": True,
    }
    base.update(overrides)
    return base


class TestRND0049Decision(unittest.TestCase):
    def test_supported_fixture(self):
        self.assertEqual(classify_validation(evidence(), passing_metrics()), "VALIDATION_SUPPORTED")

    def test_structural_failure_is_inconclusive_and_blind(self):
        self.assertEqual(classify_validation(evidence(integrity_verifiers_pass=False), None), "VALIDATION_INCONCLUSIVE_STRUCTURAL")

    def test_metrics_forbidden_on_structural_failure(self):
        with self.assertRaises(RND0049DecisionError):
            classify_validation(evidence(integrity_verifiers_pass=False), passing_metrics())

    def test_portfolio_loss_rejects(self):
        self.assertEqual(classify_validation(evidence(), passing_metrics(portfolio_terminal_equity=0.99)), "VALIDATION_REJECTED")

    def test_pair_breadth_failure_rejects(self):
        m = passing_metrics(pair_terminal_net_equity={"AUDUSD": 1.01, "EURUSD": 1.02, "GBPUSD": 0.99, "USDJPY": 0.98})
        self.assertEqual(classify_validation(evidence(), m), "VALIDATION_REJECTED")

    def test_drawdown_failure_rejects(self):
        self.assertEqual(classify_validation(evidence(), passing_metrics(portfolio_max_drawdown=-0.11)), "VALIDATION_REJECTED")

    def test_pair_concentration_failure_rejects(self):
        m = passing_metrics(positive_pair_contributions={"AUDUSD": 0.08, "EURUSD": 0.01, "GBPUSD": 0.01, "USDJPY": 0.0})
        self.assertEqual(classify_validation(evidence(), m), "VALIDATION_REJECTED")

    def test_month_concentration_failure_rejects(self):
        m = passing_metrics(positive_month_contributions={"2026-10": 0.07, "2026-11": 0.02, "2026-12": 0.01})
        self.assertEqual(classify_validation(evidence(), m), "VALIDATION_REJECTED")

    def test_authority_escalation_fails_closed(self):
        with self.assertRaises(RND0049DecisionError):
            classify_validation(evidence(broker_writes=True), None)


if __name__ == "__main__":
    unittest.main()
