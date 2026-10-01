import copy
import json
import unittest
from pathlib import Path

from rnd0035_trial_plan import RND0035PlanError, validate_plan


PLAN_PATH = Path(__file__).parents[1] / "research" / "RND0035_TRIAL_PLAN.json"


class RND0035TrialPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_repository_plan_is_valid_and_pre_outcome(self):
        plan = validate_plan(copy.deepcopy(self.plan))
        self.assertFalse(plan["outcomes_authorized"])
        self.assertFalse(plan["execution_gate"]["new_outcomes_may_run"])
        self.assertEqual(36, plan["declared_strategy_variant_trials"]["total_including_reference"])
        self.assertEqual(9, plan["declared_resampling_configurations"])

    def test_opening_any_sensitive_authority_fails_closed(self):
        for key in ("outcomes_authorized", "validation_open", "final_test_open", "strategy_selection", "broker_writes", "capital_authority"):
            plan = copy.deepcopy(self.plan)
            plan[key] = True
            with self.subTest(key=key):
                with self.assertRaises(RND0035PlanError):
                    validate_plan(plan)

    def test_parameter_cartesian_search_is_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["design_principles"]["no_cartesian_parameter_grid"] = False
        with self.assertRaises(RND0035PlanError):
            validate_plan(plan)

    def test_duplicate_trial_id_is_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["families"]["C_SESSION"]["trials"][0]["trial_id"] = "A001"
        with self.assertRaises(RND0035PlanError):
            validate_plan(plan)

    def test_undeclared_family_is_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["families"]["H_OPTIMIZE"] = {"grid_frozen": True, "outcomes_authorized": False}
        with self.assertRaises(RND0035PlanError):
            validate_plan(plan)

    def test_bootstrap_researcher_degrees_of_freedom_are_frozen(self):
        for key, value in (
            ("replications_per_configuration", 9999),
            ("seeds", [1, 2, 3]),
            ("expected_block_lengths_trades", [5, 10, 20]),
        ):
            plan = copy.deepcopy(self.plan)
            plan["families"]["G_DEPENDENCE_RESAMPLING"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(RND0035PlanError):
                    validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
