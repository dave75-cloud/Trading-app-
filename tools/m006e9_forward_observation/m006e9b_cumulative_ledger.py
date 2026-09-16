#!/usr/bin/env python3

"""
M006e.9b — Cumulative Forward-Observation Ledger

Reads:
    data/research_runs/M006E_FORWARD_OBSERVATION/sessions/
    data/research_runs/M006E_FORWARD_OBSERVATION/session_dispositions.json
    data/research_runs/M006E_FORWARD_OBSERVATION/dispositions/

Writes only when --write is supplied:
    data/research_runs/M006E_FORWARD_OBSERVATION/ledger/

No network. No broker access. No subprocesses.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


VERSION = "M006e.9b-v1.0"

ROOT = Path(
    "data/research_runs/M006E_FORWARD_OBSERVATION"
)

SESSION_DIR = ROOT / "sessions"
DISPOSITION_DIR = ROOT / "dispositions"
BASELINE_DISPOSITIONS = ROOT / "session_dispositions.json"
LEDGER_DIR = ROOT / "ledger"


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(obj, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return obj


def load_dispositions() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    if BASELINE_DISPOSITIONS.exists():
        obj = load_json(BASELINE_DISPOSITIONS)

        for day, record in (
            obj.get("sessions") or {}
        ).items():
            if isinstance(record, dict):
                result[day] = {
                    **record,
                    "source_file":
                        str(BASELINE_DISPOSITIONS),
                }

    if DISPOSITION_DIR.exists():
        for path in sorted(
            DISPOSITION_DIR.glob(
                "session_disposition_*.json"
            )
        ):
            obj = load_json(path)
            day = obj.get("day")

            if not day:
                continue

            result[str(day)] = {
                **obj,
                "source_file": str(path),
            }

    return result


def session_files() -> list[Path]:
    if not SESSION_DIR.exists():
        return []

    return sorted(
        SESSION_DIR.glob(
            "m006e9a_????-??-??.json"
        )
    )


def build_ledger() -> dict[str, Any]:
    dispositions = load_dispositions()

    rows = []

    totals = Counter()

    provider = Counter()
    reconciliation = Counter()

    max_divergence = None

    raw_verdicts = Counter()
    reviewed_dispositions = Counter()

    integrity_failures = []
    safety_failures = []
    pending_review = []

    for path in session_files():
        session = load_json(path)

        day = str(session.get("day"))
        o = session.get("orchestration") or {}
        e = session.get("events") or {}
        p = session.get("provider_path") or {}
        r = session.get("reconciliation") or {}
        i = session.get("integrity") or {}
        s = session.get("safety") or {}

        disposition = dispositions.get(day)

        if disposition is None:
            pending_review.append(day)

        reviewed = (
            disposition.get(
                "reviewed_disposition"
            )
            if disposition else
            "PENDING_REVIEW"
        )

        accepted = (
            bool(disposition.get("accepted"))
            if disposition else
            False
        )

        contained_failures = (
            int(
                disposition.get(
                    "contained_upstream_failures"
                )
                or 0
            )
            if disposition else
            0
        )

        expected = int(
            o.get("expected_cycles") or 0
        )

        observed = int(
            o.get("observed_cycles") or 0
        )

        passed = int(
            o.get("pass_cycles") or 0
        )

        skipped = int(
            o.get("skip_cycles") or 0
        )

        failed = int(
            o.get("fail_cycles") or 0
        )

        unknown = int(
            o.get("unknown_cycles") or 0
        )

        events = int(
            e.get("authoritative_events") or 0
        )

        raw_verdict = str(
            o.get("verdict") or "UNKNOWN"
        )

        raw_verdicts[raw_verdict] += 1
        reviewed_dispositions[
            str(reviewed)
        ] += 1

        totals["sessions"] += 1
        totals["expected_cycles"] += expected
        totals["observed_cycles"] += observed
        totals["pass_cycles"] += passed
        totals["skip_cycles"] += skipped
        totals["fail_cycles"] += failed
        totals["unknown_cycles"] += unknown
        totals["authoritative_events"] += events
        totals[
            "contained_upstream_failures"
        ] += contained_failures

        if accepted:
            totals["accepted_sessions"] += 1

        if reviewed == "CLEAN":
            totals["clean_sessions"] += 1

        provider_events = int(
            p.get("events") or 0
        )

        recon_events = int(
            r.get("events") or 0
        )

        provider["events"] += provider_events
        provider["missing_twelve_bars"] += int(
            p.get("missing_twelve_bars") or 0
        )

        provider[
            "direction_disagreements"
        ] += int(
            p.get("direction_disagreements")
            or 0
        )

        provider[
            "volatility_eligibility_disagreements"
        ] += int(
            p.get(
                "volatility_eligibility_disagreements"
            )
            or 0
        )

        provider[
            "divergence_over_10bps"
        ] += int(
            p.get("divergence_over_10bps")
            or 0
        )

        value = p.get(
            "max_abs_close_divergence_bps"
        )

        if isinstance(value, (int, float)):
            value = float(value)

            max_divergence = (
                value
                if max_divergence is None
                else max(
                    max_divergence,
                    value,
                )
            )

        reconciliation["events"] += (
            recon_events
        )

        if events > 0:
            if provider_events != events:
                reconciliation[
                    "provider_event_count_mismatches"
                ] += 1

            if recon_events != events:
                reconciliation[
                    "reconciliation_event_count_mismatches"
                ] += 1

        hash_match = bool(
            i.get("m006e2_hash_match")
        )

        safety_count = int(
            s.get(
                "bridge_and_validation_violation_count"
            )
            or 0
        )

        if not hash_match:
            integrity_failures.append(day)

        if safety_count:
            safety_failures.append(
                {
                    "day": day,
                    "count": safety_count,
                }
            )

        rows.append(
            {
                "day": day,
                "accepted": accepted,
                "reviewed_disposition":
                    reviewed,
                "raw_verdict":
                    raw_verdict,

                "expected_cycles":
                    expected,
                "observed_cycles":
                    observed,
                "pass_cycles":
                    passed,
                "skip_cycles":
                    skipped,
                "fail_cycles":
                    failed,
                "unknown_cycles":
                    unknown,

                "coverage_pct":
                    o.get("coverage_pct"),

                "contained_upstream_failures":
                    contained_failures,

                "authoritative_events":
                    events,

                "provider_events":
                    provider_events,

                "reconciliation_events":
                    recon_events,

                "missing_twelve_bars":
                    int(
                        p.get(
                            "missing_twelve_bars"
                        )
                        or 0
                    ),

                "direction_disagreements":
                    int(
                        p.get(
                            "direction_disagreements"
                        )
                        or 0
                    ),

                "volatility_eligibility_disagreements":
                    int(
                        p.get(
                            "volatility_eligibility_disagreements"
                        )
                        or 0
                    ),

                "divergence_over_10bps":
                    int(
                        p.get(
                            "divergence_over_10bps"
                        )
                        or 0
                    ),

                "max_abs_close_divergence_bps":
                    value,

                "m006e2_hash_match":
                    hash_match,

                "safety_violations":
                    safety_count,

                "session_file":
                    str(path),

                "disposition_file":
                    (
                        disposition.get(
                            "source_file"
                        )
                        if disposition
                        else None
                    ),
            }
        )

    observed = totals[
        "observed_cycles"
    ]

    expected = totals[
        "expected_cycles"
    ]

    accepted_sessions = totals[
        "accepted_sessions"
    ]

    cumulative_coverage_pct = (
        100.0 * observed / expected
        if expected else None
    )

    contained_failure_rate_pct = (
        100.0
        * totals[
            "contained_upstream_failures"
        ]
        / observed
        if observed else None
    )

    retrospective_twelve_availability_pct = (
        100.0
        * (
            provider["events"]
            - provider["missing_twelve_bars"]
        )
        / provider["events"]
        if provider["events"]
        else None
    )

    return {
        "version": VERSION,
        "mode":
            "READ_ONLY_CUMULATIVE_OBSERVATION_LEDGER",

        "sessions": rows,

        "summary": {
            **dict(totals),

            "pending_review_sessions":
                len(pending_review),

            "cumulative_coverage_pct":
                (
                    round(
                        cumulative_coverage_pct,
                        2,
                    )
                    if cumulative_coverage_pct
                    is not None
                    else None
                ),

            "contained_upstream_failure_rate_pct":
                (
                    round(
                        contained_failure_rate_pct,
                        3,
                    )
                    if contained_failure_rate_pct
                    is not None
                    else None
                ),

            "raw_verdicts":
                dict(raw_verdicts),

            "reviewed_dispositions":
                dict(
                    reviewed_dispositions
                ),
        },

        "provider_path": {
            **dict(provider),

            "max_abs_close_divergence_bps":
                max_divergence,

            "retrospective_twelve_availability_pct":
                (
                    round(
                        retrospective_twelve_availability_pct,
                        3,
                    )
                    if retrospective_twelve_availability_pct
                    is not None
                    else None
                ),
        },

        "reconciliation": {
            **dict(reconciliation),
        },

        "integrity": {
            "hash_mismatch_sessions":
                integrity_failures,

            "all_m006e2_hashes_match":
                not integrity_failures,
        },

        "safety": {
            "sessions_with_violations":
                safety_failures,

            "zero_recorded_safety_violations":
                not safety_failures,
        },

        "review": {
            "pending_review_days":
                pending_review,
        },
    }


def print_summary(
    ledger: dict[str, Any],
) -> None:

    s = ledger["summary"]
    p = ledger["provider_path"]
    r = ledger["reconciliation"]
    i = ledger["integrity"]
    z = ledger["safety"]

    print(
        "M006e.9b CUMULATIVE LEDGER"
    )

    print(
        f"  sessions: "
        f"{s['sessions']}"
    )

    print(
        f"  accepted sessions: "
        f"{s['accepted_sessions']}"
    )

    print(
        f"  cycles: "
        f"{s['observed_cycles']}/"
        f"{s['expected_cycles']} observed"
    )

    print(
        f"  PASS/FAIL/SKIP/UNKNOWN: "
        f"{s['pass_cycles']}/"
        f"{s['fail_cycles']}/"
        f"{s['skip_cycles']}/"
        f"{s['unknown_cycles']}"
    )

    print(
        f"  cumulative coverage: "
        f"{s['cumulative_coverage_pct']}%"
    )

    print(
        f"  contained upstream failures: "
        f"{s['contained_upstream_failures']} "
        f"({s['contained_upstream_failure_rate_pct']}%)"
    )

    print(
        f"  authoritative events: "
        f"{s['authoritative_events']}"
    )

    print(
        f"  provider/reconciliation events: "
        f"{p.get('events', 0)}/"
        f"{r.get('events', 0)}"
    )

    print(
        f"  Twelve retrospective availability: "
        f"{p.get('retrospective_twelve_availability_pct')}%"
    )

    print(
        f"  direction disagreements: "
        f"{p.get('direction_disagreements', 0)}"
    )

    print(
        f"  >10 bps divergences: "
        f"{p.get('divergence_over_10bps', 0)}"
    )

    print(
        f"  M006e.2 integrity: "
        f"{'PASS' if i['all_m006e2_hashes_match'] else 'FAIL'}"
    )

    print(
        f"  safety: "
        f"{'PASS' if z['zero_recorded_safety_violations'] else 'FAIL'}"
    )

    print(
        f"  pending human review: "
        f"{s['pending_review_sessions']}"
    )


def write_outputs(
    ledger: dict[str, Any],
) -> None:

    LEDGER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        LEDGER_DIR
        / "m006e9b_cumulative_ledger.json"
    )

    csv_path = (
        LEDGER_DIR
        / "m006e9b_sessions.csv"
    )

    json_path.write_text(
        json.dumps(
            ledger,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    rows = ledger["sessions"]

    if rows:
        with csv_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(
                    rows[0].keys()
                ),
            )

            writer.writeheader()
            writer.writerows(rows)

    print(
        f"WROTE: {json_path}"
    )

    print(
        f"WROTE: {csv_path}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
    )

    args = parser.parse_args()

    ledger = build_ledger()

    print_summary(ledger)

    if args.write:
        write_outputs(ledger)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
