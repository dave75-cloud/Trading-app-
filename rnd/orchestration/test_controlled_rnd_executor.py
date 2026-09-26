#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from controlled_rnd_executor import (
    ACTION_IDS,
    EXECUTOR_AUTHORITY,
    EXECUTOR_CAPABILITIES,
    EVIDENCE_VERSION,
    ExecutorError,
    GIT,
    PLAN_VERSION,
    SAFE_ENV,
    _action_argv,
    _assert_safe_git_argv,
    _run_process,
    build_execution_plan,
    execute_plan,
    execution_exit_code,
)
from rnd_lifecycle_coordinator import (
    EVIDENCE_VERSION as CANDIDATE_EVIDENCE_VERSION,
    SAFETY,
    build_work_packet,
    evaluate_candidate,
)
from task_spec_contract import VERSION as TASK_SPEC_VERSION


BASE = "1" * 40
HEAD = "2" * 40
HASH_A = "a" * 64
HASH_B = "b" * 64


def task_spec(labels=None):
    if labels is None:
        labels = list(ACTION_IDS)
    return {
        "contract_version": TASK_SPEC_VERSION,
        "task_id": "RND-0021",
        "title": "Controlled R&D executor",
        "git_base": BASE,
        "objective": "Run only fixed read-only Git validation actions.",
        "allowed_path_prefixes": ["rnd/"],
        "prohibited_path_prefixes": ["rnd/private/"],
        "required_outputs": [
            "rnd/orchestration/controlled_rnd_executor.py",
        ],
        "required_validation_labels": labels,
        "success_criteria": ["all selected validation actions pass"],
        "stop_conditions": ["unknown action", "scope violation"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


def work_packet(labels=None):
    return build_work_packet(task_spec(labels=labels))


def fake_result(argv, stdout=b"", stderr=b"", exit_code=0):
    return {
        "argv": list(argv),
        "working_directory": "REPOSITORY_ROOT",
        "exit_code": exit_code,
        "timed_out": False,
        "stdout": stdout,
        "stderr": stderr,
    }


class FakeRunner:
    def __init__(self, *, failures=None, changed=None):
        self.calls = []
        self.failures = set(failures or [])
        self.changed = changed or [
            "rnd/orchestration/controlled_rnd_executor.py",
        ]

    def __call__(self, argv, *, git_base=None):
        self.calls.append((list(argv), git_base))

        if argv == [GIT, "rev-parse", "HEAD"]:
            return fake_result(argv, stdout=(HEAD + "\n").encode())

        if argv[:3] == [GIT, "merge-base", "--is-ancestor"]:
            code = 1 if "base-probe" in self.failures else 0
            return fake_result(argv, exit_code=code)

        if "--name-only" in argv:
            raw = b"\0".join(x.encode() for x in self.changed) + b"\0"
            code = 1 if "scope-check" in self.failures else 0
            return fake_result(argv, stdout=raw, exit_code=code)

        if "--check" in argv:
            code = 1 if "diff-check" in self.failures else 0
            return fake_result(argv, stderr=b"diff problem\n" if code else b"", exit_code=code)

        raise AssertionError(f"unexpected argv: {argv}")


class ControlledExecutorTests(unittest.TestCase):
    def test_valid_allowlisted_plan_is_deterministic_and_hashed(self):
        packet = work_packet()
        first = build_execution_plan(packet, ["scope-check", "diff-check"])
        second = build_execution_plan(packet, ["diff-check", "scope-check"])
        self.assertEqual(first, second)
        self.assertEqual(first["plan_version"], PLAN_VERSION)
        self.assertEqual(len(first["execution_plan_content_sha256"]), 64)

    def test_arbitrary_command_string_is_rejected(self):
        packet = work_packet()
        with self.assertRaisesRegex(ExecutorError, "unknown action ID"):
            build_execution_plan(packet, ["python3 -c 'print(1)'"])

    def test_unknown_action_is_rejected(self):
        with self.assertRaisesRegex(ExecutorError, "unknown action ID"):
            build_execution_plan(work_packet(), ["network-check"])

    def test_duplicate_action_is_rejected(self):
        with self.assertRaisesRegex(ExecutorError, "duplicate action ID"):
            build_execution_plan(work_packet(), ["diff-check", "diff-check"])

    def test_action_not_authorized_by_work_packet_is_rejected(self):
        packet = work_packet(labels=["diff-check"])
        with self.assertRaisesRegex(ExecutorError, "not authorized"):
            build_execution_plan(packet, ["scope-check"])

    def test_work_packet_hash_mismatch_fails_closed(self):
        packet = work_packet()
        packet["work_packet_content_sha256"] = HASH_A
        with self.assertRaisesRegex(ExecutorError, "content hash mismatch"):
            build_execution_plan(packet, ["diff-check"])

    def test_execution_plan_hash_mismatch_fails_closed(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["diff-check"])
        plan["execution_plan_content_sha256"] = HASH_A
        with self.assertRaisesRegex(ExecutorError, "content hash mismatch"):
            execute_plan(packet, plan, runner=FakeRunner())

    def test_wrong_git_base_binding_fails_before_actions(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["diff-check"])
        runner = FakeRunner(failures={"base-probe"})
        with self.assertRaisesRegex(ExecutorError, "not an ancestor"):
            execute_plan(packet, plan, runner=runner)
        self.assertEqual(len(runner.calls), 2)

    def test_allowlisted_actions_execute_and_produce_hashed_evidence(self):
        packet = work_packet()
        plan = build_execution_plan(
            packet,
            ["diff-check", "scope-check"],
        )
        evidence = execute_plan(packet, plan, runner=FakeRunner())
        self.assertEqual(evidence["overall_status"], "PASS")
        self.assertEqual(evidence["execution_evidence_version"], EVIDENCE_VERSION)
        self.assertEqual(evidence["repository_head_sha"], HEAD)
        self.assertEqual(len(evidence["execution_evidence_content_sha256"]), 64)
        self.assertEqual(len(evidence["validations"]), 2)

    def test_scope_violation_records_fail(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["scope-check"])
        runner = FakeRunner(changed=["tools/m006e/frozen.py"])
        evidence = execute_plan(packet, plan, runner=runner)
        self.assertEqual(evidence["overall_status"], "FAIL")
        self.assertEqual(evidence["actions"][0]["status"], "FAIL")
        self.assertTrue(evidence["actions"][0]["observations"]["violations"])

    def test_nonzero_process_exit_records_fail_and_non_success_exit(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["diff-check"])
        evidence = execute_plan(
            packet,
            plan,
            runner=FakeRunner(failures={"diff-check"}),
        )
        self.assertEqual(evidence["overall_status"], "FAIL")
        self.assertEqual(evidence["actions"][0]["exit_code"], 1)
        self.assertEqual(execution_exit_code(evidence), 1)

    def test_stdout_stderr_hashes_are_stable_for_identical_bytes(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["diff-check"])
        first = execute_plan(packet, plan, runner=FakeRunner())
        second = execute_plan(packet, plan, runner=FakeRunner())
        self.assertEqual(
            first["actions"][0]["stdout"]["sha256"],
            second["actions"][0]["stdout"]["sha256"],
        )
        self.assertEqual(
            first["actions"][0]["stderr"]["sha256"],
            second["actions"][0]["stderr"]["sha256"],
        )

    def test_executor_authority_remains_human_only(self):
        packet = work_packet()
        plan = build_execution_plan(packet, ["diff-check"])
        evidence = execute_plan(packet, plan, runner=FakeRunner())
        self.assertEqual(evidence["authority"], EXECUTOR_AUTHORITY)
        self.assertIsNone(evidence["authority"]["human_disposition"])
        self.assertFalse(evidence["authority"]["automatic_merge"])
        self.assertFalse(evidence["authority"]["automatic_promotion"])

    def test_executor_capabilities_exclude_candidate_code_and_network(self):
        self.assertFalse(EXECUTOR_CAPABILITIES["network"])
        self.assertFalse(EXECUTOR_CAPABILITIES["candidate_code_execution"])
        self.assertFalse(EXECUTOR_CAPABILITIES["arbitrary_subprocess"])
        self.assertFalse(EXECUTOR_CAPABILITIES["shell"])
        self.assertEqual(
            EXECUTOR_CAPABILITIES["subprocess_mode"],
            "READ_ONLY_GIT_ALLOWLIST_ONLY",
        )

    def test_allowlist_contains_no_mutating_or_network_actions(self):
        self.assertEqual(
            set(ACTION_IDS),
            {"diff-check", "scope-check"},
        )

    def test_subprocess_helper_forces_shell_false_and_sanitized_environment(self):
        completed = subprocess.CompletedProcess(
            args=[GIT, "rev-parse", "HEAD"],
            returncode=0,
        )
        with mock.patch("controlled_rnd_executor.subprocess.run", return_value=completed) as run:
            result = _run_process([GIT, "rev-parse", "HEAD"])
        self.assertEqual(result["exit_code"], 0)
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["cwd"], Path(__file__).resolve().parents[2])
        self.assertEqual(kwargs["env"], SAFE_ENV)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)

    def test_worktree_status_is_not_in_subprocess_allowlist(self):
        with mock.patch("controlled_rnd_executor.subprocess.run") as run:
            with self.assertRaisesRegex(ExecutorError, "outside the Git allowlist"):
                _run_process(
                    [GIT, "status", "--porcelain=v1", "--untracked-files=all"]
                )
            run.assert_not_called()

    def test_generated_action_argv_matches_internal_allowlist(self):
        for action_id in ACTION_IDS:
            argv = _action_argv(action_id, BASE)
            _assert_safe_git_argv(argv, git_base=BASE)

    def test_non_allowlisted_git_argv_is_rejected_before_subprocess(self):
        with mock.patch("controlled_rnd_executor.subprocess.run") as run:
            with self.assertRaisesRegex(ExecutorError, "outside the Git allowlist"):
                _run_process([GIT, "checkout", "main"])
            run.assert_not_called()

    def test_execution_validations_are_consumable_by_rnd0020_evaluator(self):
        labels = ["diff-check", "scope-check"]
        spec = task_spec(labels=labels)
        packet = build_work_packet(spec)
        plan = build_execution_plan(packet, labels)
        execution = execute_plan(packet, plan, runner=FakeRunner())

        candidate = {
            "evidence_version": CANDIDATE_EVIDENCE_VERSION,
            "task_id": "RND-0021",
            "git_base": BASE,
            "work_packet_content_sha256": packet[
                "work_packet_content_sha256"
            ],
            "changed_paths": [
                "rnd/orchestration/controlled_rnd_executor.py",
            ],
            "outputs": [
                {
                    "path": "rnd/orchestration/controlled_rnd_executor.py",
                    "sha256": HASH_B,
                }
            ],
            "validations": execution["validations"],
            "safety": dict(SAFETY),
        }
        review = evaluate_candidate(spec, packet, candidate)
        self.assertEqual(review["machine_status"], "PASS")

    def test_output_overwrite_refusal_helper_contract(self):
        from controlled_rnd_executor import _write_new_json
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text("{}\n")
            with self.assertRaisesRegex(ExecutorError, "refusing overwrite"):
                _write_new_json(path, {"x": 1})


if __name__ == "__main__":
    unittest.main()
