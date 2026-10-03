#!/usr/bin/env python3

import copy
import json
import unittest
from pathlib import Path

from rnd0035_bounded_runner import (
    PLAN_PATH,
    RND0035RunnerError,
    fixture_self_check,
    historical_run_prohibited,
)
from rnd0035_trial_plan import validate_plan


class RND0035BoundedRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(Path(PLAN_PATH).read_text(encoding="utf-8"))

    def test_fixture_self_check_is_non_historical_and_closed(self):
        result = fixture_self_check(validate_plan(copy.deepcopy(self.plan)))
        self.assertEqual("PASS", result["status"])
        self.assertEqual("SYNTHETIC_FIXTURE_ONLY", result["mode"])
        self.assertFalse(result["historical_outcomes_generated"])
        self.assertFalse(result["global_outcome_gate_open"])
        self.assertTrue(result["integrated_sensitive_families"])
        for trial_id in ("E001", "E002", "F001", "F002", "F003", "F004"):
            self.assertIn(trial_id, result["checks"])

    def test_fixture_check_preserves_authority_boundary(self):
        result = fixture_self_check(validate_plan(copy.deepcopy(self.plan)))
        for check in result["checks"].values():
            self.assertFalse(check["broker_writes"])
            self.assertFalse(check["capital_authority"])
            self.assertFalse(check["validation_open"])
            self.assertFalse(check["final_test_open"])

    def test_historical_evidence_fails_closed_while_gate_closed(self):
        plan = validate_plan(copy.deepcopy(self.plan))
        with self.assertRaisesRegex(RND0035RunnerError, "execution gate remains closed"):
            historical_run_prohibited(plan, "/tmp/evidence")

    def test_fixture_mode_rejects_open_gate(self):
        plan = copy.deepcopy(self.plan)
        plan["outcomes_authorized"] = True
        plan["execution_gate"]["new_outcomes_may_run"] = True
        with self.assertRaisesRegex(RND0035RunnerError, "requires global outcome gate closed"):
            fixture_self_check(plan)


if __name__ == "__main__":
    unittest.main()
