#!/usr/bin/env python3

"""
M006e.9c v1.1 — Forward-Observation Graduation Monitor

The monitor cannot promote M006e or enable execution.

Possible states:
    NOT_ELIGIBLE
    EXTEND_OBSERVATION
    ELIGIBLE_FOR_FORMAL_REVIEW
    BLOCKED_BY_HARD_GATE
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


VERSION = "M006e.9c-v1.1"

HERE = Path(__file__).resolve().parent

LEDGER_MODULE = (
    HERE / "m006e9b_cumulative_ledger.py"
)

MIN_ACCEPTED_SESSIONS = 25
MIN_AUTHORITATIVE_EVENTS = 100

SATISFACTORY_UPSTREAM_FAILURE_RATE_PCT = 5.0
INVESTIGATE_UPSTREAM_FAILURE_RATE_PCT = 10.0

TARGET_RETROSPECTIVE_TWELVE_AVAILABILITY_PCT = 99.0


def load_ledger_module():
    spec = importlib.util.spec_from_file_location(
        "m006e9b",
        LEDGER_MODULE,
    )

    module = importlib.util.module_from_spec(spec)

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module


def evaluate() -> dict:
    module = load_ledger_module()
    ledger = module.build_ledger()

    s = ledger["summary"]
    p = ledger["provider_path"]
    r = ledger["reconciliation"]
    i = ledger["integrity"]
    z = ledger["safety"]

    hard_gate_failures = []
    review_flags = []

    # ------------------------------------------------------------
    # HARD GATES
    # ------------------------------------------------------------

    if not i["all_m006e2_hashes_match"]:
        hard_gate_failures.append(
            "M006e.2 frozen hash mismatch"
        )

    if not z["zero_recorded_safety_violations"]:
        hard_gate_failures.append(
            "recorded safety violation"
        )

    if s["unknown_cycles"] > 0:
        hard_gate_failures.append(
            "unclassified orchestration cycles remain"
        )

    if (
        r.get(
            "reconciliation_event_count_mismatches",
            0,
        )
        > 0
    ):
        hard_gate_failures.append(
            "authoritative/reconciliation event-count mismatch"
        )

    if (
        r.get(
            "provider_event_count_mismatches",
            0,
        )
        > 0
    ):
        hard_gate_failures.append(
            "authoritative/provider-path event-count mismatch"
        )

    # ------------------------------------------------------------
    # REVIEW FLAGS
    #
    # These prevent automatic eligibility for formal review if they
    # remain unresolved, but they are NOT safety hard gates.
    # ------------------------------------------------------------

    if (
        p.get("direction_disagreements", 0)
        > 0
    ):
        review_flags.append(
            "provider directional disagreement requires investigation"
        )

    if (
        p.get("divergence_over_10bps", 0)
        > 0
    ):
        review_flags.append(
            ">10 bps provider divergence requires investigation"
        )

    sessions = int(
        s["accepted_sessions"]
    )

    events = int(
        s["authoritative_events"]
    )

    failure_rate = s.get(
        "contained_upstream_failure_rate_pct"
    )

    twelve_availability = p.get(
        "retrospective_twelve_availability_pct"
    )

    if (
        failure_rate is not None
        and failure_rate
        > INVESTIGATE_UPSTREAM_FAILURE_RATE_PCT
    ):
        review_flags.append(
            "contained upstream-failure rate exceeds investigation threshold"
        )

    if (
        twelve_availability is not None
        and events > 0
        and twelve_availability
        < TARGET_RETROSPECTIVE_TWELVE_AVAILABILITY_PCT
    ):
        review_flags.append(
            "retrospective Twelve availability below provisional target"
        )

    criteria = {
        "accepted_sessions": {
            "current": sessions,
            "required": MIN_ACCEPTED_SESSIONS,
            "pass": (
                sessions
                >= MIN_ACCEPTED_SESSIONS
            ),
        },

        "authoritative_events": {
            "current": events,
            "required": MIN_AUTHORITATIVE_EVENTS,
            "pass": (
                events
                >= MIN_AUTHORITATIVE_EVENTS
            ),
        },

        "contained_upstream_failure_rate": {
            "current_pct": failure_rate,
            "satisfactory_lte_pct":
                SATISFACTORY_UPSTREAM_FAILURE_RATE_PCT,
            "investigate_gt_pct":
                INVESTIGATE_UPSTREAM_FAILURE_RATE_PCT,
            "status": (
                "SATISFACTORY"
                if (
                    failure_rate is not None
                    and failure_rate
                    <= SATISFACTORY_UPSTREAM_FAILURE_RATE_PCT
                )
                else "INVESTIGATE"
                if (
                    failure_rate is not None
                    and failure_rate
                    > INVESTIGATE_UPSTREAM_FAILURE_RATE_PCT
                )
                else "OBSERVE"
            ),
        },

        "retrospective_twelve_availability": {
            "current_pct":
                twelve_availability,
            "provisional_target_pct":
                TARGET_RETROSPECTIVE_TWELVE_AVAILABILITY_PCT,
            "status": (
                "PASS"
                if (
                    twelve_availability is not None
                    and twelve_availability
                    >= TARGET_RETROSPECTIVE_TWELVE_AVAILABILITY_PCT
                )
                else "INSUFFICIENT_EVENT_EVIDENCE"
                if events == 0
                else "OBSERVE"
            ),
        },

        "pending_human_review": {
            "count":
                s["pending_review_sessions"],
            "pass": (
                s["pending_review_sessions"]
                == 0
            ),
        },
    }

    if hard_gate_failures:
        overall = "BLOCKED_BY_HARD_GATE"

    elif (
        sessions < MIN_ACCEPTED_SESSIONS
        or events < MIN_AUTHORITATIVE_EVENTS
    ):
        overall = "NOT_ELIGIBLE"

    elif (
        s["pending_review_sessions"] > 0
        or review_flags
    ):
        overall = "EXTEND_OBSERVATION"

    else:
        overall = (
            "ELIGIBLE_FOR_FORMAL_REVIEW"
        )

    return {
        "version": VERSION,

        "principle": (
            "This monitor cannot promote "
            "M006e or enable execution."
        ),

        "overall_status": overall,

        "hard_gate_failures":
            hard_gate_failures,

        "review_flags":
            review_flags,

        "criteria":
            criteria,

        "progress": {
            "session_progress_pct":
                round(
                    min(
                        sessions
                        / MIN_ACCEPTED_SESSIONS,
                        1.0,
                    )
                    * 100,
                    1,
                ),

            "event_progress_pct":
                round(
                    min(
                        events
                        / MIN_AUTHORITATIVE_EVENTS,
                        1.0,
                    )
                    * 100,
                    1,
                ),
        },
    }


def main() -> int:
    result = evaluate()

    c = result["criteria"]
    p = result["progress"]

    print("M006e.9c v1.1 GRADUATION MONITOR")

    print(
        f"  overall status: "
        f"{result['overall_status']}"
    )

    print(
        "  accepted sessions: "
        f"{c['accepted_sessions']['current']}/"
        f"{c['accepted_sessions']['required']} "
        f"({p['session_progress_pct']}%)"
    )

    print(
        "  authoritative events: "
        f"{c['authoritative_events']['current']}/"
        f"{c['authoritative_events']['required']} "
        f"({p['event_progress_pct']}%)"
    )

    print(
        "  upstream-failure rate: "
        f"{c['contained_upstream_failure_rate']['current_pct']}% "
        f"[{c['contained_upstream_failure_rate']['status']}]"
    )

    print(
        "  retrospective Twelve availability: "
        f"{c['retrospective_twelve_availability']['current_pct']}% "
        f"[{c['retrospective_twelve_availability']['status']}]"
    )

    print(
        "  pending human reviews: "
        f"{c['pending_human_review']['count']}"
    )

    if result["hard_gate_failures"]:
        print("  HARD-GATE FAILURES:")

        for item in result[
            "hard_gate_failures"
        ]:
            print(f"    - {item}")

    else:
        print("  hard gates: PASS")

    if result["review_flags"]:
        print("  REVIEW FLAGS:")

        for item in result[
            "review_flags"
        ]:
            print(f"    - {item}")

    else:
        print("  review flags: NONE")

    print(
        "  automatic promotion capability: NONE"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
