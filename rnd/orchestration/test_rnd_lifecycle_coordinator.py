#!/usr/bin/env python3

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rnd_lifecycle_coordinator import (
    EVIDENCE_VERSION,
    SAFETY,
    LifecycleError,
    build_work_packet,
    evaluate_candidate,
)
from task_spec_contract import VERSION


BASE = "2" * 40
HASH_A = "a" * 64
HASH_B = "b" * 64


def spec():
    return {
        "contract_version": VERSION,
        "task_id": "RND-0020",
        "title": "Lifecycle coordinator",
        "git_base": BASE,
        "objective": "Coordinate offline R&D planning and evidence review.",
        "allowed_path_prefixes": ["rnd/orchestration/"],
        "prohibited_path_prefixes": ["rnd/orchestration/private/"],
        "required_outputs": [
            "rnd/orchestration/task_spec_contract.py",
            "rnd/orchestration/rnd_lifecycle_coordinator.py",
        ],
        "required_validation_labels": ["focused-tests", "workspace-audit"],
        "success_criteria": ["required validation evidence passes"],
        "stop_conditions": ["scope mismatch", "authority expansion"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


def evidence(packet):
    return {
        "evidence_version": EVIDENCE_VERSION,
        "task_id": "RND-0020",
        "git_base": BASE,
        "work_packet_content_sha256": packet["work_packet_content_sha256"],
        "changed_paths": [
            "rnd/orchestration/task_spec_contract.py",
            "rnd/orchestration/rnd_lifecycle_coordinator.py",
        ],
        "outputs": [
            {"path": "rnd/orchestration/task_spec_contract.py", "sha256": HASH_A},
            {"path": "rnd/orchestration/rnd_lifecycle_coordinator.py", "sha256": HASH_B},
        ],
        "validations": [
            {"label": "focused-tests", "status": "PASS", "evidence_sha256": HASH_A},
            {"label": "workspace-audit", "status": "PASS", "evidence_sha256": HASH_B},
        ],
        "safety": dict(SAFETY),
    }


class LifecycleCoordinatorTests(unittest.TestCase):
    def test_work_packet_is_deterministic_and_hashed(self):
        first = build_work_packet(spec())
        second = build_work_packet(spec())
        self.assertEqual(first, second)
        self.assertEqual(len(first["work_packet_content_sha256"]), 64)

    def test_valid_candidate_produces_deterministic_pass_dossier(self):
        packet = build_work_packet(spec())
        first = evaluate_candidate(spec(), packet, evidence(packet))
        second = evaluate_candidate(spec(), packet, evidence(packet))
        self.assertEqual(first, second)
        self.assertEqual(first["machine_status"], "PASS")
        self.assertIsNone(first["authority"]["human_disposition"])
        self.assertFalse(first["authority"]["automatic_merge"])
        self.assertFalse(first["authority"]["automatic_promotion"])

    def test_work_packet_spec_mismatch_fails_closed(self):
        packet = build_work_packet(spec())
        other = spec()
        other["objective"] = "different objective"
        with self.assertRaisesRegex(LifecycleError, "does not match"):
            evaluate_candidate(other, packet, evidence(packet))

    def test_work_packet_hash_mismatch_fails_closed(self):
        packet = build_work_packet(spec())
        packet["work_packet_content_sha256"] = HASH_A
        with self.assertRaisesRegex(LifecycleError, "content hash mismatch"):
            evaluate_candidate(spec(), packet, evidence(build_work_packet(spec())))

    def test_wrong_git_base_fails_closed(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["git_base"] = "3" * 40
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertEqual(dossier["machine_status"], "FAIL_CLOSED")
        self.assertIn("GIT_BASE_MISMATCH", dossier["flags"])

    def test_changed_path_outside_allowed_scope_fails_closed(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["changed_paths"].append("rnd/other/file.py")
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertIn("CHANGED_PATH_OUTSIDE_ALLOWED_SCOPE", dossier["flags"])

    def test_changed_protected_path_fails_closed(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["changed_paths"].append("tools/m006e/frozen.py")
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertEqual(dossier["machine_status"], "FAIL_CLOSED")
        self.assertIn("PROTECTED_PATH_CHANGED", dossier["flags"])

    def test_missing_required_output_requires_review(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["outputs"] = candidate["outputs"][:1]
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertEqual(dossier["machine_status"], "REVIEW_REQUIRED")
        self.assertIn("MISSING_REQUIRED_OUTPUT", dossier["review_flags"])

    def test_missing_required_validation_requires_review(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["validations"] = candidate["validations"][:1]
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertEqual(dossier["machine_status"], "REVIEW_REQUIRED")
        self.assertIn("MISSING_REQUIRED_VALIDATION", dossier["review_flags"])

    def test_failed_required_validation_fails_closed(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["validations"][0]["status"] = "FAIL"
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertEqual(dossier["machine_status"], "FAIL_CLOSED")
        self.assertIn("FAILED_REQUIRED_VALIDATION", dossier["flags"])

    def test_invalid_safety_declaration_fails_closed(self):
        packet = build_work_packet(spec())
        candidate = evidence(packet)
        candidate["safety"]["automatic_merge"] = True
        dossier = evaluate_candidate(spec(), packet, candidate)
        self.assertIn("SAFETY_DECLARATION_INVALID", dossier["flags"])

    def test_coordinator_declares_no_network_or_subprocess_capability(self):
        packet = build_work_packet(spec())
        dossier = evaluate_candidate(spec(), packet, evidence(packet))
        self.assertFalse(packet["capabilities"]["network"])
        self.assertFalse(packet["capabilities"]["subprocess"])
        self.assertFalse(dossier["capabilities"]["network"])
        self.assertFalse(dossier["capabilities"]["subprocess"])
        self.assertEqual(dossier["authority"]["merge_authority"], "NONE")
        self.assertEqual(dossier["authority"]["promotion_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
