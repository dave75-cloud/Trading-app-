import unittest

from rnd0051_shadow_risk import evaluate_shadow_intent, CANDIDATE_FINGERPRINT


def intent(**overrides):
    base = {
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "intent_id": "fixture-001",
        "symbol": "EURUSD",
        "side": "LONG",
        "decision_time_utc": "2026-10-05T08:00:00Z",
        "evidence_time_utc": "2026-10-05T07:59:00Z",
        "requested_units": 10,
        "source_state": "SHADOW_FIXTURE",
        "broker_writes": False,
        "capital_authority": False,
    }
    base.update(overrides)
    return base


def policy(**overrides):
    base = {
        "kill_switch": False,
        "max_evidence_age_seconds": 300,
        "max_fixture_units": 100,
        "projected_gross_fixture_exposure": 40,
        "max_gross_fixture_exposure": 100,
        "projected_currency_leg_fixture_exposure": 20,
        "max_currency_leg_fixture_exposure": 50,
    }
    base.update(overrides)
    return base


class TestRND0051ShadowRisk(unittest.TestCase):
    def test_accept_fixture(self):
        out = evaluate_shadow_intent(intent(), policy())
        self.assertEqual(out["decision"], "SHADOW_ACCEPT")
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["execution_authority"])

    def test_candidate_mismatch_rejects(self):
        self.assertEqual(evaluate_shadow_intent(intent(candidate_fingerprint="0" * 64), policy())["decision"], "SHADOW_REJECT")

    def test_duplicate_rejects(self):
        out = evaluate_shadow_intent(intent(), policy(), seen_intent_ids=("fixture-001",))
        self.assertIn("DUPLICATE_INTENT", out["reasons"])

    def test_stale_rejects(self):
        out = evaluate_shadow_intent(intent(evidence_time_utc="2026-10-05T07:00:00Z"), policy())
        self.assertIn("STALE_EVIDENCE", out["reasons"])

    def test_kill_switch_rejects(self):
        self.assertIn("KILL_SWITCH_ACTIVE", evaluate_shadow_intent(intent(), policy(kill_switch=True))["reasons"])

    def test_units_limit_rejects(self):
        self.assertIn("FIXTURE_UNITS_LIMIT", evaluate_shadow_intent(intent(requested_units=101), policy())["reasons"])

    def test_gross_limit_rejects(self):
        self.assertIn("GROSS_EXPOSURE_LIMIT", evaluate_shadow_intent(intent(), policy(projected_gross_fixture_exposure=101))["reasons"])

    def test_currency_leg_limit_rejects(self):
        self.assertIn("CURRENCY_LEG_LIMIT", evaluate_shadow_intent(intent(), policy(projected_currency_leg_fixture_exposure=51))["reasons"])

    def test_authority_escalation_rejects(self):
        out = evaluate_shadow_intent(intent(broker_writes=True), policy())
        self.assertIn("BROKER_WRITES_NOT_FALSE", out["reasons"])


if __name__ == "__main__":
    unittest.main()
