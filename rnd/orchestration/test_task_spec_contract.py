#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_spec_contract import TaskSpecError, VERSION, validate_task_spec


BASE = "1" * 40


def valid_spec():
    return {
        "contract_version": VERSION,
        "task_id": "RND-0020",
        "title": "Lifecycle coordinator",
        "git_base": BASE,
        "objective": "Build a bounded offline coordinator.",
        "allowed_path_prefixes": ["rnd/orchestration/"],
        "prohibited_path_prefixes": ["rnd/orchestration/private/"],
        "required_outputs": [
            "rnd/orchestration/task_spec_contract.py",
            "rnd/orchestration/rnd_lifecycle_coordinator.py",
        ],
        "required_validation_labels": ["focused-tests", "workspace-audit"],
        "success_criteria": ["all required validations pass"],
        "stop_conditions": ["scope ambiguity"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


class TaskSpecContractTests(unittest.TestCase):
    def test_valid_spec_normalizes_deterministically(self):
        first = validate_task_spec(valid_spec())
        second = validate_task_spec(valid_spec())
        self.assertEqual(first, second)
        self.assertEqual(first["allowed_path_prefixes"], ["rnd/orchestration"])

    def test_missing_objective_fails_closed(self):
        spec = valid_spec()
        spec["objective"] = ""
        with self.assertRaises(TaskSpecError):
            validate_task_spec(spec)

    def test_invalid_git_base_fails_closed(self):
        spec = valid_spec()
        spec["git_base"] = "abc"
        with self.assertRaises(TaskSpecError):
            validate_task_spec(spec)

    def test_authority_expanding_allowed_path_fails_closed(self):
        spec = valid_spec()
        spec["allowed_path_prefixes"] = ["tools/m006e/"]
        with self.assertRaises(TaskSpecError):
            validate_task_spec(spec)

    def test_required_output_outside_allowed_scope_fails_closed(self):
        spec = valid_spec()
        spec["required_outputs"].append("rnd/other/file.py")
        with self.assertRaises(TaskSpecError):
            validate_task_spec(spec)

    def test_merge_or_promotion_authority_fails_closed(self):
        for key in ("automatic_merge", "automatic_promotion"):
            spec = valid_spec()
            spec[key] = True
            with self.assertRaises(TaskSpecError):
                validate_task_spec(spec)


if __name__ == "__main__":
    unittest.main()
