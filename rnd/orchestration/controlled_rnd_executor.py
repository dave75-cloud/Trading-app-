#!/usr/bin/env python3
"""Controlled local execution of a tiny read-only R&D validation allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from task_spec_contract import SHA40_RE, SHA256_RE, canonical_hash
from rnd_lifecycle_coordinator import WORK_PACKET_VERSION


VERSION = "RND-controlled-executor-v0.1"
PLAN_VERSION = "RND-execution-plan-v0.1"
EVIDENCE_VERSION = "RND-execution-evidence-v0.1"

ROOT = Path(__file__).resolve().parents[2]
GIT = "/usr/bin/git"
MAX_PREVIEW_BYTES = 4096
PROCESS_TIMEOUT_SECONDS = 60

ACTION_IDS = (
    "diff-check",
    "scope-check",
)

WORK_PACKET_AUTHORITY = {
    "human_gate_required": True,
    "automatic_merge": False,
    "automatic_promotion": False,
    "merge_authority": "NONE",
    "promotion_authority": "NONE",
}

WORK_PACKET_CAPABILITIES = {
    "network": False,
    "subprocess": False,
    "github_api": False,
    "broker_transport": False,
    "submission": False,
}

EXECUTOR_AUTHORITY = {
    "human_disposition": None,
    "human_notes": None,
    "human_gate_required": True,
    "automatic_merge": False,
    "automatic_promotion": False,
    "merge_authority": "NONE",
    "promotion_authority": "NONE",
}

EXECUTOR_CAPABILITIES = {
    "network": False,
    "github_api": False,
    "broker_transport": False,
    "submission": False,
    "candidate_code_execution": False,
    "subprocess_mode": "READ_ONLY_GIT_ALLOWLIST_ONLY",
    "arbitrary_subprocess": False,
    "shell": False,
}

SAFE_ENV = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "GIT_PAGER": "cat",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


class ExecutorError(ValueError):
    pass


def _verify_hashed_object(value, hash_field, role):
    if not isinstance(value, dict):
        raise ExecutorError(f"{role}: expected JSON object")
    recorded = value.get(hash_field)
    if not isinstance(recorded, str) or not SHA256_RE.fullmatch(recorded):
        raise ExecutorError(f"{role}: invalid {hash_field}")
    body = dict(value)
    body.pop(hash_field, None)
    if canonical_hash(body) != recorded:
        raise ExecutorError(f"{role}: content hash mismatch")


def validate_work_packet(packet):
    _verify_hashed_object(
        packet,
        "work_packet_content_sha256",
        "work packet",
    )
    if packet.get("work_packet_version") != WORK_PACKET_VERSION:
        raise ExecutorError("work packet: unsupported version")

    task_id = str(packet.get("task_id", "")).strip()
    git_base = str(packet.get("git_base", "")).strip().lower()
    labels = packet.get("required_validation_labels")

    if not task_id:
        raise ExecutorError("work packet: task_id is required")
    if not SHA40_RE.fullmatch(git_base):
        raise ExecutorError("work packet: git_base is invalid")
    if not isinstance(labels, list) or not all(
        isinstance(x, str) and x.strip() for x in labels
    ):
        raise ExecutorError(
            "work packet: required_validation_labels must be list[str]"
        )
    labels = [x.strip() for x in labels]
    if len(labels) != len(set(labels)):
        raise ExecutorError("work packet: duplicate validation labels")

    if packet.get("authority") != WORK_PACKET_AUTHORITY:
        raise ExecutorError("work packet: authority boundary invalid")
    if packet.get("capabilities") != WORK_PACKET_CAPABILITIES:
        raise ExecutorError("work packet: capability boundary invalid")

    scope = packet.get("scope")
    if not isinstance(scope, dict):
        raise ExecutorError("work packet: scope is missing")
    allowed = scope.get("allowed_path_prefixes")
    prohibited = scope.get("prohibited_path_prefixes")
    protected = scope.get("known_protected_prefixes")
    for name, value in (
        ("allowed_path_prefixes", allowed),
        ("prohibited_path_prefixes", prohibited),
        ("known_protected_prefixes", protected),
    ):
        if not isinstance(value, list) or not all(
            isinstance(x, str) and x.strip() for x in value
        ):
            raise ExecutorError(f"work packet: {name} must be list[str]")

    return {
        "task_id": task_id,
        "git_base": git_base,
        "required_validation_labels": labels,
        "allowed_path_prefixes": list(allowed),
        "prohibited_path_prefixes": list(prohibited),
        "known_protected_prefixes": list(protected),
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
    }


def _path_within(path, prefix):
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def build_execution_plan(work_packet, action_ids):
    packet = validate_work_packet(work_packet)

    if not isinstance(action_ids, list) or not action_ids:
        raise ExecutorError("execution plan requires at least one action ID")
    if not all(isinstance(x, str) and x.strip() for x in action_ids):
        raise ExecutorError("action IDs must be non-empty strings")

    requested = [x.strip() for x in action_ids]
    if len(requested) != len(set(requested)):
        raise ExecutorError("duplicate action ID")

    unknown = sorted(set(requested) - set(ACTION_IDS))
    if unknown:
        raise ExecutorError("unknown action ID: " + ", ".join(unknown))

    unauthorized = sorted(
        action for action in requested
        if action not in packet["required_validation_labels"]
    )
    if unauthorized:
        raise ExecutorError(
            "action not authorized by work packet: "
            + ", ".join(unauthorized)
        )

    payload = {
        "plan_version": PLAN_VERSION,
        "task_id": packet["task_id"],
        "git_base": packet["git_base"],
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
        "actions": sorted(requested),
        "authority": dict(EXECUTOR_AUTHORITY),
        "capabilities": dict(EXECUTOR_CAPABILITIES),
    }
    payload["execution_plan_content_sha256"] = canonical_hash(payload)
    return payload


def validate_execution_plan(work_packet, plan):
    packet = validate_work_packet(work_packet)
    _verify_hashed_object(
        plan,
        "execution_plan_content_sha256",
        "execution plan",
    )

    if plan.get("plan_version") != PLAN_VERSION:
        raise ExecutorError("execution plan: unsupported version")
    if plan.get("task_id") != packet["task_id"]:
        raise ExecutorError("execution plan: task_id mismatch")
    if plan.get("git_base") != packet["git_base"]:
        raise ExecutorError("execution plan: git_base mismatch")
    if (
        plan.get("work_packet_content_sha256")
        != packet["work_packet_content_sha256"]
    ):
        raise ExecutorError("execution plan: work-packet hash mismatch")
    if plan.get("authority") != EXECUTOR_AUTHORITY:
        raise ExecutorError("execution plan: authority boundary invalid")
    if plan.get("capabilities") != EXECUTOR_CAPABILITIES:
        raise ExecutorError("execution plan: capability boundary invalid")

    actions = plan.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ExecutorError("execution plan: actions are required")

    expected = build_execution_plan(work_packet, list(actions))
    if plan != expected:
        raise ExecutorError("execution plan does not match work packet")

    return packet, list(actions)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _capture_meta(raw):
    return {
        "sha256": _sha256(raw),
        "size_bytes": len(raw),
        "preview": raw[:MAX_PREVIEW_BYTES].decode(
            "utf-8",
            errors="replace",
        ),
        "preview_truncated": len(raw) > MAX_PREVIEW_BYTES,
    }


def _assert_safe_git_argv(argv, git_base=None):
    if not isinstance(argv, list) or not argv or argv[0] != GIT:
        raise ExecutorError("subprocess argv is not an approved Git command")

    approved = [
        [GIT, "rev-parse", "HEAD"],
    ]
    if git_base is not None:
        approved.extend([
            [GIT, "merge-base", "--is-ancestor", git_base, "HEAD"],
            [
                GIT,
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--ignore-submodules=all",
                "--check",
                f"{git_base}...HEAD",
            ],
            [
                GIT,
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--ignore-submodules=all",
                "--name-only",
                "-z",
                f"{git_base}...HEAD",
            ],
        ])

    if argv not in approved:
        raise ExecutorError("subprocess argv is outside the Git allowlist")


def _run_process(argv, *, git_base=None):
    _assert_safe_git_argv(argv, git_base=git_base)

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            completed = subprocess.run(
                argv,
                cwd=ROOT,
                env=SAFE_ENV,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                check=False,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
            exit_code = int(completed.returncode)
            timed_out = False
        except subprocess.TimeoutExpired:
            exit_code = 124
            timed_out = True

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read()
        stderr = stderr_file.read()

    return {
        "argv": list(argv),
        "working_directory": "REPOSITORY_ROOT",
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
    }


def _repository_probe(packet, runner):
    head = runner([GIT, "rev-parse", "HEAD"])
    if head["exit_code"] != 0:
        raise ExecutorError("repository HEAD probe failed")
    head_sha = head["stdout"].decode("utf-8", errors="replace").strip()
    if not SHA40_RE.fullmatch(head_sha):
        raise ExecutorError("repository HEAD probe returned invalid SHA")

    ancestry = runner(
        [
            GIT,
            "merge-base",
            "--is-ancestor",
            packet["git_base"],
            "HEAD",
        ],
        git_base=packet["git_base"],
    )
    if ancestry["exit_code"] != 0:
        raise ExecutorError(
            "work-packet git_base is not an ancestor of repository HEAD"
        )

    return head_sha


def _action_argv(action_id, git_base):
    if action_id == "diff-check":
        return [
            GIT,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=all",
            "--check",
            f"{git_base}...HEAD",
        ]
    if action_id == "scope-check":
        return [
            GIT,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=all",
            "--name-only",
            "-z",
            f"{git_base}...HEAD",
        ]
    raise ExecutorError("unknown action ID")


def _action_result(action_id, packet, process_result):
    stdout = process_result["stdout"]
    stderr = process_result["stderr"]
    status = "PASS" if process_result["exit_code"] == 0 else "FAIL"
    observations = {}

    if action_id == "scope-check" and status == "PASS":
        changed = [
            item.decode("utf-8", errors="strict")
            for item in stdout.split(b"\0")
            if item
        ]
        violations = []
        for path in changed:
            if not any(
                _path_within(path, prefix)
                for prefix in packet["allowed_path_prefixes"]
            ):
                violations.append(
                    {"path": path, "reason": "OUTSIDE_ALLOWED_SCOPE"}
                )
            if any(
                _path_within(path, prefix)
                for prefix in packet["prohibited_path_prefixes"]
            ):
                violations.append(
                    {"path": path, "reason": "PROHIBITED_PATH"}
                )
            if any(
                _path_within(path, prefix)
                for prefix in packet["known_protected_prefixes"]
            ):
                violations.append(
                    {"path": path, "reason": "PROTECTED_PATH"}
                )
        observations = {
            "changed_paths": sorted(changed),
            "violations": sorted(
                violations,
                key=lambda x: (x["path"], x["reason"]),
            ),
        }
        if violations:
            status = "FAIL"

    body = {
        "action_id": action_id,
        "validation_label": action_id,
        "argv": process_result["argv"],
        "working_directory": process_result["working_directory"],
        "exit_code": process_result["exit_code"],
        "timed_out": process_result["timed_out"],
        "status": status,
        "stdout": _capture_meta(stdout),
        "stderr": _capture_meta(stderr),
        "observations": observations,
    }
    body["action_evidence_sha256"] = canonical_hash(body)
    return body


def execute_plan(work_packet, execution_plan, *, runner=_run_process):
    packet, actions = validate_execution_plan(
        work_packet,
        execution_plan,
    )

    head_sha = _repository_probe(packet, runner)
    action_rows = []

    for action_id in actions:
        argv = _action_argv(action_id, packet["git_base"])
        result = runner(
            argv,
            git_base=packet["git_base"],
        )
        action_rows.append(
            _action_result(action_id, packet, result)
        )

    overall_status = (
        "PASS"
        if all(row["status"] == "PASS" for row in action_rows)
        else "FAIL"
    )

    payload = {
        "execution_evidence_version": EVIDENCE_VERSION,
        "executor_version": VERSION,
        "task_id": packet["task_id"],
        "git_base": packet["git_base"],
        "repository_head_sha": head_sha,
        "work_packet_content_sha256": packet[
            "work_packet_content_sha256"
        ],
        "execution_plan_content_sha256": execution_plan[
            "execution_plan_content_sha256"
        ],
        "overall_status": overall_status,
        "actions": action_rows,
        "validations": [
            {
                "label": row["validation_label"],
                "status": row["status"],
                "evidence_sha256": row["action_evidence_sha256"],
            }
            for row in action_rows
        ],
        "authority": dict(EXECUTOR_AUTHORITY),
        "capabilities": dict(EXECUTOR_CAPABILITIES),
    }
    payload["execution_evidence_content_sha256"] = canonical_hash(payload)
    return payload


def execution_exit_code(evidence):
    if evidence.get("overall_status") == "PASS":
        return 0
    if evidence.get("overall_status") == "FAIL":
        return 1
    raise ExecutorError("unknown execution evidence status")


def _load_json(path, role):
    try:
        value = json.loads(Path(path).read_text())
    except Exception as exc:
        raise ExecutorError(f"{role}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise ExecutorError(f"{role}: expected JSON object")
    return value


def _write_new_json(path, value):
    path = Path(path)
    if path.exists():
        raise ExecutorError("output already exists; refusing overwrite")
    if not path.parent.is_dir():
        raise ExecutorError("output parent directory does not exist")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--work-packet", required=True)
    plan_parser.add_argument("--action", action="append", required=True)
    plan_parser.add_argument("--output", required=True)

    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--work-packet", required=True)
    execute_parser.add_argument("--execution-plan", required=True)
    execute_parser.add_argument("--output", required=True)

    args = parser.parse_args()

    work_packet = _load_json(args.work_packet, "work packet")

    if args.mode == "plan":
        plan = build_execution_plan(work_packet, args.action)
        _write_new_json(args.output, plan)
        print("RND_CONTROLLED_EXECUTOR_PLAN: PASS")
        print(f"actions={len(plan['actions'])}")
        print("candidate_code_execution=FALSE")
        print("arbitrary_subprocess=FALSE")
        return 0

    evidence = execute_plan(
        work_packet,
        _load_json(args.execution_plan, "execution plan"),
    )
    _write_new_json(args.output, evidence)
    print("RND_CONTROLLED_EXECUTOR_EXECUTE: " + evidence["overall_status"])
    print(f"actions={len(evidence['actions'])}")
    print("candidate_code_execution=FALSE")
    print("arbitrary_subprocess=FALSE")
    print("automatic_merge=FALSE")
    print("automatic_promotion=FALSE")
    return execution_exit_code(evidence)


if __name__ == "__main__":
    raise SystemExit(main())
