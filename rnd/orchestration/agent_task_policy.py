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
    status = dossier.get("machine_status")
    flags, review_flags = dossier.get("flags"), dossier.get("review_flags")
    if not isinstance(flags, list) or not isinstance(review_flags, list):
        raise AgentPolicyError("review dossier flags missing")
    if status == "PASS" and not flags and not review_flags:
        handoff = "HUMAN_REVIEW_REQUIRED"
    elif status == "REVIEW_REQUIRED" and not flags and review_flags:
        handoff = "INCOMPLETE"
    elif status == "FAIL_CLOSED" and flags:
        handoff = "BLOCKED"
    else:
        raise AgentPolicyError("review dossier status/flags mismatch")
    return {
        "handoff_status": handoff,
        "task_id": spec["task_id"],
        "human_disposition": None,
        "automatic_merge": False,
        "automatic_promotion": False,
    }
