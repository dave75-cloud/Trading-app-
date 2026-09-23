#!/usr/bin/env python3
"""Fail-closed contract validation for governed autonomous R&D task specs."""

from __future__ import annotations

import hashlib
import json
import re


VERSION = "RND-task-spec-v0.1"
TASK_RE = re.compile(r"^RND-[0-9]{4}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

KNOWN_PROTECTED_PREFIXES = (
    "tools/m006e",
    "tools/m006e9_forward_observation",
    "tools/pre_monday",
    "cli",
    ".github/workflows",
)


class TaskSpecError(ValueError):
    pass


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def canonical_hash(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise TaskSpecError(f"{name} must be a non-empty string")
    return value.strip()


def _string_list(value, name, *, nonempty=True):
    if not isinstance(value, list):
        raise TaskSpecError(f"{name} must be list[str]")
    out = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise TaskSpecError(f"{name} must contain non-empty strings")
        out.append(item.strip())
    if nonempty and not out:
        raise TaskSpecError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise TaskSpecError(f"{name} contains duplicates")
    return out


def normalize_repo_path(value, name):
    text = _text(value, name)
    if "\\" in text:
        raise TaskSpecError(f"{name} must use repository '/' separators")
    if text.startswith("/"):
        raise TaskSpecError(f"{name} must be repository-relative")
    parts = [p for p in text.rstrip("/").split("/") if p]
    if not parts or any(p in {".", ".."} for p in parts):
        raise TaskSpecError(f"{name} is not a safe repository path")
    return "/".join(parts)


def path_within(path, prefix):
    path = normalize_repo_path(path, "path")
    prefix = normalize_repo_path(prefix, "prefix")
    return path == prefix or path.startswith(prefix + "/")


def validate_task_spec(raw):
    if not isinstance(raw, dict):
        raise TaskSpecError("task spec must be a JSON object")

    if raw.get("contract_version") != VERSION:
        raise TaskSpecError("unsupported contract_version")

    task_id = _text(raw.get("task_id"), "task_id")
    if not TASK_RE.fullmatch(task_id):
        raise TaskSpecError("task_id must match RND-NNNN")

    git_base = _text(raw.get("git_base"), "git_base").lower()
    if not SHA40_RE.fullmatch(git_base):
        raise TaskSpecError("git_base must be a 40-character lowercase SHA")

    title = _text(raw.get("title"), "title")
    objective = _text(raw.get("objective"), "objective")

    allowed = [
        normalize_repo_path(x, "allowed_path_prefix")
        for x in _string_list(raw.get("allowed_path_prefixes"), "allowed_path_prefixes")
    ]
    for prefix in allowed:
        if not path_within(prefix, "rnd"):
            raise TaskSpecError(
                "allowed_path_prefixes may grant authority only under rnd/"
            )

    prohibited = [
        normalize_repo_path(x, "prohibited_path_prefix")
        for x in _string_list(
            raw.get("prohibited_path_prefixes", []),
            "prohibited_path_prefixes",
            nonempty=False,
        )
    ]

    outputs = [
        normalize_repo_path(x, "required_output")
        for x in _string_list(raw.get("required_outputs"), "required_outputs")
    ]
    for path in outputs:
        if not any(path_within(path, prefix) for prefix in allowed):
            raise TaskSpecError("required_output is outside allowed_path_prefixes")
        if any(path_within(path, prefix) for prefix in prohibited):
            raise TaskSpecError("required_output is inside prohibited_path_prefixes")

    validations = _string_list(
        raw.get("required_validation_labels"),
        "required_validation_labels",
    )
    success = _string_list(raw.get("success_criteria"), "success_criteria")
    stops = _string_list(raw.get("stop_conditions"), "stop_conditions")

    if raw.get("human_gate_required") is not True:
        raise TaskSpecError("human_gate_required must be true")
    if raw.get("automatic_merge") is not False:
        raise TaskSpecError("automatic_merge must be false")
    if raw.get("automatic_promotion") is not False:
        raise TaskSpecError("automatic_promotion must be false")

    normalized = {
        "contract_version": VERSION,
        "task_id": task_id,
        "title": title,
        "git_base": git_base,
        "objective": objective,
        "allowed_path_prefixes": allowed,
        "prohibited_path_prefixes": prohibited,
        "required_outputs": outputs,
        "required_validation_labels": validations,
        "success_criteria": success,
        "stop_conditions": stops,
        "human_gate_required": True,
        "automatic_merge": False,
        "automatic_promotion": False,
    }
    return normalized


def task_spec_hash(raw):
    return canonical_hash(validate_task_spec(raw))
