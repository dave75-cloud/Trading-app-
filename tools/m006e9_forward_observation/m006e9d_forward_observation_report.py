#!/usr/bin/env python3

"""
M006e.9d — Forward-Observation Report Generator

Produces a human-readable report from the cumulative ledger and
graduation monitor.

No network access.
No broker access.
No execution capability.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


VERSION = "M006e.9d-v1.0"

HERE = Path(__file__).resolve().parent

ROOT = Path(
    "data/research_runs/M006E_FORWARD_OBSERVATION"
)

REPORT_DIR = ROOT / "reports"

LEDGER_MODULE = (
    HERE / "m006e9b_cumulative_ledger.py"
)

MONITOR_MODULE = (
    HERE / "m006e9c_graduation_monitor.py"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    module = importlib.util.module_from_spec(
        spec
    )

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module


def fmt(value, digits=2):
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def build_report() -> str:
    ledger_module = load_module(
        "m006e9b",
        LEDGER_MODULE,
    )

    monitor_module = load_module(
        "m006e9c",
        MONITOR_MODULE,
    )

    ledger = ledger_module.build_ledger()
    monitor = monitor_module.evaluate()

    sessions = ledger["sessions"]
    s = ledger["summary"]
    p = ledger["provider_path"]
    r = ledger["reconciliation"]
    i = ledger["integrity"]
    z = ledger["safety"]

    criteria = monitor["criteria"]
    progress = monitor["progress"]

    if sessions:
        first_day = sessions[0]["day"]
        last_day = sessions[-1]["day"]
    else:
        first_day = "N/A"
        last_day = "N/A"

    lines = []

    lines.append(
        "# M006e Forward-Observation Report"
    )
    lines.append("")
    lines.append(
        f"Generator: {VERSION}"
    )
    lines.append("")
    lines.append(
        f"Observation period: {first_day} to {last_day}"
    )
    lines.append("")
    lines.append(
        f"Current graduation status: **{monitor['overall_status']}**"
    )
    lines.append("")

    lines.append("## 1. Executive Summary")
    lines.append("")

    lines.append(
        f"- Accepted sessions: "
        f"{s['accepted_sessions']} / "
        f"{criteria['accepted_sessions']['required']}"
    )

    lines.append(
        f"- Authoritative OANDA events: "
        f"{s['authoritative_events']} / "
        f"{criteria['authoritative_events']['required']}"
    )

    lines.append(
        f"- Session-progress threshold: "
        f"{progress['session_progress_pct']}%"
    )

    lines.append(
        f"- Event-progress threshold: "
        f"{progress['event_progress_pct']}%"
    )

    lines.append(
        f"- Observed cycles: "
        f"{s['observed_cycles']} / "
        f"{s['expected_cycles']}"
    )

    lines.append(
        f"- Cumulative coverage: "
        f"{fmt(s['cumulative_coverage_pct'])}%"
    )

    lines.append(
        f"- PASS / FAIL / SKIP / UNKNOWN: "
        f"{s['pass_cycles']} / "
        f"{s['fail_cycles']} / "
        f"{s['skip_cycles']} / "
        f"{s['unknown_cycles']}"
    )

    lines.append(
        f"- Contained upstream failures: "
        f"{s['contained_upstream_failures']} "
        f"({fmt(s['contained_upstream_failure_rate_pct'], 3)}%)"
    )

    lines.append("")

    lines.append("## 2. Safety and Integrity")
    lines.append("")

    lines.append(
        f"- Frozen M006e.2 integrity: "
        f"{'PASS' if i['all_m006e2_hashes_match'] else 'FAIL'}"
    )

    lines.append(
        f"- Recorded safety violations: "
        f"{'0' if z['zero_recorded_safety_violations'] else 'PRESENT'}"
    )

    lines.append(
        f"- Pending human session reviews: "
        f"{s['pending_review_sessions']}"
    )

    lines.append(
        "- Automatic promotion capability: NONE"
    )

    lines.append("")

    lines.append("## 3. Operational Reliability")
    lines.append("")

    lines.append(
        f"- Cumulative cycle coverage: "
        f"{fmt(s['cumulative_coverage_pct'])}%"
    )

    lines.append(
        f"- Contained upstream-failure rate: "
        f"{fmt(s['contained_upstream_failure_rate_pct'], 3)}%"
    )

    lines.append(
        f"- Current infrastructure classification: "
        f"{criteria['contained_upstream_failure_rate']['status']}"
    )

    lines.append("")

    lines.append("## 4. Provider-Path Evidence")
    lines.append("")

    lines.append(
        f"- Provider-path events: "
        f"{p.get('events', 0)}"
    )

    lines.append(
        f"- Retrospective Twelve availability: "
        f"{fmt(p.get('retrospective_twelve_availability_pct'), 3)}%"
    )

    lines.append(
        f"- Missing Twelve bars: "
        f"{p.get('missing_twelve_bars', 0)}"
    )

    lines.append(
        f"- Direction disagreements: "
        f"{p.get('direction_disagreements', 0)}"
    )

    lines.append(
        f"- Volatility-eligibility disagreements: "
        f"{p.get('volatility_eligibility_disagreements', 0)}"
    )

    lines.append(
        f"- >10 bps price divergences: "
        f"{p.get('divergence_over_10bps', 0)}"
    )

    lines.append(
        f"- Maximum observed absolute close divergence: "
        f"{fmt(p.get('max_abs_close_divergence_bps'), 4)} bps"
    )

    lines.append("")

    lines.append("## 5. Reconciliation")
    lines.append("")

    lines.append(
        f"- Reconciliation events: "
        f"{r.get('events', 0)}"
    )

    lines.append(
        f"- Provider event-count mismatch sessions: "
        f"{r.get('provider_event_count_mismatches', 0)}"
    )

    lines.append(
        f"- Reconciliation event-count mismatch sessions: "
        f"{r.get('reconciliation_event_count_mismatches', 0)}"
    )

    lines.append("")

    lines.append("## 6. Session Ledger")
    lines.append("")

    lines.append(
        "| Date | Reviewed disposition | Raw | "
        "Observed | PASS | FAIL | Events | Safety |"
    )

    lines.append(
        "|---|---|---:|---:|---:|---:|---:|---:|"
    )

    for row in sessions:
        lines.append(
            f"| {row['day']} "
            f"| {row['reviewed_disposition']} "
            f"| {row['raw_verdict']} "
            f"| {row['observed_cycles']} "
            f"| {row['pass_cycles']} "
            f"| {row['fail_cycles']} "
            f"| {row['authoritative_events']} "
            f"| {row['safety_violations']} |"
        )

    lines.append("")

    lines.append("## 7. Graduation Assessment")
    lines.append("")

    lines.append(
        f"Current status: **{monitor['overall_status']}**"
    )

    lines.append("")

    lines.append(
        f"- Sessions: "
        f"{criteria['accepted_sessions']['current']} / "
        f"{criteria['accepted_sessions']['required']}"
    )

    lines.append(
        f"- Events: "
        f"{criteria['authoritative_events']['current']} / "
        f"{criteria['authoritative_events']['required']}"
    )

    lines.append(
        f"- Hard gates: "
        f"{'PASS' if not monitor['hard_gate_failures'] else 'BLOCKED'}"
    )

    if monitor["hard_gate_failures"]:
        for item in monitor[
            "hard_gate_failures"
        ]:
            lines.append(
                f"  - {item}"
            )

    lines.append(
        f"- Review flags: "
        f"{len(monitor['review_flags'])}"
    )

    if monitor["review_flags"]:
        for item in monitor[
            "review_flags"
        ]:
            lines.append(
                f"  - {item}"
            )

    lines.append("")

    lines.append("## 8. Current Interpretation")
    lines.append("")

    lines.append(
        "The forward-observation program remains in evidence-gathering mode. "
        "The minimum graduation sample has not yet been reached."
    )

    lines.append("")

    if (
        s["authoritative_events"] > 0
        and p.get("events", 0)
        == s["authoritative_events"]
        and r.get("events", 0)
        == s["authoritative_events"]
    ):
        lines.append(
            "All authoritative events accumulated so far are represented "
            "in both provider-path and reconciliation evidence."
        )
        lines.append("")

    lines.append(
        "No conclusion regarding strategy profitability should be drawn "
        "from the current sample."
    )

    lines.append("")

    lines.append(
        "M006e remains frozen. No strategy repair, optimisation, "
        "parameter change, or execution promotion is authorised by "
        "this report."
    )

    lines.append("")

    lines.append("## 9. Next Evidence Requirement")
    lines.append("")

    lines.append(
        "Continue frozen forward observation until BOTH minimum "
        "requirements are met:"
    )

    lines.append("")

    lines.append(
        f"1. At least {criteria['accepted_sessions']['required']} "
        "accepted sessions."
    )

    lines.append(
        f"2. At least {criteria['authoritative_events']['required']} "
        "authoritative OANDA events."
    )

    lines.append("")

    lines.append(
        "The longer requirement governs. Meeting these numbers does "
        "not itself promote the system; it only permits formal review."
    )

    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
    )

    args = parser.parse_args()

    report = build_report()

    print(report)

    if args.write:
        REPORT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            REPORT_DIR
            / "M006e_Forward_Observation_Report.md"
        )

        path.write_text(
            report,
            encoding="utf-8",
        )

        print()
        print(
            f"WROTE: {path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
