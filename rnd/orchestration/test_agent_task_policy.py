#!/usr/bin/env python3

import copy
import unittest

from agent_task_policy import (
    APPROVAL_VERSION,
    AgentPolicyError,
    assess_review_handoff,
    assess_task_intake,
)
from rnd_lifecycle_coordinator import SAFETY, build_work_packet, evaluate_candidate
from task_spec_contract import VERSION as TASK_SPEC_VERSION, canonical_hash, validate_task_spec


BASE = "1" * 40
OUTPUT = "rnd/governance/report.md"


def spec():
    return {
        "contract_version": TASK_SPEC_VERSION,
        "task_id": "RND-0024",
        "title": "Agent governance",
        "git_base": BASE,
        "objective": "Rehearse agent task intake under human governance.",
        "allowed_path_prefixes": ["rnd/"],
        "prohibited_path_prefixes": ["rnd/private/"],
        "required_outputs": [OUTPUT],
        "required_validation_labels": ["unit-tests"],
        "success_criteria": ["the dossier is reviewable"],
        "stop_conditions": ["scope or provenance mismatch"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


def queued():
    return [{
        "task_id": "RND-0024",
        "status": "queued",
        "timestamp_utc": "2026-09-23T10:40:00Z",
        "human_gate_required": True,
        "protected_paths_allowed": False,
        "title": "Agent governance",
    }]


def approval(task_spec):
    record = {
        "approval_version": APPROVAL_VERSION,
        "task_id": task_spec["task_id"],
        "git_base": task_spec["git_base"],
        "task_spec_sha256": canonical_hash(validate_task_spec(task_spec)),
        "decision": "APPROVED",
        "approver_role": "HUMAN",
        "approver_id": "external-human-operator",
        "approved_at_utc": "2026-09-23T10:41:00Z",
    }
    record["approval_content_sha256"] = canonical_hash(record)
    return record


def dossier(task_spec, status="PASS"):
    packet = build_work_packet(task_spec)
    validations = []
    if status != "REVIEW_REQUIRED":
        validations = [{
            "label": "unit-tests",
            "status": "FAIL" if status == "FAIL_CLOSED" else "PASS",
            "evidence_sha256": "a" * 64,
        }]
    candidate = {
        "evidence_version": "RND-candidate-evidence-v0.1",
        "task_id": task_spec["task_id"],
        "git_base": task_spec["git_base"],
        "work_packet_content_sha256": packet["work_packet_content_sha256"],
        "changed_paths": [OUTPUT],
        "outputs": [{"path": OUTPUT, "sha256": "b" * 64}],
        "validations": validations,
        "safety": dict(SAFETY),
    }
    return evaluate_candidate(task_spec, packet, candidate)


class AgentTaskPolicyTests(unittest.TestCase):
    def test_consistent_claim_is_not_task_acceptance(self):
        task = spec()
        result = assess_task_intake(task, queued(), approval(task), [OUTPUT])
        self.assertEqual(result["policy_status"], "DECLARATIONS_CONSISTENT")
        self.assertFalse(result["human_identity_authenticated"])
        self.assertFalse(result["task_accepted"])
        self.assertEqual(result["execution_authority"], "NONE")

    def test_missing_approval_requires_review(self):
        result = assess_task_intake(spec(), queued(), None, [OUTPUT])
        self.assertEqual(result["policy_status"], "REVIEW_REQUIRED")

    def test_rehashed_approval_for_other_task_is_rejected(self):
        task = spec()
        record = approval(task)
        record["task_spec_sha256"] = "0" * 64
        record.pop("approval_content_sha256")
        record["approval_content_sha256"] = canonical_hash(record)
        with self.assertRaisesRegex(AgentPolicyError, "task-spec hash mismatch"):
            assess_task_intake(task, queued(), record, [OUTPUT])

    def test_declared_agent_approval_is_rejected_even_when_rehashed(self):
        task = spec()
        record = approval(task)
        record["approver_role"] = "AGENT"
        record.pop("approval_content_sha256")
        record["approval_content_sha256"] = canonical_hash(record)
        with self.assertRaisesRegex(AgentPolicyError, "human approval"):
            assess_task_intake(task, queued(), record, [OUTPUT])

    def test_out_of_scope_or_prohibited_paths_are_rejected(self):
        task = spec()
        record = approval(task)
        for path in ("tools/m006e/config.py", "rnd/private/secret.txt", "rnd/../cli/x"):
            with self.subTest(path=path), self.assertRaises(AgentPolicyError):
                assess_task_intake(task, queued(), record, [path])

    def test_running_or_duplicated_queue_state_cannot_be_accepted(self):
        task = spec()
        record = approval(task)
        running = copy.deepcopy(queued())
        running[0]["status"] = "running"
        for events in (running, queued() + running):
            with self.subTest(events=events), self.assertRaisesRegex(
                AgentPolicyError, "exactly one queued event"
            ):
                assess_task_intake(task, events, record, [OUTPUT])

    def test_malformed_event_stream_is_rejected(self):
        task = spec()
        with self.assertRaisesRegex(AgentPolicyError, "task event must be an object"):
            assess_task_intake(task, queued() + ["not an event"], approval(task), [OUTPUT])

    def test_machine_pass_still_requires_human_review(self):
        task = spec()
        result = assess_review_handoff(task, dossier(task))
        self.assertEqual(result["handoff_status"], "HUMAN_REVIEW_REQUIRED")
        self.assertIsNone(result["human_disposition"])
        self.assertFalse(result["automatic_merge"])

    def test_missing_or_failed_evidence_does_not_reach_merge_handoff(self):
        task = spec()
        self.assertEqual(
            assess_review_handoff(task, dossier(task, "REVIEW_REQUIRED"))["handoff_status"],
            "INCOMPLETE",
        )
        self.assertEqual(
            assess_review_handoff(task, dossier(task, "FAIL_CLOSED"))["handoff_status"],
            "BLOCKED",
        )

    def test_rehashed_dossier_with_expanded_authority_fails_closed(self):
        task = spec()
        review = dossier(task)
        review["authority"]["automatic_merge"] = True
        review.pop("review_dossier_content_sha256")
        review["review_dossier_content_sha256"] = canonical_hash(review)
        with self.assertRaisesRegex(AgentPolicyError, "expands authority"):
            assess_review_handoff(task, review)


if __name__ == "__main__":
    unittest.main()
