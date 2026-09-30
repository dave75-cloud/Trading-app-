#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def build_dossier(ledger: dict, reliability: dict, concurrency: dict) -> tuple[dict, str]:
    summary = ledger.get("summary", {})
    review = ledger.get("review", {})
    safety = ledger.get("safety", {})
    integrity = ledger.get("integrity", {})

    sessions = int(summary.get("accepted_sessions", summary.get("sessions_accepted", 0)) or 0)
    events = int(summary.get("authoritative_events", 0) or 0)

    # Current frozen threshold contract.
    session_threshold = 25
    event_threshold = 100
    thresholds_met = sessions >= session_threshold and events >= event_threshold

    hard_gate_pass = bool(
        isinstance(safety, dict)
        and safety.get("zero_recorded_safety_violations") is True
        and isinstance(review, dict)
        and len(review.get("pending_review_days", [])) == 0
    )

    integrity_pass = bool(
        isinstance(integrity, dict)
        and integrity.get("all_m006e2_hashes_match") is True
    )

    reliability_tax = reliability.get("failure_taxonomy", {})
    incident = concurrency.get("incident", {})

    data = {
        "version": "RND-0009-v1.0",
        "accepted_sessions": sessions,
        "required_sessions": session_threshold,
        "authoritative_events": events,
        "required_events": event_threshold,
        "minimum_thresholds_met": thresholds_met,
        "hard_gate_pass": hard_gate_pass,
        "integrity_pass": integrity_pass,
        "contained_upstream_failures": reliability_tax.get("contained_upstream"),
        "contained_local_concurrency_failures": reliability_tax.get("contained_local_concurrency"),
        "unclassified_raw_failures": reliability_tax.get("unclassified_raw_failures"),
        "concurrency_fail_closed": incident.get("fail_closed"),
        "human_decision_required": True,
        "automatic_promotion": False,
        "decision_options": [
            "PROMOTE_TO_SHADOW",
            "EXTEND_OBSERVATION",
            "REJECT_REENGINEER",
        ],
        "selected_outcome": None,
    }

    md = f"""# Forward-Observation Graduation Dossier

## Threshold status

- Accepted sessions: {sessions}/{session_threshold}
- Authoritative events: {events}/{event_threshold}
- Minimum thresholds met: {str(thresholds_met).upper()}

## Safety and integrity

- Hard-gate evidence: {str(hard_gate_pass).upper()}
- Integrity evidence: {str(integrity_pass).upper()}
- Contained upstream failures: {data['contained_upstream_failures']}
- Contained local concurrency failures: {data['contained_local_concurrency_failures']}
- Unclassified raw failures: {data['unclassified_raw_failures']}
- Recorded concurrency incident failed closed: {data['concurrency_fail_closed']}

## Decision boundary

This dossier does not select an outcome.

Human review is required to choose among:

- PROMOTE_TO_SHADOW
- EXTEND_OBSERVATION
- REJECT_REENGINEER

Automatic promotion: NONE.
"""
    return data, md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--reliability", required=True)
    ap.add_argument("--concurrency", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    data, md = build_dossier(
        _read(Path(args.ledger)),
        _read(Path(args.reliability)),
        _read(Path(args.concurrency)),
    )

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graduation_dossier.json").write_text(json.dumps(data, indent=2) + "\n")
    (out / "graduation_dossier.md").write_text(md)

    print("GRADUATION_DOSSIER: COMPLETE")
    print(f"minimum_thresholds_met={data['minimum_thresholds_met']}")
    print("human_decision_required=TRUE")
    print("automatic_promotion=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
