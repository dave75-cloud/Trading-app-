#!/usr/bin/env python3

import copy
import tempfile
import unittest
from pathlib import Path

from controlled_rnd_executor import (
    EVIDENCE_VERSION as EXECUTION_EVIDENCE_VERSION,
    EXECUTOR_AUTHORITY,
    EXECUTOR_CAPABILITIES,
)
from rnd_lifecycle_coordinator import (
    SAFETY,
    build_work_packet,
    evaluate_candidate,
)
from task_spec_contract import VERSION as TASK_SPEC_VERSION, canonical_hash
from validation_evidence_assembler import (
    ASSEMBLER_AUTHORITY,
    ASSEMBLER_CAPABILITIES,
    EXTERNAL_VALIDATION_VERSION,
    OUTPUT_MANIFEST_VERSION,
    PATH_MANIFEST_VERSION,
    AssemblerError,
    _write_pair,
    assemble_evidence,
    assembly_exit_code,
)


BASE = "1" * 40
HEAD = "2" * 40
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def task_spec(labels=None):
    if labels is None:
        labels = ["diff-check", "scope-check", "unit-tests", "workspace-audit"]
    return {
        "contract_version": TASK_SPEC_VERSION,
        "task_id": "RND-0022",
        "title": "Validation evidence assembler",
        "git_base": BASE,
        "objective": "Assemble validation evidence without executing it.",
        "allowed_path_prefixes": ["rnd/"],
        "prohibited_path_prefixes": ["rnd/private/"],
        "required_outputs": [
            "rnd/orchestration/validation_evidence_assembler.py",
        ],
        "required_validation_labels": labels,
        "success_criteria": ["required evidence is bound to one HEAD"],
        "stop_conditions": ["provenance mismatch"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


def packet(labels=None):
    return build_work_packet(task_spec(labels=labels))


def hashed_action(label, status, digest_seed):
    observations = {}
    if label == "scope-check":
        observations = {
            "changed_paths": [
                "rnd/orchestration/validation_evidence_assembler.py",
            ],
            "violations": [],
        }
    row = {
        "action_id": label,
        "validation_label": label,
        "argv": ["/usr/bin/git", "diff"],
        "working_directory": "REPOSITORY_ROOT",
        "exit_code": 0 if status == "PASS" else 1,
        "timed_out": False,
        "status": status,
        "stdout": {
            "sha256": digest_seed,
            "size_bytes": 0,
            "preview": "",
            "preview_truncated": False,
        },
        "stderr": {
            "sha256": digest_seed,
            "size_bytes": 0,
            "preview": "",
            "preview_truncated": False,
        },
        "observations": observations,
    }
    row["action_evidence_sha256"] = canonical_hash(row)
    return row


def execution_evidence(work_packet):
    actions = [
        hashed_action("diff-check", "PASS", HASH_A),
        hashed_action("scope-check", "PASS", HASH_B),
    ]
    body = {
        "execution_evidence_version": EXECUTION_EVIDENCE_VERSION,
        "executor_version": "RND-controlled-executor-v0.1",
        "task_id": "RND-0022",
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": work_packet[
            "work_packet_content_sha256"
        ],
        "execution_plan_content_sha256": HASH_C,
        "overall_status": "PASS",
        "actions": actions,
        "validations": [
            {
                "label": row["validation_label"],
                "status": row["status"],
                "evidence_sha256": row["action_evidence_sha256"],
            }
            for row in actions
        ],
        "authority": dict(EXECUTOR_AUTHORITY),
        "capabilities": dict(EXECUTOR_CAPABILITIES),
    }
    body["execution_evidence_content_sha256"] = canonical_hash(body)
    return body


def external(work_packet, label, status="PASS", producer="trusted-runner"):
    body = {
        "external_validation_version": EXTERNAL_VALIDATION_VERSION,
        "task_id": "RND-0022",
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": work_packet[
            "work_packet_content_sha256"
        ],
        "label": label,
        "status": status,
        "evidence_sha256": HASH_D,
        "producer_id": producer,
    }
    body["external_validation_content_sha256"] = canonical_hash(body)
    return body


def path_manifest(work_packet):
    body = {
        "path_manifest_version": PATH_MANIFEST_VERSION,
        "task_id": "RND-0022",
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": work_packet[
            "work_packet_content_sha256"
        ],
        "changed_paths": [
            "rnd/orchestration/validation_evidence_assembler.py",
        ],
    }
    body["path_manifest_content_sha256"] = canonical_hash(body)
    return body


