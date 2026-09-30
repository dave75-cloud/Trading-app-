#!/usr/bin/env python3
"""Bounded offline workflow orchestration for one prospective M006f shadow session."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prospective_shadow_session_pipeline import run_pipeline


VERSION = "M006f-prospective-shadow-workflow-orchestrator-v0.1"
MARKET_EVIDENCE_TEMPLATE = "market_evidence_{day}.jsonl"
OUTPUT_TEMPLATE = "shadow_session_{day}"


class WorkflowError(ValueError):
    pass


class NoEligibleSession(WorkflowError):
    pass


def _directory(path, role):
    p = Path(path).resolve()
    if not p.is_dir():
        raise WorkflowError(f"{role}: required directory does not exist")
    return p


def _load_json(path, role):
    p = Path(path)
    if not p.is_file():
        raise WorkflowError(f"{role}: required file does not exist")
    try:
        value = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"{role}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowError(f"{role}: expected JSON object")
    return value


def _candidate_record(session_path, reconciliation_root, disposition_root,
                      market_evidence_root, output_root):
    session = _load_json(session_path, "accepted_session")
    day = str(session.get("day", "")).strip()
    if not day:
        raise WorkflowError(f"{Path(session_path).name}: accepted session missing day")

    reconciliation_name = Path(
        str(session.get("reconciliation", {}).get("source_file", ""))
    ).name
    if not reconciliation_name:
        return {
            "day": day,
            "eligible": False,
            "reason": "accepted session lacks reconciliation source_file",
        }

    reconciliation = reconciliation_root / reconciliation_name
    market_evidence = market_evidence_root / MARKET_EVIDENCE_TEMPLATE.format(day=day)
    disposition = disposition_root / f"session_disposition_{day}.json"
    output = output_root / OUTPUT_TEMPLATE.format(day=day)

    reason = None
    if output.exists():
        reason = "output already exists"
    elif not reconciliation.is_file():
        reason = "declared reconciliation is missing"
    elif not market_evidence.is_file():
        reason = "exact market evidence is missing"
    else:
        recon = _load_json(reconciliation, "reconciliation")
        if str(recon.get("day", "")).strip() != day:
            reason = "reconciliation day mismatch"

    verdict = str(session.get("orchestration", {}).get("verdict", "")).strip().upper()
    disposition_required = verdict != "CLEAN"

    if reason is None and disposition_required:
        if not disposition.is_file():
            reason = "non-CLEAN source lacks required disposition"
        else:
            disp = _load_json(disposition, "disposition")
            if str(disp.get("day", "")).strip() != day:
                reason = "disposition day mismatch"
            elif disp.get("accepted") is not True:
                reason = "disposition is not accepted"
            elif not str(disp.get("reviewed_disposition", "")).startswith("ACCEPTED"):
                reason = "disposition is not human-accepted"

    return {
        "day": day,
        "eligible": reason is None,
        "reason": reason,
        "session": str(Path(session_path).resolve()),
        "reconciliation": str(reconciliation.resolve()),
        "disposition": str(disposition.resolve()) if disposition_required else None,
        "market_evidence": str(market_evidence.resolve()),
        "output": str(output.resolve()),
        "session_id": f"prospective-{day}",
    }


def discover_candidates(*, accepted_session_root, reconciliation_root,
                        disposition_root, market_evidence_root, output_root):
    roots = {
        "accepted_session_root": _directory(accepted_session_root, "accepted_session_root"),
        "reconciliation_root": _directory(reconciliation_root, "reconciliation_root"),
        "disposition_root": _directory(disposition_root, "disposition_root"),
        "market_evidence_root": _directory(market_evidence_root, "market_evidence_root"),
        "output_root": _directory(output_root, "output_root"),
    }

    records = []
    days = set()
    for session_path in sorted(roots["accepted_session_root"].glob("m006e9a_*.json")):
        record = _candidate_record(
            session_path,
            roots["reconciliation_root"],
            roots["disposition_root"],
            roots["market_evidence_root"],
            roots["output_root"],
        )
        if record["day"] in days:
            raise WorkflowError(f"duplicate accepted session day: {record['day']}")
        days.add(record["day"])
        records.append(record)

    records.sort(key=lambda x: (x["day"], x.get("session", "")))
    return records


def select_candidate(*, accepted_session_root, reconciliation_root,
                     disposition_root, market_evidence_root, output_root,
                     session_date_utc=None):
    records = discover_candidates(
        accepted_session_root=accepted_session_root,
        reconciliation_root=reconciliation_root,
        disposition_root=disposition_root,
        market_evidence_root=market_evidence_root,
        output_root=output_root,
    )

    if session_date_utc is not None:
        target = str(session_date_utc).strip()
        matches = [r for r in records if r["day"] == target]
        if not matches:
            raise NoEligibleSession(f"{target}: accepted session not found")
        record = matches[0]
        if record["reason"] == "output already exists":
            raise WorkflowError(f"{target}: output already exists; refusing overwrite")
        if not record["eligible"]:
            raise NoEligibleSession(f"{target}: {record['reason']}")
        return record

    eligible = [r for r in records if r["eligible"]]
    if not eligible:
        detail = "; ".join(
            f"{r['day']}: {r['reason']}" for r in records
        ) or "no accepted session records found"
        raise NoEligibleSession(detail)
    if len(eligible) > 1:
        days = ", ".join(r["day"] for r in eligible)
        raise WorkflowError(f"ambiguous eligible sessions: {days}")
    return eligible[0]


def run_workflow(*, accepted_session_root, reconciliation_root,
                 disposition_root, market_evidence_root, output_root,
                 session_date_utc=None, initial_equity_aud=100000.0,
                 slippage_bps=0.0):
    selected = select_candidate(
        accepted_session_root=accepted_session_root,
        reconciliation_root=reconciliation_root,
        disposition_root=disposition_root,
        market_evidence_root=market_evidence_root,
        output_root=output_root,
        session_date_utc=session_date_utc,
    )

    pipeline_manifest = run_pipeline(
        session_id=selected["session_id"],
        session_date_utc=selected["day"],
        accepted_session=selected["session"],
        reconciliation=selected["reconciliation"],
        disposition=selected["disposition"],
        market_evidence=selected["market_evidence"],
        output_dir=selected["output"],
        initial_equity_aud=initial_equity_aud,
        slippage_bps=slippage_bps,
    )

    return {
        "workflow_version": VERSION,
        "selected_day": selected["day"],
        "session_id": selected["session_id"],
        "output": selected["output"],
        "pipeline_manifest": pipeline_manifest,
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_disposition": False,
            "automatic_promotion": False,
            "promotion_authority": "NONE",
            "human_review_required": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-session-root", required=True)
    parser.add_argument("--reconciliation-root", required=True)
    parser.add_argument("--disposition-root", required=True)
    parser.add_argument("--market-evidence-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--session-date-utc")
    parser.add_argument("--initial-equity-aud", type=float, default=100000.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    args = parser.parse_args()

    try:
        result = run_workflow(**vars(args))
    except NoEligibleSession as exc:
        print("M006F_PROSPECTIVE_SHADOW_WORKFLOW: NO_ELIGIBLE_SESSION")
        print(str(exc))
        return 2
    except WorkflowError as exc:
        print("M006F_PROSPECTIVE_SHADOW_WORKFLOW: FAIL_CLOSED")
        print(str(exc))
        return 1

    print("M006F_PROSPECTIVE_SHADOW_WORKFLOW: PASS")
    print(f"selected_day={result['selected_day']}")
    print(f"session_id={result['session_id']}")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")
    print("automatic_disposition=FALSE")
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")
    print("human_review_required=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
