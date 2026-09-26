#!/usr/bin/env python3

import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from controlled_rnd_executor import build_execution_plan, execute_plan
from offline_evidence_rehearsal import RehearsalError, _write_outputs, rehearse_evidence
from rnd_lifecycle_coordinator import build_work_packet
from task_spec_contract import VERSION as TASK_SPEC_VERSION, canonical_hash
from validation_evidence_assembler import (
    EXTERNAL_VALIDATION_VERSION,
    OUTPUT_MANIFEST_VERSION,
    PATH_MANIFEST_VERSION,
    AssemblerError,
)


BASE = "1" * 40
HEAD = "2" * 40
OUTPUT = "rnd/rehearsal/fixture.txt"
LABELS = ["diff-check", "scope-check", "unit-tests", "workspace-audit"]


def hashed(body, field):
    body[field] = canonical_hash(body)
    return body


def task_spec():
    return {
        "contract_version": TASK_SPEC_VERSION,
        "task_id": "RND-0023",
        "title": "Offline evidence-chain rehearsal",
        "git_base": BASE,
        "objective": "Review a harmless R&D fixture from supplied evidence.",
        "allowed_path_prefixes": ["rnd/"],
        "prohibited_path_prefixes": ["rnd/private/"],
        "required_outputs": [OUTPUT],
        "required_validation_labels": list(LABELS),
        "success_criteria": ["review dossier is deterministic"],
        "stop_conditions": ["evidence mismatch"],
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }


def fake_git(argv, *, git_base=None):
    if argv[1:] == ["rev-parse", "HEAD"]:
        stdout = (HEAD + "\n").encode()
    elif argv[1] == "merge-base":
        stdout = b""
    elif "--name-only" in argv:
        stdout = OUTPUT.encode() + b"\0"
    else:
        stdout = b""
    return {
        "argv": argv,
        "working_directory": "REPOSITORY_ROOT",
        "exit_code": 0,
        "timed_out": False,
        "stdout": stdout,
        "stderr": b"",
    }


def external(packet, label, status="PASS"):
    return hashed({
        "external_validation_version": EXTERNAL_VALIDATION_VERSION,
        "task_id": packet["task_id"],
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": packet["work_packet_content_sha256"],
        "label": label,
        "status": status,
        "evidence_sha256": "a" * 64,
        "producer_id": "external-fixture-runner",
    }, "external_validation_content_sha256")


def fixture():
    spec = task_spec()
    packet = build_work_packet(spec)
    plan = build_execution_plan(packet, ["diff-check", "scope-check"])
    execution = execute_plan(packet, plan, runner=fake_git)
    common = {
        "task_id": packet["task_id"],
        "git_base": BASE,
        "repository_head_sha": HEAD,
        "work_packet_content_sha256": packet["work_packet_content_sha256"],
    }
    paths = hashed({
        "path_manifest_version": PATH_MANIFEST_VERSION,
        **common,
        "changed_paths": [OUTPUT],
    }, "path_manifest_content_sha256")
    outputs = hashed({
        "output_manifest_version": OUTPUT_MANIFEST_VERSION,
        **common,
        "outputs": [{"path": OUTPUT, "sha256": "b" * 64}],
    }, "output_manifest_content_sha256")
    validations = [external(packet, "unit-tests"), external(packet, "workspace-audit")]
    return spec, execution, validations, paths, outputs


class OfflineEvidenceRehearsalTests(unittest.TestCase):
    def test_valid_handoff_is_deterministic_and_keeps_human_gate(self):
        inputs = fixture()
        with mock.patch("subprocess.run", side_effect=AssertionError("no subprocess")):
            first = rehearse_evidence(*inputs)
            second = rehearse_evidence(*inputs)
        self.assertEqual(first, second)
        packet, candidate, provenance, dossier = first
        self.assertEqual(packet["task_id"], "RND-0023")
        self.assertEqual(provenance["repository_head_sha"], HEAD)
        self.assertEqual(provenance["assembly_status"], "PASS")
        self.assertEqual(dossier["machine_status"], "PASS")
        self.assertIsNone(dossier["authority"]["human_disposition"])
        self.assertFalse(dossier["authority"]["automatic_merge"])
        self.assertEqual(len(candidate["validations"]), 4)

    def test_missing_external_evidence_requires_review(self):
        spec, execution, validations, paths, outputs = fixture()
        _, candidate, provenance, dossier = rehearse_evidence(
            spec, execution, validations[:1], paths, outputs
        )
        self.assertEqual(provenance["assembly_status"], "REVIEW_REQUIRED")
        self.assertEqual(provenance["missing_validation_labels"], ["workspace-audit"])
        self.assertEqual(dossier["machine_status"], "REVIEW_REQUIRED")
        self.assertNotIn("workspace-audit", [r["label"] for r in candidate["validations"]])

    def test_failed_external_evidence_is_not_rewritten(self):
        spec, execution, validations, paths, outputs = fixture()
        validations[0] = external(build_work_packet(spec), "unit-tests", "FAIL")
        _, candidate, _, dossier = rehearse_evidence(
            spec, execution, validations, paths, outputs
        )
        self.assertIn({"label": "unit-tests", "status": "FAIL", "evidence_sha256": "a" * 64}, candidate["validations"])
        self.assertEqual(dossier["machine_status"], "FAIL_CLOSED")
        self.assertIn("FAILED_REQUIRED_VALIDATION", dossier["flags"])

    def test_external_evidence_from_other_head_fails_closed(self):
        spec, execution, validations, paths, outputs = fixture()
        validations[0]["repository_head_sha"] = "3" * 40
        validations[0].pop("external_validation_content_sha256")
        hashed(validations[0], "external_validation_content_sha256")
        with self.assertRaisesRegex(AssemblerError, "HEAD mismatch"):
            rehearse_evidence(spec, execution, validations, paths, outputs)

    def test_changed_path_manifest_disagreement_fails_closed(self):
        spec, execution, validations, paths, outputs = fixture()
        paths["changed_paths"] = ["rnd/rehearsal/other.txt"]
        paths.pop("path_manifest_content_sha256")
        hashed(paths, "path_manifest_content_sha256")
        with self.assertRaisesRegex(AssemblerError, "scope-check evidence"):
            rehearse_evidence(spec, execution, validations, paths, outputs)

    def test_duplicate_external_label_fails_closed(self):
        spec, execution, validations, paths, outputs = fixture()
        with self.assertRaisesRegex(AssemblerError, "duplicate validation label"):
            rehearse_evidence(spec, execution, validations + [copy.deepcopy(validations[0])], paths, outputs)

    def test_output_write_refuses_overwrite_without_partial_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "work_packet.json"
            existing = Path(tmp) / "candidate.json"
            existing.write_text("keep")
            paths = [first, existing, Path(tmp) / "provenance.json", Path(tmp) / "dossier.json"]
            with self.assertRaisesRegex(RehearsalError, "refusing overwrite"):
                _write_outputs(paths, [{}, {}, {}, {}])
            self.assertEqual(existing.read_text(), "keep")
            self.assertFalse(first.exists())


if __name__ == "__main__":
    unittest.main()
