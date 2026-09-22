#!/usr/bin/env python3
"""Fail-closed, offline orchestration for one prospective M006f session."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from accepted_event_replay_adapter import (
    accepted_reconciliation_files,
    adapt,
    load_market,
    load_rows,
)
from market_evidence_contract import load_jsonl, validate_rows
from shadow_session_packager import build_package
from shadow_session_review_dossier import build_dossier, render_markdown
from shadow_simulator import simulate


VERSION = "M006f-prospective-shadow-session-pipeline-v0.1"


class PipelineError(ValueError):
    pass


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _regular_file(path, role):
    path = Path(path)
    if not path.is_file():
        raise PipelineError(f"{role}: required regular file does not exist")
    return path.resolve()


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))


def run_pipeline(*, session_id, session_date_utc, accepted_session,
                 reconciliation, disposition, market_evidence, output_dir,
                 initial_equity_aud=100000.0, slippage_bps=0.0):
    """Run all stages and atomically publish the completed output directory."""
    sources = {
        "accepted_session": _regular_file(accepted_session, "accepted_session"),
        "reconciliation": _regular_file(reconciliation, "reconciliation"),
        "market_evidence": _regular_file(market_evidence, "market_evidence"),
    }
    if disposition is not None:
        sources["disposition"] = _regular_file(disposition, "disposition")

    try:
        accepted_payload = json.loads(sources["accepted_session"].read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise PipelineError(f"accepted_session: invalid JSON: {exc}") from exc

    authoritative_day = str(accepted_payload.get("day", "")).strip()
    if not authoritative_day:
        raise PipelineError("accepted_session: missing authoritative day")
    if str(session_date_utc).strip() != authoritative_day:
        raise PipelineError(
            f"session_date_utc {session_date_utc!r} does not match "
            f"accepted-session day {authoritative_day!r}"
        )

    reconciliation_name = Path(
        str(accepted_payload.get("reconciliation", {}).get("source_file", ""))
    ).name
    if not reconciliation_name:
        raise PipelineError("accepted_session: reconciliation source_file is missing")

    output = Path(output_dir).resolve()
    if output.exists():
        raise PipelineError("session output directory already exists; refusing overwrite")
    if not output.parent.is_dir():
        raise PipelineError("output parent directory does not exist")

    # Validate the exact contract before creating even a temporary output tree.
    market_rows = load_jsonl(sources["market_evidence"])
    market_validation = validate_rows(market_rows)

    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        input_root = temporary / ".adapter-inputs"
        sessions = input_root / "sessions"
        reconciliations = input_root / "reconciliation"
        dispositions = input_root / "dispositions"
        for directory in (sessions, reconciliations, dispositions):
            directory.mkdir(parents=True)

        # The pipeline accepts explicit paths, while the established replay adapter
        # intentionally discovers formal evidence by canonical filename patterns.
        # Normalize only the temporary copies; never alter the source evidence.
        shutil.copyfile(sources["accepted_session"], sessions / "m006e9a_explicit.json")
        shutil.copyfile(sources["reconciliation"], reconciliations / reconciliation_name)
        if "disposition" in sources:
            shutil.copyfile(
                sources["disposition"],
                dispositions / "session_disposition_explicit.json",
            )

        accepted_names = accepted_reconciliation_files(sessions, reconciliations, dispositions)
        if accepted_names != [reconciliation_name]:
            raise PipelineError("explicit reconciliation was not uniquely accepted")
        source_rows = load_rows(reconciliations, accepted_names)
        replay = adapt(source_rows, load_market(sources["market_evidence"]))
        replay["summary"].update({"accepted_sessions": 1, "acceptance_gate_pass": True})
        if replay["summary"]["suppressed_chains"] != 0:
            raise PipelineError("market evidence is incomplete for an accepted replay chain")

        audit_path = temporary / "replay_audit.json"
        events_path = temporary / "replay_events.jsonl"
        shadow_path = temporary / "shadow_result.json"
        package_path = temporary / "shadow_session_package.json"
        dossier_path = temporary / "review_dossier.json"
        markdown_path = temporary / "review_dossier.md"
        _write_json(audit_path, replay)
        _write_jsonl(events_path, replay["replay_events"])

        shadow = simulate(replay["replay_events"], initial_equity_aud=initial_equity_aud,
                          slippage_bps=slippage_bps)
        _write_json(shadow_path, shadow)
        package = build_package(session_id, session_date_utc, sources["accepted_session"],
                                sources["market_evidence"], audit_path, events_path, shadow_path)
        _write_json(package_path, package)
        dossier = build_dossier(package_path)
        if dossier["review"]["human_disposition"] is not None:
            raise PipelineError("pipeline must not create a human disposition")
        _write_json(dossier_path, dossier)
        markdown_path.write_text(render_markdown(dossier))

        manifest = {
            "pipeline_version": VERSION,
            "session_id": str(session_id),
            "session_date_utc": str(session_date_utc),
            "source_sha256": {name: _sha256(path) for name, path in sorted(sources.items())},
            "artifact_sha256": {
                path.name: _sha256(path) for path in
                (audit_path, events_path, shadow_path, package_path, dossier_path, markdown_path)
            },
            "market_evidence_validation": market_validation,
            "safety": {
                "broker_transport": False,
                "network_capability": False,
                "submission_capability": False,
                "automatic_disposition": False,
                "automatic_promotion": False,
                "promotion_authority": "NONE",
                "human_review_required": True,
            },
        }
        _write_json(temporary / "pipeline_manifest.json", manifest)
        shutil.rmtree(input_root)
        temporary.rename(output)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--session-date-utc", required=True)
    parser.add_argument("--accepted-session", required=True)
    parser.add_argument("--reconciliation", required=True)
    parser.add_argument("--disposition")
    parser.add_argument("--market-evidence", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--initial-equity-aud", type=float, default=100000.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    args = parser.parse_args()
    manifest = run_pipeline(**vars(args))
    print("M006F_PROSPECTIVE_SHADOW_SESSION_PIPELINE: PASS")
    print(f"session_id={manifest['session_id']}")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")
    print("human_disposition=UNSET")


if __name__ == "__main__":
    main()
