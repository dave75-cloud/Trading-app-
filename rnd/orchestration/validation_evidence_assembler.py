#!/usr/bin/env python3
"""Deterministic evidence assembly for governed autonomous R&D."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from controlled_rnd_executor import (
    EVIDENCE_VERSION as EXECUTION_EVIDENCE_VERSION,
    EXECUTOR_AUTHORITY,
    EXECUTOR_CAPABILITIES,
)
from rnd_lifecycle_coordinator import (
    EVIDENCE_VERSION as CANDIDATE_EVIDENCE_VERSION,
    SAFETY as CANDIDATE_SAFETY,
)
from task_spec_contract import (
    SHA40_RE,
    SHA256_RE,
    TaskSpecError,
    canonical_hash,
    normalize_repo_path,
)


VERSION = "RND-validation-evidence-assembler-v0.1"
EXTERNAL_VALIDATION_VERSION = "RND-external-validation-v0.1"
PATH_MANIFEST_VERSION = "RND-candidate-path-manifest-v0.1"
OUTPUT_MANIFEST_VERSION = "RND-candidate-output-manifest-v0.1"
PROVENANCE_VERSION = "RND-evidence-assembly-provenance-v0.1"

ASSEMBLER_AUTHORITY = {
    "human_disposition": None,
    "human_notes": None,
    "human_gate_required": True,
    "automatic_merge": False,
    "automatic_promotion": False,
    "merge_authority": "NONE",
    "promotion_authority": "NONE",
}

ASSEMBLER_CAPABILITIES = {
    "network": False,
    "subprocess": False,
    "github_api": False,
    "broker_transport": False,
    "submission": False,
    "candidate_code_execution": False,
    "git_mutation": False,
}


class AssemblerError(ValueError):
    pass


def _verify_hashed_object(value, hash_field, role):
    if not isinstance(value, dict):
        raise AssemblerError(f"{role}: expected JSON object")
    recorded = value.get(hash_field)
    if not isinstance(recorded, str) or not SHA256_RE.fullmatch(recorded):
        raise AssemblerError(f"{role}: invalid {hash_field}")
    body = dict(value)
    body.pop(hash_field, None)
    if canonical_hash(body) != recorded:
        raise AssemblerError(f"{role}: content hash mismatch")


def _require_sha40(value, role):
    value = str(value or "").strip().lower()
    if not SHA40_RE.fullmatch(value):
        raise AssemblerError(f"{role}: invalid repository HEAD SHA")
    return value


def _require_sha256(value, role):
    value = str(value or "").strip().lower()
    if not SHA256_RE.fullmatch(value):
        raise AssemblerError(f"{role}: invalid SHA-256")
    return value


def _validate_work_packet(packet):
    _verify_hashed_object(
        packet,
        "work_packet_content_sha256",
        "work packet",
    )
    task_id = str(packet.get("task_id", "")).strip()
    git_base = str(packet.get("git_base", "")).strip().lower()
    labels = packet.get("required_validation_labels")
    if not task_id:
        raise AssemblerError("work packet: task_id is required")
    if not SHA40_RE.fullmatch(git_base):
        raise AssemblerError("work packet: git_base is invalid")
    if not isinstance(labels, list) or not labels:
        raise AssemblerError(
            "work packet: required_validation_labels must be non-empty list[str]"
        )
    if not all(isinstance(x, str) and x.strip() for x in labels):
        raise AssemblerError(
            "work packet: required_validation_labels must be non-empty list[str]"
        )
    labels = [x.strip() for x in labels]
    if len(labels) != len(set(labels)):
        raise AssemblerError("work packet: duplicate validation labels")
    return {
        "task_id": task_id,
        "git_base": git_base,
        "required_validation_labels": labels,
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
    }


def _validate_execution_evidence(raw, packet):
    _verify_hashed_object(
        raw,
        "execution_evidence_content_sha256",
        "RND-0021 execution evidence",
    )
    if raw.get("execution_evidence_version") != EXECUTION_EVIDENCE_VERSION:
        raise AssemblerError("RND-0021 execution evidence: unsupported version")
    if raw.get("task_id") != packet["task_id"]:
        raise AssemblerError("RND-0021 execution evidence: task_id mismatch")
    if raw.get("git_base") != packet["git_base"]:
        raise AssemblerError("RND-0021 execution evidence: git_base mismatch")
    if (
        raw.get("work_packet_content_sha256")
        != packet["work_packet_content_sha256"]
    ):
        raise AssemblerError(
            "RND-0021 execution evidence: work-packet hash mismatch"
        )

    head = _require_sha40(
        raw.get("repository_head_sha"),
        "RND-0021 execution evidence",
    )
    actions = raw.get("actions")
    validations = raw.get("validations")
    if not isinstance(actions, list) or not isinstance(validations, list):
        raise AssemblerError(
            "RND-0021 execution evidence: actions/validations must be lists"
        )

    action_rows = {}
    for row in actions:
        if not isinstance(row, dict):
            raise AssemblerError(
                "RND-0021 execution evidence: action row must be object"
            )
        _verify_hashed_object(
            row,
            "action_evidence_sha256",
            "RND-0021 action evidence",
        )
        label = str(row.get("validation_label", "")).strip()
        status = str(row.get("status", "")).strip().upper()
        if not label or status not in {"PASS", "FAIL"}:
            raise AssemblerError(
                "RND-0021 action evidence: invalid label/status"
            )
        if label in action_rows:
            raise AssemblerError(
                "RND-0021 execution evidence: duplicate action label"
            )
        action_rows[label] = {
            "status": status,
            "evidence_sha256": row["action_evidence_sha256"],
        }

    validation_rows = {}
    for row in validations:
        if not isinstance(row, dict):
            raise AssemblerError(
                "RND-0021 execution evidence: validation row must be object"
            )
        label = str(row.get("label", "")).strip()
        status = str(row.get("status", "")).strip().upper()
        digest = _require_sha256(
            row.get("evidence_sha256"),
            "RND-0021 validation evidence",
        )
        if not label or status not in {"PASS", "FAIL"}:
            raise AssemblerError(
                "RND-0021 execution evidence: invalid validation row"
            )
        if label in validation_rows:
            raise AssemblerError(
                "RND-0021 execution evidence: duplicate validation label"
            )
        validation_rows[label] = {
            "status": status,
            "evidence_sha256": digest,
        }

    if action_rows != validation_rows:
        raise AssemblerError(
            "RND-0021 execution evidence: action/validation evidence mismatch"
        )

    if raw.get("authority") != EXECUTOR_AUTHORITY:
        raise AssemblerError(
            "RND-0021 execution evidence: authority boundary invalid"
        )
    if raw.get("capabilities") != EXECUTOR_CAPABILITIES:
        raise AssemblerError(
            "RND-0021 execution evidence: capability boundary invalid"
        )
    _require_sha256(
        raw.get("execution_plan_content_sha256"),
        "RND-0021 execution plan",
    )

    expected_overall = (
        "PASS"
        if all(row["status"] == "PASS" for row in validation_rows.values())
        else "FAIL"
    )
    if raw.get("overall_status") != expected_overall:
        raise AssemblerError(
            "RND-0021 execution evidence: overall_status mismatch"
        )

    scope_changed_paths = None
    for row in actions:
        if row.get("validation_label") == "scope-check":
            observations = row.get("observations")
            if not isinstance(observations, dict):
                raise AssemblerError(
                    "RND-0021 scope-check: observations missing"
                )
            changed = observations.get("changed_paths")
            if not isinstance(changed, list) or not all(
                isinstance(x, str) for x in changed
            ):
                raise AssemblerError(
                    "RND-0021 scope-check: changed_paths invalid"
                )
            try:
                scope_changed_paths = sorted(
                    normalize_repo_path(x, "RND-0021 scope changed path")
                    for x in changed
                )
            except TaskSpecError as exc:
                raise AssemblerError(str(exc)) from exc
            if len(scope_changed_paths) != len(set(scope_changed_paths)):
                raise AssemblerError(
                    "RND-0021 scope-check: duplicate changed path"
                )

    return {
        "repository_head_sha": head,
        "validations": validation_rows,
        "scope_changed_paths": scope_changed_paths,
        "source_sha256": raw["execution_evidence_content_sha256"],
    }


def _validate_external_record(raw, packet):
    _verify_hashed_object(
        raw,
        "external_validation_content_sha256",
        "external validation",
    )
    if raw.get("external_validation_version") != EXTERNAL_VALIDATION_VERSION:
        raise AssemblerError("external validation: unsupported version")
    if raw.get("task_id") != packet["task_id"]:
        raise AssemblerError("external validation: task_id mismatch")
    if raw.get("git_base") != packet["git_base"]:
        raise AssemblerError("external validation: git_base mismatch")
    if (
        raw.get("work_packet_content_sha256")
        != packet["work_packet_content_sha256"]
    ):
        raise AssemblerError("external validation: work-packet hash mismatch")

    label = str(raw.get("label", "")).strip()
    status = str(raw.get("status", "")).strip().upper()
    producer = str(raw.get("producer_id", "")).strip()
    head = _require_sha40(raw.get("repository_head_sha"), "external validation")
    digest = _require_sha256(
        raw.get("evidence_sha256"),
        "external validation evidence",
    )
    if not label:
        raise AssemblerError("external validation: label is required")
    if status not in {"PASS", "FAIL"}:
        raise AssemblerError("external validation: invalid status")
    if not producer:
        raise AssemblerError("external validation: producer_id is required")

    return {
        "label": label,
        "status": status,
        "evidence_sha256": digest,
        "producer_id": producer,
        "repository_head_sha": head,
        "source_sha256": raw["external_validation_content_sha256"],
    }


def _validate_path_manifest(raw, packet):
    _verify_hashed_object(
        raw,
        "path_manifest_content_sha256",
        "candidate path manifest",
    )
    if raw.get("path_manifest_version") != PATH_MANIFEST_VERSION:
        raise AssemblerError("candidate path manifest: unsupported version")
    if raw.get("task_id") != packet["task_id"]:
        raise AssemblerError("candidate path manifest: task_id mismatch")
    if raw.get("git_base") != packet["git_base"]:
        raise AssemblerError("candidate path manifest: git_base mismatch")
    if (
        raw.get("work_packet_content_sha256")
        != packet["work_packet_content_sha256"]
    ):
        raise AssemblerError(
            "candidate path manifest: work-packet hash mismatch"
        )
    head = _require_sha40(raw.get("repository_head_sha"), "candidate path manifest")
    paths = raw.get("changed_paths")
    if not isinstance(paths, list):
        raise AssemblerError("candidate path manifest: changed_paths must be list")
    normalized = []
    try:
        for path in paths:
            normalized.append(
                normalize_repo_path(path, "candidate changed path")
            )
    except TaskSpecError as exc:
        raise AssemblerError(str(exc)) from exc
    if len(normalized) != len(set(normalized)):
        raise AssemblerError("candidate path manifest: duplicate changed path")
    return {
        "repository_head_sha": head,
        "changed_paths": sorted(normalized),
        "source_sha256": raw["path_manifest_content_sha256"],
    }


def _validate_output_manifest(raw, packet):
    _verify_hashed_object(
        raw,
        "output_manifest_content_sha256",
        "candidate output manifest",
    )
    if raw.get("output_manifest_version") != OUTPUT_MANIFEST_VERSION:
        raise AssemblerError("candidate output manifest: unsupported version")
    if raw.get("task_id") != packet["task_id"]:
        raise AssemblerError("candidate output manifest: task_id mismatch")
    if raw.get("git_base") != packet["git_base"]:
        raise AssemblerError("candidate output manifest: git_base mismatch")
    if (
        raw.get("work_packet_content_sha256")
        != packet["work_packet_content_sha256"]
    ):
        raise AssemblerError(
            "candidate output manifest: work-packet hash mismatch"
        )
    head = _require_sha40(raw.get("repository_head_sha"), "candidate output manifest")
    rows = raw.get("outputs")
    if not isinstance(rows, list):
        raise AssemblerError("candidate output manifest: outputs must be list")

    outputs = {}
    for row in rows:
        if not isinstance(row, dict):
            raise AssemblerError("candidate output manifest: output row must be object")
        try:
            path = normalize_repo_path(
                row.get("path"),
                "candidate output path",
            )
        except TaskSpecError as exc:
            raise AssemblerError(str(exc)) from exc
        digest = _require_sha256(
            row.get("sha256"),
            "candidate output manifest",
        )
        if path in outputs:
            raise AssemblerError("candidate output manifest: duplicate output path")
        outputs[path] = digest

    return {
        "repository_head_sha": head,
        "outputs": outputs,
        "source_sha256": raw["output_manifest_content_sha256"],
    }


def assemble_evidence(
    work_packet,
    execution_evidence,
    external_validations,
    path_manifest,
    output_manifest,
):
    packet = _validate_work_packet(work_packet)
    execution = _validate_execution_evidence(execution_evidence, packet)
    paths = _validate_path_manifest(path_manifest, packet)
    outputs = _validate_output_manifest(output_manifest, packet)

    if not isinstance(external_validations, list):
        raise AssemblerError("external validations must be a list")
    external = [
        _validate_external_record(row, packet)
        for row in external_validations
    ]

    heads = {
        execution["repository_head_sha"],
        paths["repository_head_sha"],
        outputs["repository_head_sha"],
    }
    heads.update(row["repository_head_sha"] for row in external)
    if len(heads) != 1:
        raise AssemblerError("candidate repository HEAD mismatch across evidence")
    candidate_head = next(iter(heads))

    if (
        execution["scope_changed_paths"] is not None
        and execution["scope_changed_paths"] != paths["changed_paths"]
    ):
        raise AssemblerError(
            "candidate path manifest does not match RND-0021 scope-check evidence"
        )

    required_labels = set(packet["required_validation_labels"])
    validations = {}
    validation_sources = {}

    for label, row in execution["validations"].items():
        if label not in required_labels:
            raise AssemblerError(
                f"unknown validation label from RND-0021 evidence: {label}"
            )
        validations[label] = dict(row)
        validation_sources[label] = {
            "source_type": "RND-0021_EXECUTOR",
            "source_sha256": execution["source_sha256"],
        }

    for row in external:
        label = row["label"]
        if label not in required_labels:
            raise AssemblerError(f"unknown external validation label: {label}")
        if label in validations:
            raise AssemblerError(f"duplicate validation label: {label}")
        validations[label] = {
            "status": row["status"],
            "evidence_sha256": row["evidence_sha256"],
        }
        validation_sources[label] = {
            "source_type": "EXTERNAL_ATTESTATION",
            "source_sha256": row["source_sha256"],
            "producer_id": row["producer_id"],
        }

    missing = sorted(required_labels - set(validations))
    assembly_status = "PASS" if not missing else "REVIEW_REQUIRED"

    candidate = {
        "evidence_version": CANDIDATE_EVIDENCE_VERSION,
        "task_id": packet["task_id"],
        "git_base": packet["git_base"],
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
        "changed_paths": paths["changed_paths"],
        "outputs": [
            {"path": path, "sha256": outputs["outputs"][path]}
            for path in sorted(outputs["outputs"])
        ],
        "validations": [
            {
                "label": label,
                "status": validations[label]["status"],
                "evidence_sha256": validations[label]["evidence_sha256"],
            }
            for label in sorted(validations)
        ],
        "safety": dict(CANDIDATE_SAFETY),
    }

    provenance = {
        "provenance_version": PROVENANCE_VERSION,
        "assembler_version": VERSION,
        "assembly_status": assembly_status,
        "task_id": packet["task_id"],
        "git_base": packet["git_base"],
        "repository_head_sha": candidate_head,
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
        "candidate_evidence_sha256": canonical_hash(candidate),
        "source_artifacts": {
            "rnd0021_execution_evidence_sha256": execution["source_sha256"],
            "path_manifest_sha256": paths["source_sha256"],
            "output_manifest_sha256": outputs["source_sha256"],
            "external_validation_sha256": sorted(
                row["source_sha256"] for row in external
            ),
        },
        "validation_sources": {
            label: validation_sources[label]
            for label in sorted(validation_sources)
        },
        "required_validation_labels": sorted(required_labels),
        "present_validation_labels": sorted(validations),
        "missing_validation_labels": missing,
        "changed_paths": paths["changed_paths"],
        "output_sha256": {
            path: outputs["outputs"][path]
            for path in sorted(outputs["outputs"])
        },
        "trust_boundary": {
            "rnd0021_evidence": "MACHINE_GENERATED_BOUNDED_EXECUTOR",
            "external_validation": "ATTESTED_INPUT_NOT_REEXECUTED",
            "assembler_verifies_execution_truth": False,
        },
        "authority": dict(ASSEMBLER_AUTHORITY),
        "capabilities": dict(ASSEMBLER_CAPABILITIES),
    }
    provenance["provenance_content_sha256"] = canonical_hash(provenance)
    return candidate, provenance


def assembly_exit_code(provenance):
    status = provenance.get("assembly_status")
    if status == "PASS":
        return 0
    if status == "REVIEW_REQUIRED":
        return 2
    raise AssemblerError("unknown assembly status")


def _load_json(path, role):
    try:
        value = json.loads(Path(path).read_text())
    except Exception as exc:
        raise AssemblerError(f"{role}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise AssemblerError(f"{role}: expected JSON object")
    return value


def _load_external(paths):
    return [_load_json(path, "external validation") for path in paths]


def _write_pair(candidate_path, provenance_path, candidate, provenance):
    candidate_path = Path(candidate_path)
    provenance_path = Path(provenance_path)
    if candidate_path == provenance_path:
        raise AssemblerError("candidate/provenance outputs must differ")
    for path in (candidate_path, provenance_path):
        if path.exists():
            raise AssemblerError("output already exists; refusing overwrite")
        if not path.parent.is_dir():
            raise AssemblerError("output parent directory does not exist")
    candidate_path.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-packet", required=True)
    parser.add_argument("--execution-evidence", required=True)
    parser.add_argument("--external-validation", action="append", default=[])
    parser.add_argument("--path-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--candidate-output", required=True)
    parser.add_argument("--provenance-output", required=True)
    args = parser.parse_args()

    candidate, provenance = assemble_evidence(
        _load_json(args.work_packet, "work packet"),
        _load_json(args.execution_evidence, "RND-0021 execution evidence"),
        _load_external(args.external_validation),
        _load_json(args.path_manifest, "candidate path manifest"),
        _load_json(args.output_manifest, "candidate output manifest"),
    )
    _write_pair(
        args.candidate_output,
        args.provenance_output,
        candidate,
        provenance,
    )
    print("RND_EVIDENCE_ASSEMBLER: " + provenance["assembly_status"])
    print(f"validations={len(candidate['validations'])}")
    print(f"missing={len(provenance['missing_validation_labels'])}")
    print("subprocess_capability=FALSE")
    print("network_capability=FALSE")
    print("automatic_merge=FALSE")
    print("automatic_promotion=FALSE")
    return assembly_exit_code(provenance)


if __name__ == "__main__":
    raise SystemExit(main())
