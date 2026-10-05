import unittest

from rnd0052_control_state import transition, effective_authority


class TestRND0052ControlState(unittest.TestCase):
    def test_human_gate_required(self):
        out = transition("RESEARCH_FROZEN", "PROSPECTIVE_ACCUMULATING", human_authorized=False)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["reason"], "HUMAN_AUTHORIZATION_REQUIRED")

    def test_human_gate_allows_declared_transition(self):
        out = transition("RESEARCH_FROZEN", "PROSPECTIVE_ACCUMULATING", human_authorized=True)
        self.assertTrue(out["allowed"])
        self.assertEqual(out["state"], "PROSPECTIVE_ACCUMULATING")

    def test_rejected_candidate_terminal(self):
        out = transition("VALIDATION_REJECTED", "SHADOW_ELIGIBLE", human_authorized=True)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["reason"], "REJECTED_CANDIDATE_TERMINAL")

    def test_skip_transition_rejected(self):
        out = transition("VALIDATION_SUPPORTED", "SHADOW_ACTIVE", human_authorized=True)
        self.assertFalse(out["allowed"])

    def test_unknown_state_rejected(self):
        self.assertFalse(transition("UNKNOWN", "SHADOW_ACTIVE", human_authorized=True)["allowed"])

    def test_state_does_not_grant_shadow(self):
        auth = effective_authority("VALIDATION_SUPPORTED", {"shadow_authorized": True})
        self.assertFalse(auth["shadow_authorized"])

    def test_pre_execution_state_forces_broker_false(self):
        auth = effective_authority("SHADOW_ACTIVE", {"broker_writes_authorized": True, "capital_authority": True, "live_environment_authorized": True})
        self.assertFalse(auth["broker_writes_authorized"])
        self.assertFalse(auth["capital_authority"])
        self.assertFalse(auth["live_environment_authorized"])

    def test_missing_authority_defaults_false(self):
        auth = effective_authority("EXECUTION_ELIGIBLE", {})
        self.assertTrue(all(value is False for value in auth.values()))

    def test_structural_inconclusive_can_return_to_accumulation_with_human_gate(self):
        out = transition("VALIDATION_INCONCLUSIVE_STRUCTURAL", "PROSPECTIVE_ACCUMULATING", human_authorized=True)
        self.assertTrue(out["allowed"])


if __name__ == "__main__":
    unittest.main()
