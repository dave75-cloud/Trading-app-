#!/usr/bin/env python3
"""Pure, advisory checks for new R&D task intake and review handoff."""

from __future__ import annotations

import re
from datetime import datetime

from rnd_lifecycle_coordinator import build_work_packet, REVIEW_VERSION
from task_spec_contract import (
    KNOWN_PROTECTED_PREFIXES,
    SHA256_RE,
    TaskSpecError,
    canonical_hash,
    normalize_repo_path,
    path_within,
    validate_task_spec,
)


APPROVAL_VERSION = "RND-external-task-approval-v0.1"
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

REVIEW_AUTHORITY = {
    "human_disposition": None,
    "human_notes": None,
    "human_gate_required": True,
    "automatic_merge": False,
    "automatic_promotion": False,
    "merge_authority": "NONE",
    "promotion_authority": "NONE",
}
REVIEW_CAPABILITIES = {
    "network": False,
    "subprocess": False,
    "github_api": False,
    "broker_transport": False,
    "submission": False,
}
REVIEW_DOSSIER_FIELDS = {
    "review_version", "task_id", "git_base", "work_packet_content_sha256",
    "machine_status", "flags", "review_flags", "candidate_evidence_sha256",
    "evidence_summary", "authority", "capabilities",
    "review_dossier_content_sha256",
}
EVIDENCE_SUMMARY_FIELDS = {
    "changed_paths", "output_sha256", "validations",
    "missing_required_outputs", "missing_required_validations",
    "failed_required_validations",
}
OPAQUE_EVALUATOR_FLAGS = {
    "TASK_ID_MISMATCH", "GIT_BASE_MISMATCH", "WORK_PACKET_HASH_MISMATCH",
    "SAFETY_DECLARATION_INVALID",
}


class AgentPolicyError(ValueError):
    pass


