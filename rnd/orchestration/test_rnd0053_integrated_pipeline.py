import unittest

from rnd0049_validation_decision import CANDIDATE_FINGERPRINT
from rnd0053_integrated_pipeline import (
    RND0053PipelineError,
    plan_accumulation,
    validation_readout,
    request_lifecycle_transition,
    evaluate_fixture_shadow,
    authority_snapshot,
)


SYMBOLS = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]


def ledger(**overrides):
    base = {
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "verified_end_utc": "2026-10-05T07:35:00Z",
        "next_tranche_number": 2,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
    base.update(overrides)
    return base


def evidence(**overrides):
    base = {
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": SYMBOLS,
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


def supported_metrics(**overrides):
    base = {
        "portfolio_terminal_equity": 1.02,
        "portfolio_realized_net_sum": 0.04,
        "portfolio_max_drawdown": -0.05,
        "pair_terminal_net_equity": {
            "AUDUSD": 1.02,
            "EURUSD": 1.01,
            "GBPUSD": 1.00,
            "USDJPY": 0.99,
        },
        "positive_pair_contributions": {
            "AUDUSD": 0.04,
            "EURUSD": 0.03,
            "GBPUSD": 0.02,
            "USDJPY": 0.01,
        },
        "positive_month_contributions": {
            "m1": 0.02,
            "m2": 0.02,
            "m3": 0.01,
        },
        "reconciliation_integrity_pass": True,
        "observed_bid_ask_costs": True,
    }
    base.update(overrides)
    return base


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


class TestRND0053IntegratedPipeline(unittest.TestCase):
    def test_accumulation_planning_preserved(self):
        out = plan_accumulation(ledger(), "2026-10-06T07:35:00Z")
        self.assertEqual(out["status"], "NOT_YET_RUNNABLE")
        self.assertEqual(out["window"]["end_utc"], "2026-10-12T07:35:00Z")

    def test_eligible_readout_waits_for_human_gate(self):
        out = validation_readout(evidence(), validation_readout_authorized=False)
        self.assertEqual(out["status"], "READOUT_ELIGIBLE_PENDING_HUMAN_GATE")
        self.assertFalse(out["broker_writes"])

    def test_metrics_cannot_be_peeked_without_human_gate(self):
        with self.assertRaises(RND0053PipelineError):
            validation_readout(evidence(), supported_metrics(), validation_readout_authorized=False)

    def test_structural_failure_forbids_metrics(self):
        with self.assertRaises(RND0053PipelineError):
            validation_readout(evidence(integrity_verifiers_pass=False), supported_metrics())

    def test_structural_failure_is_inconclusive_without_economic_open(self):
        out = validation_readout(evidence(integrity_verifiers_pass=False))
        self.assertEqual(out, "VALIDATION_INCONCLUSIVE_STRUCTURAL")

    def test_authorized_supported_readout(self):
        out = validation_readout(evidence(), supported_metrics(), validation_readout_authorized=True)
        self.assertEqual(out, "VALIDATION_SUPPORTED")

    def test_authorized_failed_economics_rejects(self):
        bad = supported_metrics(portfolio_terminal_equity=0.99)
        out = validation_readout(evidence(), bad, validation_readout_authorized=True)
        self.assertEqual(out, "VALIDATION_REJECTED")

    def test_rejected_candidate_cannot_enter_shadow(self):
        out = request_lifecycle_transition("VALIDATION_REJECTED", "SHADOW_ELIGIBLE", human_authorized=True)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["reason"], "REJECTED_CANDIDATE_TERMINAL")

    def test_supported_candidate_still_needs_human_transition(self):
        out = request_lifecycle_transition("VALIDATION_SUPPORTED", "SHADOW_ELIGIBLE", human_authorized=False)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["reason"], "HUMAN_AUTHORIZATION_REQUIRED")

    def test_shadow_fixture_requires_shadow_active(self):
        out = evaluate_fixture_shadow(intent(), policy(), lifecycle_state="SHADOW_ELIGIBLE")
        self.assertEqual(out["decision"], "SHADOW_REJECT")
        self.assertIn("LIFECYCLE_NOT_SHADOW_ACTIVE", out["reasons"])

    def test_shadow_fixture_accepts_but_remains_zero_write(self):
        out = evaluate_fixture_shadow(intent(), policy(), lifecycle_state="SHADOW_ACTIVE")
        self.assertEqual(out["decision"], "SHADOW_ACCEPT")
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["execution_authority"])

    def test_kill_switch_still_rejects(self):
        out = evaluate_fixture_shadow(intent(), policy(kill_switch=True), lifecycle_state="SHADOW_ACTIVE")
        self.assertEqual(out["decision"], "SHADOW_REJECT")
        self.assertIn("KILL_SWITCH_ACTIVE", out["reasons"])

    def test_hostile_authority_request_cannot_enable_broker_before_execution(self):
        out = authority_snapshot("SHADOW_ACTIVE", {
            "shadow_authorized": True,
            "risk_policy_authorized": True,
            "broker_writes_authorized": True,
            "capital_authority": True,
            "live_environment_authorized": True,
        })
        self.assertFalse(out["broker_writes_authorized"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["live_environment_authorized"])


if __name__ == "__main__":
    unittest.main()
