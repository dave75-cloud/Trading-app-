import unittest

from rnd0056_portfolio_risk import evaluate_portfolio_intent, CANDIDATE_FINGERPRINT


POLICY = {
    "kill_switch": False,
    "max_intent_units": 10,
    "max_pair_abs_units": 12,
    "max_gross_units": 24,
    "max_net_units": 12,
    "max_active_pairs": 3,
    "max_currency_leg_units": 18,
}


def intent(**overrides):
    out = {
        "intent_id": "i-1",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbol": "AUDUSD",
        "side": "LONG",
        "requested_units": 5,
        "broker_writes": False,
        "capital_authority": False,
    }
    out.update(overrides)
    return out


class TestRND0056PortfolioRisk(unittest.TestCase):
    def test_accepts_bounded_fixture(self):
        out = evaluate_portfolio_intent(intent(), {}, POLICY)
        self.assertEqual(out["decision"], "SHADOW_ACCEPT")
        self.assertFalse(out["broker_writes"])

    def test_duplicate_rejected(self):
        out = evaluate_portfolio_intent(intent(), {}, POLICY, seen_intent_ids=["i-1"])
        self.assertIn("DUPLICATE_INTENT", out["reasons"])

    def test_kill_switch_rejected(self):
        p = dict(POLICY, kill_switch=True)
        self.assertIn("KILL_SWITCH_ACTIVE", evaluate_portfolio_intent(intent(), {}, p)["reasons"])

    def test_pair_limit_rejected(self):
        i = intent(requested_units=13)
        p = dict(POLICY, max_intent_units=20)
        self.assertIn("PAIR_POSITION_LIMIT", evaluate_portfolio_intent(i, {}, p)["reasons"])

    def test_gross_limit_rejected(self):
        pos = {"EURUSD": 10, "GBPUSD": -10}
        p = dict(POLICY, max_gross_units=20)
        self.assertIn("GROSS_EXPOSURE_LIMIT", evaluate_portfolio_intent(intent(requested_units=5), pos, p)["reasons"])

    def test_net_limit_rejected(self):
        pos = {"EURUSD": 8}
        p = dict(POLICY, max_net_units=10)
        self.assertIn("NET_EXPOSURE_LIMIT", evaluate_portfolio_intent(intent(requested_units=5), pos, p)["reasons"])

    def test_active_pair_limit_rejected(self):
        pos = {"EURUSD": 2, "GBPUSD": -2, "USDJPY": 2}
        self.assertIn("ACTIVE_PAIR_LIMIT", evaluate_portfolio_intent(intent(requested_units=2), pos, POLICY)["reasons"])

    def test_currency_leg_aggregation(self):
        out = evaluate_portfolio_intent(intent(symbol="USDJPY", side="LONG", requested_units=5), {"EURUSD": 4}, POLICY)
        self.assertEqual(out["projected_currency_legs"]["USD"], 1.0)
        self.assertEqual(out["projected_currency_legs"]["JPY"], -5.0)

    def test_currency_leg_limit_rejected(self):
        pos = {"AUDUSD": 8, "EURUSD": 8}
        p = dict(POLICY, max_gross_units=40, max_net_units=40, max_currency_leg_units=10)
        out = evaluate_portfolio_intent(intent(symbol="GBPUSD", requested_units=8), pos, p)
        self.assertIn("CURRENCY_LEG_LIMIT", out["reasons"])

    def test_authority_escalation_rejected(self):
        out = evaluate_portfolio_intent(intent(broker_writes=True), {}, POLICY)
        self.assertIn("AUTHORITY_ESCALATION", out["reasons"])
        self.assertFalse(out["execution_authority"])


if __name__ == "__main__":
    unittest.main()