def _utc(value, role):
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise AgentPolicyError(f"{role}: invalid UTC timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise AgentPolicyError(f"{role}: invalid UTC timestamp") from exc


def _verify_hash(value, field, role):
    if not isinstance(value, dict):
        raise AgentPolicyError(f"{role}: expected JSON object")
    digest = value.get(field)
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise AgentPolicyError(f"{role}: invalid content hash")
    body = dict(value)
    body.pop(field)
    if digest != canonical_hash(body):
        raise AgentPolicyError(f"{role}: content hash mismatch")


def _check_paths(spec, proposed_paths):
    if not isinstance(proposed_paths, list) or not proposed_paths:
        raise AgentPolicyError("proposed paths must be a non-empty list")
    normalized = []
    for path in proposed_paths:
        try:
            clean = normalize_repo_path(path, "proposed path")
        except TaskSpecError as exc:
            raise AgentPolicyError(str(exc)) from exc
        if path != clean:
            raise AgentPolicyError("proposed path must already be normalized")
        if not any(path_within(clean, prefix) for prefix in spec["allowed_path_prefixes"]):
            raise AgentPolicyError("proposed path is outside task scope")
        if any(path_within(clean, prefix) for prefix in spec["prohibited_path_prefixes"]):
            raise AgentPolicyError("proposed path is prohibited")
        if any(path_within(clean, prefix) for prefix in KNOWN_PROTECTED_PREFIXES):
            raise AgentPolicyError("proposed path is protected")
        normalized.append(clean)
    if len(normalized) != len(set(normalized)):
        raise AgentPolicyError("duplicate proposed path")
    return sorted(normalized)


def _check_queued_event(task_id, task_events):
    if not isinstance(task_events, list):
        raise AgentPolicyError("task events must be a list")
    if any(not isinstance(row, dict) for row in task_events):
        raise AgentPolicyError("task event must be an object")
    own = [row for row in task_events if row.get("task_id") == task_id]
    if len(own) != 1 or own[0].get("status") != "queued":
        raise AgentPolicyError("new task must have exactly one queued event")
    if own[0].get("human_gate_required") is not True:
        raise AgentPolicyError("queued event must retain human gate")
    if own[0].get("protected_paths_allowed") is not False:
        raise AgentPolicyError("queued event must deny protected paths")
    _utc(own[0].get("timestamp_utc"), "queued event")


def _check_approval(spec, record):
    _verify_hash(record, "approval_content_sha256", "approval record")
    required = {
        "approval_version", "task_id", "git_base", "task_spec_sha256",
        "decision", "approver_role", "approver_id", "approved_at_utc",
        "approval_content_sha256",
    }
    if set(record) != required:
        raise AgentPolicyError("approval record has missing or unexpected fields")
    if record["approval_version"] != APPROVAL_VERSION:
        raise AgentPolicyError("approval record version mismatch")
    if record["task_id"] != spec["task_id"] or record["git_base"] != spec["git_base"]:
        raise AgentPolicyError("approval record task/base mismatch")
    if record["task_spec_sha256"] != canonical_hash(spec):
        raise AgentPolicyError("approval record task-spec hash mismatch")
    if record["decision"] != "APPROVED" or record["approver_role"] != "HUMAN":
        raise AgentPolicyError("approval record lacks declared human approval")
    if not isinstance(record["approver_id"], str) or not record["approver_id"].strip():
        raise AgentPolicyError("approval record lacks approver identifier")
    _utc(record["approved_at_utc"], "approval record")


def assess_task_intake(task_spec, task_events, approval_record, proposed_paths):
    """Validate supplied declarations; never authenticate or accept a task."""
    spec = validate_task_spec(task_spec)
    paths = _check_paths(spec, proposed_paths)
    _check_queued_event(spec["task_id"], task_events)
    if approval_record is None:
        status = "REVIEW_REQUIRED"
    else:
        _check_approval(spec, approval_record)
        status = "DECLARATIONS_CONSISTENT"
    return {
        "policy_status": status,
        "task_id": spec["task_id"],
        "git_base": spec["git_base"],
        "task_spec_sha256": canonical_hash(spec),
        "proposed_paths": paths,
        "human_identity_authenticated": False,
        "task_accepted": False,
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "promotion_authority": "NONE",
    }


def _check_review_summary(spec, dossier):
    if set(dossier) != REVIEW_DOSSIER_FIELDS:
        raise AgentPolicyError("review dossier has missing or unexpected fields")
    candidate_hash = dossier.get("candidate_evidence_sha256")
    if not isinstance(candidate_hash, str) or not SHA256_RE.fullmatch(candidate_hash):
        raise AgentPolicyError("review dossier candidate hash invalid")

    summary = dossier.get("evidence_summary")
    if not isinstance(summary, dict) or set(summary) != EVIDENCE_SUMMARY_FIELDS:
        raise AgentPolicyError("review dossier evidence summary shape mismatch")

    changed = summary["changed_paths"]
    outputs = summary["output_sha256"]
    validations = summary["validations"]
    if not isinstance(changed, list) or not isinstance(outputs, dict) or not isinstance(validations, dict):
        raise AgentPolicyError("review dossier evidence summary malformed")

    derived_flags = []
    seen = set()
    for path in changed:
        try:
            clean = normalize_repo_path(path, "review changed path")
        except TaskSpecError as exc:
            raise AgentPolicyError(str(exc)) from exc
        if clean != path or clean in seen:
            raise AgentPolicyError("review changed paths must be normalized and unique")
        seen.add(clean)
        if any(path_within(clean, prefix) for prefix in KNOWN_PROTECTED_PREFIXES):
            derived_flags.append("PROTECTED_PATH_CHANGED")
        if not any(path_within(clean, prefix) for prefix in spec["allowed_path_prefixes"]):
            derived_flags.append("CHANGED_PATH_OUTSIDE_ALLOWED_SCOPE")
        if any(path_within(clean, prefix) for prefix in spec["prohibited_path_prefixes"]):
            derived_flags.append("PROHIBITED_PATH_CHANGED")

    for path, digest in outputs.items():
        try:
            clean = normalize_repo_path(path, "review output path")
        except TaskSpecError as exc:
            raise AgentPolicyError(str(exc)) from exc
        if clean != path or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise AgentPolicyError("review output summary invalid")
        if not any(path_within(clean, prefix) for prefix in spec["allowed_path_prefixes"]):
            derived_flags.append("OUTPUT_OUTSIDE_ALLOWED_SCOPE")
        if any(path_within(clean, prefix) for prefix in spec["prohibited_path_prefixes"]):
            derived_flags.append("PROHIBITED_OUTPUT")

    for label, row in validations.items():
        if not isinstance(label, str) or not label or not isinstance(row, dict) or set(row) != {"status", "evidence_sha256"}:
            raise AgentPolicyError("review validation summary invalid")
        if row["status"] not in {"PASS", "FAIL"} or not isinstance(row["evidence_sha256"], str) or not SHA256_RE.fullmatch(row["evidence_sha256"]):
            raise AgentPolicyError("review validation summary invalid")

    missing_outputs = [path for path in spec["required_outputs"] if path not in outputs]
    missing_validations = [label for label in spec["required_validation_labels"] if label not in validations]
    failed_validations = [
        label for label in spec["required_validation_labels"]
        if label in validations and validations[label]["status"] != "PASS"
    ]
    if summary["missing_required_outputs"] != missing_outputs:
        raise AgentPolicyError("review missing-output summary mismatch")
    if summary["missing_required_validations"] != missing_validations:
        raise AgentPolicyError("review missing-validation summary mismatch")
    if summary["failed_required_validations"] != failed_validations:
        raise AgentPolicyError("review failed-validation summary mismatch")

    derived_review_flags = []
    if missing_outputs:
        derived_review_flags.append("MISSING_REQUIRED_OUTPUT")
    if missing_validations:
        derived_review_flags.append("MISSING_REQUIRED_VALIDATION")
    if failed_validations:
        derived_flags.append("FAILED_REQUIRED_VALIDATION")

    flags = dossier.get("flags")
    review_flags = dossier.get("review_flags")
    if not isinstance(flags, list) or not isinstance(review_flags, list):
        raise AgentPolicyError("review dossier flags missing")
    if len(flags) != len(set(flags)) or len(review_flags) != len(set(review_flags)):
        raise AgentPolicyError("review dossier flags must be unique")
    opaque = set(flags) - set(derived_flags)
    if not opaque.issubset(OPAQUE_EVALUATOR_FLAGS):
        raise AgentPolicyError("review dossier contains unknown flags")
    if set(derived_flags) - set(flags):
        raise AgentPolicyError("review dossier omits derived failure flags")
    if sorted(review_flags) != sorted(derived_review_flags):
        raise AgentPolicyError("review dossier review flags mismatch")

    expected_status = "FAIL_CLOSED" if flags else ("REVIEW_REQUIRED" if review_flags else "PASS")
    if dossier.get("machine_status") != expected_status:
        raise AgentPolicyError("review dossier machine status mismatch")
    return expected_status


def assess_review_handoff(task_spec, dossier):
    """A machine PASS only makes evidence structurally ready for human review."""
    spec = validate_task_spec(task_spec)
    _verify_hash(dossier, "review_dossier_content_sha256", "review dossier")
    if dossier.get("review_version") != REVIEW_VERSION:
        raise AgentPolicyError("review dossier version mismatch")
    if dossier.get("task_id") != spec["task_id"] or dossier.get("git_base") != spec["git_base"]:
        raise AgentPolicyError("review dossier task/base mismatch")
    packet = build_work_packet(spec)
    if dossier.get("work_packet_content_sha256") != packet["work_packet_content_sha256"]:
        raise AgentPolicyError("review dossier work-packet mismatch")
    if dossier.get("authority") != REVIEW_AUTHORITY or dossier.get("capabilities") != REVIEW_CAPABILITIES:
        raise AgentPolicyError("review dossier expands authority or capability")
    status = _check_review_summary(spec, dossier)
    if status == "PASS":
        handoff = "HUMAN_REVIEW_REQUIRED"
    elif status == "REVIEW_REQUIRED":
        handoff = "INCOMPLETE"
    else:
        handoff = "BLOCKED"
    return {
        "handoff_status": handoff,
        "task_id": spec["task_id"],
        "human_disposition": None,
        "automatic_merge": False,
        "automatic_promotion": False,
    }
