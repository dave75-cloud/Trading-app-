#!/usr/bin/env python3
"""Offline planner/evaluator coordinator for governed autonomous R&D."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from task_spec_contract import (
    KNOWN_PROTECTED_PREFIXES,
    SHA256_RE,
    TaskSpecError,
    canonical_hash,
    normalize_repo_path,
    path_within,
    validate_task_spec,
)


WORK_PACKET_VERSION = "RND-work-packet-v0.1"
EVIDENCE_VERSION = "RND-candidate-evidence-v0.1"
REVIEW_VERSION = "RND-review-dossier-v0.1"

SAFETY = {
    "network_capability": False,
    "subprocess_capability": False,
    "broker_transport": False,
    "submission_capability": False,
    "automatic_disposition": False,
    "automatic_merge": False,
    "automatic_promotion": False,
    "merge_authority": "NONE",
    "promotion_authority": "NONE",
    "human_review_required": True,
}


class LifecycleError(ValueError):
    pass


def _hash_payload(payload, hash_field):
    out = dict(payload)
    out[hash_field] = canonical_hash(payload)
    return out


def _verify_hash(payload, hash_field, role):
    if not isinstance(payload, dict):
        raise LifecycleError(f"{role}: expected JSON object")
    recorded = payload.get(hash_field)
    if not isinstance(recorded, str) or not SHA256_RE.fullmatch(recorded):
        raise LifecycleError(f"{role}: invalid {hash_field}")
    body = dict(payload)
    body.pop(hash_field, None)
    if canonical_hash(body) != recorded:
        raise LifecycleError(f"{role}: content hash mismatch")


def build_work_packet(task_spec):
    spec = validate_task_spec(task_spec)
    payload = {
        "work_packet_version": WORK_PACKET_VERSION,
        "task_id": spec["task_id"],
        "git_base": spec["git_base"],
        "objective": spec["objective"],
        "scope": {
            "allowed_path_prefixes": spec["allowed_path_prefixes"],
            "prohibited_path_prefixes": spec["prohibited_path_prefixes"],
            "known_protected_prefixes": list(KNOWN_PROTECTED_PREFIXES),
        },
        "required_outputs": spec["required_outputs"],
        "required_validation_labels": spec["required_validation_labels"],
        "success_criteria": spec["success_criteria"],
        "stop_conditions": spec["stop_conditions"],
        "task_spec_sha256": canonical_hash(spec),
        "authority": {
            "human_gate_required": True,
            "automatic_merge": False,
            "automatic_promotion": False,
            "merge_authority": "NONE",
            "promotion_authority": "NONE",
        },
        "capabilities": {
            "network": False,
            "subprocess": False,
            "github_api": False,
            "broker_transport": False,
            "submission": False,
        },
    }
    return _hash_payload(payload, "work_packet_content_sha256")


def _validate_evidence(evidence):
    if not isinstance(evidence, dict):
        raise LifecycleError("candidate evidence must be a JSON object")
    if evidence.get("evidence_version") != EVIDENCE_VERSION:
        raise LifecycleError("candidate evidence: unsupported evidence_version")

    changed = evidence.get("changed_paths")
    if not isinstance(changed, list) or not all(
        isinstance(x, str) and x.strip() for x in changed
    ):
        raise LifecycleError("candidate evidence: changed_paths must be list[str]")
    try:
        changed = [
            normalize_repo_path(x, "candidate changed path")
            for x in changed
        ]
    except TaskSpecError as exc:
        raise LifecycleError(f"candidate evidence: {exc}") from exc
    if len(changed) != len(set(changed)):
        raise LifecycleError("candidate evidence: duplicate changed_paths")

    outputs = evidence.get("outputs")
    if not isinstance(outputs, list):
        raise LifecycleError("candidate evidence: outputs must be a list")
    output_map = {}
    for row in outputs:
        if not isinstance(row, dict):
            raise LifecycleError("candidate evidence: output row must be object")
        try:
            path = normalize_repo_path(
                row.get("path"),
                "candidate output path",
            )
        except TaskSpecError as exc:
            raise LifecycleError(f"candidate evidence: {exc}") from exc
        digest = str(row.get("sha256", "")).strip().lower()
        if not SHA256_RE.fullmatch(digest):
            raise LifecycleError("candidate evidence: invalid output record")
        if path in output_map:
            raise LifecycleError("candidate evidence: duplicate output path")
        output_map[path] = digest

    validations = evidence.get("validations")
    if not isinstance(validations, list):
        raise LifecycleError("candidate evidence: validations must be a list")
    validation_map = {}
    for row in validations:
        if not isinstance(row, dict):
            raise LifecycleError("candidate evidence: validation row must be object")
        label = str(row.get("label", "")).strip()
        status = str(row.get("status", "")).strip().upper()
        digest = str(row.get("evidence_sha256", "")).strip().lower()
        if not label or status not in {"PASS", "FAIL"} or not SHA256_RE.fullmatch(digest):
            raise LifecycleError("candidate evidence: invalid validation record")
        if label in validation_map:
            raise LifecycleError("candidate evidence: duplicate validation label")
        validation_map[label] = {"status": status, "evidence_sha256": digest}

    safety = evidence.get("safety")
    if not isinstance(safety, dict):
        raise LifecycleError("candidate evidence: safety block missing")

    return {
        "task_id": str(evidence.get("task_id", "")).strip(),
        "git_base": str(evidence.get("git_base", "")).strip().lower(),
        "work_packet_content_sha256": str(
            evidence.get("work_packet_content_sha256", "")
        ).strip().lower(),
        "changed_paths": changed,
        "outputs": output_map,
        "validations": validation_map,
        "safety": safety,
    }


def evaluate_candidate(task_spec, work_packet, candidate_evidence):
    spec = validate_task_spec(task_spec)
    expected_packet = build_work_packet(spec)

    _verify_hash(
        work_packet,
        "work_packet_content_sha256",
        "work packet",
    )
    if work_packet != expected_packet:
        raise LifecycleError("work packet does not match task specification")

    evidence = _validate_evidence(candidate_evidence)
    flags = []
    review_flags = []

    if evidence["task_id"] != spec["task_id"]:
        flags.append("TASK_ID_MISMATCH")
    if evidence["git_base"] != spec["git_base"]:
        flags.append("GIT_BASE_MISMATCH")
    if evidence["work_packet_content_sha256"] != work_packet[
        "work_packet_content_sha256"
    ]:
        flags.append("WORK_PACKET_HASH_MISMATCH")

    allowed = spec["allowed_path_prefixes"]
    prohibited = spec["prohibited_path_prefixes"]

    for path in evidence["changed_paths"]:
        if any(path_within(path, prefix) for prefix in KNOWN_PROTECTED_PREFIXES):
            flags.append("PROTECTED_PATH_CHANGED")
        if not any(path_within(path, prefix) for prefix in allowed):
            flags.append("CHANGED_PATH_OUTSIDE_ALLOWED_SCOPE")
        if any(path_within(path, prefix) for prefix in prohibited):
            flags.append("PROHIBITED_PATH_CHANGED")

    for path in evidence["outputs"]:
        if not any(path_within(path, prefix) for prefix in allowed):
            flags.append("OUTPUT_OUTSIDE_ALLOWED_SCOPE")
        if any(path_within(path, prefix) for prefix in prohibited):
            flags.append("PROHIBITED_OUTPUT")

    missing_outputs = [
        path for path in spec["required_outputs"]
        if path not in evidence["outputs"]
    ]
    if missing_outputs:
        review_flags.append("MISSING_REQUIRED_OUTPUT")

    missing_validations = [
        label for label in spec["required_validation_labels"]
        if label not in evidence["validations"]
    ]
    if missing_validations:
        review_flags.append("MISSING_REQUIRED_VALIDATION")

    failed_validations = [
        label for label, row in evidence["validations"].items()
        if label in spec["required_validation_labels"]
        and row["status"] != "PASS"
    ]
    if failed_validations:
        flags.append("FAILED_REQUIRED_VALIDATION")

    if evidence["safety"] != SAFETY:
        flags.append("SAFETY_DECLARATION_INVALID")

    flags = sorted(set(flags))
    review_flags = sorted(set(review_flags))

    if flags:
        machine_status = "FAIL_CLOSED"
    elif review_flags:
        machine_status = "REVIEW_REQUIRED"
    else:
        machine_status = "PASS"

    payload = {
        "review_version": REVIEW_VERSION,
        "task_id": spec["task_id"],
        "git_base": spec["git_base"],
        "work_packet_content_sha256": work_packet[
            "work_packet_content_sha256"
        ],
        "machine_status": machine_status,
        "flags": flags,
        "review_flags": review_flags,
        "candidate_evidence_sha256": canonical_hash(evidence),
        "evidence_summary": {
            "changed_paths": sorted(evidence["changed_paths"]),
            "output_sha256": {
                path: evidence["outputs"][path]
                for path in sorted(evidence["outputs"])
            },
            "validations": {
                label: evidence["validations"][label]
                for label in sorted(evidence["validations"])
            },
            "missing_required_outputs": missing_outputs,
            "missing_required_validations": missing_validations,
            "failed_required_validations": failed_validations,
        },
        "authority": {
            "human_disposition": None,
            "human_notes": None,
            "human_gate_required": True,
            "automatic_merge": False,
            "automatic_promotion": False,
            "merge_authority": "NONE",
            "promotion_authority": "NONE",
        },
        "capabilities": {
            "network": False,
            "subprocess": False,
            "github_api": False,
            "broker_transport": False,
            "submission": False,
        },
    }
    return _hash_payload(payload, "review_dossier_content_sha256")


def evaluation_exit_code(machine_status):
    if machine_status == "PASS":
        return 0
    if machine_status == "REVIEW_REQUIRED":
        return 2
    if machine_status == "FAIL_CLOSED":
        return 1
    raise LifecycleError("unknown machine status")


def _load_json(path, role):
    try:
        value = json.loads(Path(path).read_text())
    except Exception as exc:
        raise LifecycleError(f"{role}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"{role}: expected JSON object")
    return value


def _write_new_json(path, value):
    path = Path(path)
    if path.exists():
        raise LifecycleError("output already exists; refusing overwrite")
    if not path.parent.is_dir():
        raise LifecycleError("output parent directory does not exist")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--task-spec", required=True)
    plan.add_argument("--output", required=True)

    review = sub.add_parser("evaluate")
    review.add_argument("--task-spec", required=True)
    review.add_argument("--work-packet", required=True)
    review.add_argument("--candidate-evidence", required=True)
    review.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.mode == "plan":
        packet = build_work_packet(_load_json(args.task_spec, "task spec"))
        _write_new_json(args.output, packet)
        print("RND_LIFECYCLE_COORDINATOR_PLAN: PASS")
        print(f"task_id={packet['task_id']}")
        print("subprocess_capability=FALSE")
        print("network_capability=FALSE")
        print("automatic_merge=FALSE")
        return 0

    dossier = evaluate_candidate(
        _load_json(args.task_spec, "task spec"),
        _load_json(args.work_packet, "work packet"),
        _load_json(args.candidate_evidence, "candidate evidence"),
    )
    _write_new_json(args.output, dossier)
    print(
        "RND_LIFECYCLE_COORDINATOR_EVALUATE: "
        + dossier["machine_status"]
    )
    print(f"machine_status={dossier['machine_status']}")
    print("human_disposition=UNSET")
    print("automatic_merge=FALSE")
    print("automatic_promotion=FALSE")
    return evaluation_exit_code(dossier["machine_status"])


if __name__ == "__main__":
    raise SystemExit(main())