def output_manifest(work_packet):
    body = {
        "output_manifest_version": OUTPUT_MANIFEST_VERSION,
        "task_id": "RND-0022",
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": work_packet[
            "work_packet_content_sha256"
        ],
        "outputs": [
            {
                "path": "rnd/orchestration/validation_evidence_assembler.py",
                "sha256": HASH_A,
            }
        ],
    }
    body["output_manifest_content_sha256"] = canonical_hash(body)
    return body


class EvidenceAssemblerTests(unittest.TestCase):
    def assemble(self, labels=None, external_rows=None):
        wp = packet(labels=labels)
        if external_rows is None:
            external_rows = [
                external(wp, "unit-tests"),
                external(wp, "workspace-audit"),
            ]
        return wp, assemble_evidence(
            wp,
            execution_evidence(wp),
            external_rows,
            path_manifest(wp),
            output_manifest(wp),
        )

    def test_valid_inputs_produce_deterministic_candidate_and_provenance(self):
        wp, first = self.assemble()
        _, second = self.assemble()
        self.assertEqual(first, second)
        candidate, provenance = first
        self.assertEqual(provenance["assembly_status"], "PASS")
        self.assertEqual(candidate["task_id"], "RND-0022")
        self.assertEqual(len(candidate["validations"]), 4)
        self.assertEqual(
            provenance["candidate_evidence_sha256"],
            canonical_hash(candidate),
        )

    def test_tampered_executor_authority_fails_closed(self):
        wp = packet()
        execution = execution_evidence(wp)
        execution["authority"]["automatic_merge"] = True
        execution["execution_evidence_content_sha256"] = canonical_hash(
            {k: v for k, v in execution.items() if k != "execution_evidence_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "authority boundary invalid"):
            assemble_evidence(
                wp,
                execution,
                [],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_path_manifest_must_match_scope_check_evidence(self):
        wp = packet()
        paths = path_manifest(wp)
        paths["changed_paths"] = ["rnd/orchestration/other.py"]
        paths["path_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in paths.items() if k != "path_manifest_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "does not match RND-0021 scope-check"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                paths,
                output_manifest(wp),
            )

    def test_mismatched_candidate_head_fails_closed(self):
        wp = packet()
        ext = external(wp, "unit-tests")
        ext["repository_head_sha"] = "3" * 40
        ext["external_validation_content_sha256"] = canonical_hash(
            {k: v for k, v in ext.items() if k != "external_validation_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "HEAD mismatch"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [ext, external(wp, "workspace-audit")],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_mismatched_task_id_fails_closed(self):
        wp = packet()
        ext = external(wp, "unit-tests")
        ext["task_id"] = "RND-9999"
        ext["external_validation_content_sha256"] = canonical_hash(
            {k: v for k, v in ext.items() if k != "external_validation_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "task_id mismatch"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [ext],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_mismatched_git_base_fails_closed(self):
        wp = packet()
        paths = path_manifest(wp)
        paths["git_base"] = "3" * 40
        paths["path_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in paths.items() if k != "path_manifest_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "git_base mismatch"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                paths,
                output_manifest(wp),
            )

    def test_mismatched_work_packet_hash_fails_closed(self):
        wp = packet()
        outputs = output_manifest(wp)
        outputs["work_packet_content_sha256"] = HASH_B
        outputs["output_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in outputs.items() if k != "output_manifest_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "work-packet hash mismatch"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                path_manifest(wp),
                outputs,
            )

    def test_tampered_execution_evidence_hash_fails_closed(self):
        wp = packet()
        execution = execution_evidence(wp)
        execution["execution_evidence_content_sha256"] = HASH_A
        with self.assertRaisesRegex(AssemblerError, "content hash mismatch"):
            assemble_evidence(
                wp,
                execution,
                [],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_tampered_action_evidence_hash_fails_closed(self):
        wp = packet()
        execution = execution_evidence(wp)
        execution["actions"][0]["action_evidence_sha256"] = HASH_A
        execution["execution_evidence_content_sha256"] = canonical_hash(
            {k: v for k, v in execution.items() if k != "execution_evidence_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "action evidence: content hash mismatch"):
            assemble_evidence(
                wp,
                execution,
                [],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_malformed_external_schema_fails_closed(self):
        wp = packet()
        row = external(wp, "unit-tests")
        row["producer_id"] = ""
        row["external_validation_content_sha256"] = canonical_hash(
            {k: v for k, v in row.items() if k != "external_validation_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "producer_id"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [row],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_invalid_external_evidence_sha_fails_closed(self):
        wp = packet()
        row = external(wp, "unit-tests")
        row["evidence_sha256"] = "bad"
        row["external_validation_content_sha256"] = canonical_hash(
            {k: v for k, v in row.items() if k != "external_validation_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "invalid SHA-256"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [row],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_duplicate_validation_label_fails_closed(self):
        wp = packet()
        with self.assertRaisesRegex(AssemblerError, "duplicate validation label"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [
                    external(wp, "unit-tests"),
                    external(wp, "unit-tests", producer="other"),
                ],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_unknown_extra_validation_label_fails_closed(self):
        wp = packet()
        with self.assertRaisesRegex(AssemblerError, "unknown external validation label"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [external(wp, "unexpected")],
                path_manifest(wp),
                output_manifest(wp),
            )

    def test_missing_required_label_is_review_required(self):
        wp = packet()
        candidate, provenance = assemble_evidence(
            wp,
            execution_evidence(wp),
            [external(wp, "unit-tests")],
            path_manifest(wp),
            output_manifest(wp),
        )
        self.assertEqual(provenance["assembly_status"], "REVIEW_REQUIRED")
        self.assertEqual(
            provenance["missing_validation_labels"],
            ["workspace-audit"],
        )
        self.assertEqual(assembly_exit_code(provenance), 2)
        review = evaluate_candidate(task_spec(), wp, candidate)
        self.assertEqual(review["machine_status"], "REVIEW_REQUIRED")

    def test_failed_validation_is_preserved(self):
        wp = packet()
        candidate, provenance = assemble_evidence(
            wp,
            execution_evidence(wp),
            [
                external(wp, "unit-tests", status="FAIL"),
                external(wp, "workspace-audit"),
            ],
            path_manifest(wp),
            output_manifest(wp),
        )
        status = {
            row["label"]: row["status"]
            for row in candidate["validations"]
        }
        self.assertEqual(status["unit-tests"], "FAIL")
        self.assertEqual(provenance["assembly_status"], "PASS")
        review = evaluate_candidate(task_spec(), wp, candidate)
        self.assertEqual(review["machine_status"], "FAIL_CLOSED")

    def test_unsafe_changed_path_fails_closed(self):
        wp = packet()
        paths = path_manifest(wp)
        paths["changed_paths"] = ["rnd/../tools/frozen.py"]
        paths["path_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in paths.items() if k != "path_manifest_content_sha256"}
        )
        with self.assertRaises(AssemblerError):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                paths,
                output_manifest(wp),
            )

    def test_unsafe_output_path_fails_closed(self):
        wp = packet()
        outputs = output_manifest(wp)
        outputs["outputs"][0]["path"] = "../escape.py"
        outputs["output_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in outputs.items() if k != "output_manifest_content_sha256"}
        )
        with self.assertRaises(AssemblerError):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                path_manifest(wp),
                outputs,
            )

    def test_invalid_output_sha_fails_closed(self):
        wp = packet()
        outputs = output_manifest(wp)
        outputs["outputs"][0]["sha256"] = "bad"
        outputs["output_manifest_content_sha256"] = canonical_hash(
            {k: v for k, v in outputs.items() if k != "output_manifest_content_sha256"}
        )
        with self.assertRaisesRegex(AssemblerError, "invalid SHA-256"):
            assemble_evidence(
                wp,
                execution_evidence(wp),
                [],
                path_manifest(wp),
                outputs,
            )

    def test_emitted_candidate_is_consumable_by_rnd0020(self):
        wp, assembled = self.assemble()
        candidate, _ = assembled
        review = evaluate_candidate(task_spec(), wp, candidate)
        self.assertEqual(review["machine_status"], "PASS")

    def test_assembler_has_no_execution_or_network_authority(self):
        self.assertFalse(ASSEMBLER_CAPABILITIES["network"])
        self.assertFalse(ASSEMBLER_CAPABILITIES["subprocess"])
        self.assertFalse(ASSEMBLER_CAPABILITIES["github_api"])
        self.assertFalse(ASSEMBLER_CAPABILITIES["candidate_code_execution"])
        self.assertFalse(ASSEMBLER_CAPABILITIES["git_mutation"])
        self.assertIsNone(ASSEMBLER_AUTHORITY["human_disposition"])
        self.assertFalse(ASSEMBLER_AUTHORITY["automatic_merge"])
        self.assertFalse(ASSEMBLER_AUTHORITY["automatic_promotion"])

    def test_output_pair_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            candidate_path = Path(td) / "candidate.json"
            provenance_path = Path(td) / "provenance.json"
            candidate_path.write_text("{}\n")
            with self.assertRaisesRegex(AssemblerError, "refusing overwrite"):
                _write_pair(
                    candidate_path,
                    provenance_path,
                    {"a": 1},
                    {"b": 2},
                )


if __name__ == "__main__":
    unittest.main()
