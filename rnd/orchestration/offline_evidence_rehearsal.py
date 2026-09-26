#!/usr/bin/env python3
"""Offline handoff across the existing RND-0020/21/22 evidence contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rnd_lifecycle_coordinator import (
    build_work_packet,
    evaluate_candidate,
    evaluation_exit_code,
)
from validation_evidence_assembler import assemble_evidence


class RehearsalError(ValueError):
    pass


def rehearse_evidence(
    task_spec,
    execution_evidence,
    external_validations,
    path_manifest,
    output_manifest,
):
    """Consume supplied artifacts; do not run or attest any validation."""
    work_packet = build_work_packet(task_spec)
    candidate, provenance = assemble_evidence(
        work_packet,
        execution_evidence,
        external_validations,
        path_manifest,
        output_manifest,
    )
    dossier = evaluate_candidate(task_spec, work_packet, candidate)
    return work_packet, candidate, provenance, dossier


def _load_json(path, role):
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise RehearsalError(f"{role}: cannot read JSON") from exc
    if not isinstance(value, dict):
        raise RehearsalError(f"{role}: expected JSON object")
    return value


def _write_outputs(paths, values):
    if len(paths) != len(values):
        raise RehearsalError("output count mismatch")
    targets = [Path(path) for path in paths]
    if len({path.resolve() for path in targets}) != len(targets):
        raise RehearsalError("output paths must be distinct")
    for path in targets:
        if path.exists():
            raise RehearsalError("output already exists; refusing overwrite")
        if not path.parent.is_dir():
            raise RehearsalError("output parent directory does not exist")
    created = []
    try:
        for path, value in zip(targets, values):
            with path.open("x") as stream:
                created.append(path)
                stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
    except OSError as exc:
        for path in created:
            path.unlink()
        raise RehearsalError("could not write rehearsal outputs") from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-spec", required=True)
    parser.add_argument("--execution-evidence", required=True)
    parser.add_argument("--external-validation", action="append", default=[])
    parser.add_argument("--path-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--work-packet-output", required=True)
    parser.add_argument("--candidate-output", required=True)
    parser.add_argument("--provenance-output", required=True)
    parser.add_argument("--dossier-output", required=True)
    args = parser.parse_args()

    artifacts = rehearse_evidence(
        _load_json(args.task_spec, "task spec"),
        _load_json(args.execution_evidence, "RND-0021 execution evidence"),
        [_load_json(path, "external validation") for path in args.external_validation],
        _load_json(args.path_manifest, "changed-path manifest"),
        _load_json(args.output_manifest, "output-hash manifest"),
    )
    _write_outputs(
        [
            args.work_packet_output,
            args.candidate_output,
            args.provenance_output,
            args.dossier_output,
        ],
        artifacts,
    )
    status = artifacts[3]["machine_status"]
    print("RND_OFFLINE_EVIDENCE_REHEARSAL: " + status)
    print("human_disposition=UNSET")
    print("candidate_code_execution=FALSE")
    print("automatic_merge=FALSE")
    print("automatic_promotion=FALSE")
    return evaluation_exit_code(status)


if __name__ == "__main__":
    raise SystemExit(main())
