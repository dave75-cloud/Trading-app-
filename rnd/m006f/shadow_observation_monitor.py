#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from shadow_session_packager import canonical_hash
from shadow_session_ledger import VERSION as LEDGER_VERSION


VERSION = "M006f-shadow-observation-monitor-v0.1"

MIN_ACCEPTED_SESSIONS = 25
MIN_ACCEPTED_REPLAY_EVENTS = 100

ACCEPTED_DISPOSITIONS = {
    "ACCEPTED",
    "ACCEPTED_WITH_REVIEW",
}

ALL_DISPOSITIONS = ACCEPTED_DISPOSITIONS | {
    "REJECTED",
}


class MonitorError(ValueError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def nonnegative_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise MonitorError(
            f"{name} must be a non-negative integer"
        )

    if value < 0:
        raise MonitorError(
            f"{name} must be a non-negative integer"
        )

    return value


def finite_number(value, name):
    if isinstance(value, bool):
        raise MonitorError(f"{name} must be numeric")

    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise MonitorError(
            f"{name} must be numeric"
        ) from exc

    if not math.isfinite(x):
        raise MonitorError(
            f"{name} must be finite"
        )

    return x


def load_verified_ledger(path):
    path = Path(path)

    if not path.exists() or not path.is_file():
        raise MonitorError(
            "ledger file does not exist"
        )

    raw = path.read_bytes()

    try:
        ledger = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise MonitorError(
            "ledger is invalid JSON"
        ) from exc

    if not isinstance(ledger, dict):
        raise MonitorError(
            "ledger must be a JSON object"
        )

    if ledger.get("ledger_version") != LEDGER_VERSION:
        raise MonitorError(
            "unsupported ledger version"
        )

    recorded_hash = ledger.get(
        "ledger_content_sha256"
    )

    if not isinstance(recorded_hash, str):
        raise MonitorError(
            "missing ledger_content_sha256"
        )

    payload = dict(ledger)
    payload.pop("ledger_content_sha256", None)

    if recorded_hash != canonical_hash(payload):
        raise MonitorError(
            "ledger-content SHA-256 mismatch"
        )

    if ledger.get("reviewed_cohort_only") is not True:
        raise MonitorError(
            "ledger must contain reviewed cohort only"
        )

    integrity = ledger.get("integrity")
    safety = ledger.get("safety")
    summary = ledger.get("summary")
    sessions = ledger.get("sessions")

    if not isinstance(integrity, dict):
        raise MonitorError(
            "ledger integrity block missing"
        )

    if (
        integrity.get(
            "all_sessions_have_verified_human_disposition"
        )
        is not True
    ):
        raise MonitorError(
            "ledger human-disposition integrity failed"
        )

    if integrity.get("duplicate_session_ids") is not False:
        raise MonitorError(
            "ledger reports duplicate session IDs"
        )

    if not isinstance(safety, dict):
        raise MonitorError(
            "ledger safety block missing"
        )

    expected_safety = {
        "network_capability": False,
        "submission_capability": False,
        "automatic_disposition": False,
        "automatic_promotion": False,
        "promotion_authority": "NONE",
    }

    for key, expected in expected_safety.items():
        if safety.get(key) != expected:
            raise MonitorError(
                f"ledger safety mismatch: {key}"
            )

    if not isinstance(summary, dict):
        raise MonitorError(
            "ledger summary missing"
        )

    if not isinstance(sessions, list) or not sessions:
        raise MonitorError(
            "ledger sessions must be a non-empty list"
        )

    seen = set()
    disposition_counts = Counter()
    flag_counts = Counter()

    replay_events = 0
    market_records = 0
    suppressed_chains = 0
    open_position_sessions = 0
    total_pnl = 0.0
    final_equities = []

    for index, session in enumerate(sessions):
        if not isinstance(session, dict):
            raise MonitorError(
                f"session {index}: expected object"
            )

        session_id = session.get("session_id")

        if not isinstance(session_id, str) or not session_id:
            raise MonitorError(
                f"session {index}: invalid session_id"
            )

        if session_id in seen:
            raise MonitorError(
                "duplicate session_id in ledger"
            )

        seen.add(session_id)

        disposition = session.get("disposition")

        if disposition not in ALL_DISPOSITIONS:
            raise MonitorError(
                f"session {session_id}: invalid disposition"
            )

        disposition_counts[disposition] += 1

        replay = nonnegative_int(
            session.get("replay_events"),
            f"{session_id}.replay_events",
        )

        market = nonnegative_int(
            session.get("market_evidence_records"),
            f"{session_id}.market_evidence_records",
        )

        suppressed = nonnegative_int(
            session.get("suppressed_chains"),
            f"{session_id}.suppressed_chains",
        )

        positions = session.get("final_positions")

        if not isinstance(positions, dict):
            raise MonitorError(
                f"{session_id}.final_positions must be an object"
            )

        flags = session.get("review_flags")

        if not isinstance(flags, list):
            raise MonitorError(
                f"{session_id}.review_flags must be a list"
            )

        for flag in flags:
            if not isinstance(flag, str) or not flag:
                raise MonitorError(
                    f"{session_id}: invalid review flag"
                )
            flag_counts[flag] += 1

        pnl = finite_number(
            session.get("realized_pnl_aud"),
            f"{session_id}.realized_pnl_aud",
        )

        equity = finite_number(
            session.get("final_equity_aud"),
            f"{session_id}.final_equity_aud",
        )

        replay_events += replay
        market_records += market
        suppressed_chains += suppressed
        total_pnl += pnl
        final_equities.append(equity)

        if positions:
            open_position_sessions += 1

    expected_summary = {
        "reviewed_sessions": len(sessions),
        "accepted_sessions":
            disposition_counts["ACCEPTED"],
        "accepted_with_review_sessions":
            disposition_counts["ACCEPTED_WITH_REVIEW"],
        "rejected_sessions":
            disposition_counts["REJECTED"],
        "replay_events": replay_events,
        "market_evidence_records": market_records,
        "suppressed_chains": suppressed_chains,
        "sessions_with_open_positions":
            open_position_sessions,
        "review_flag_counts":
            dict(sorted(flag_counts.items())),
        "final_equity_observations_aud":
            final_equities,
    }

    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise MonitorError(
                f"ledger summary mismatch: {key}"
            )

    reported_pnl = finite_number(
        summary.get("total_realized_pnl_aud"),
        "summary.total_realized_pnl_aud",
    )

    if not math.isclose(
        reported_pnl,
        total_pnl,
        rel_tol=1e-12,
        abs_tol=1e-9,
    ):
        raise MonitorError(
            "ledger summary mismatch: total_realized_pnl_aud"
        )

    return ledger, raw


def build_monitor(ledger_path):
    ledger, ledger_raw = load_verified_ledger(
        ledger_path
    )

    accepted = [
        session
        for session in ledger["sessions"]
        if session["disposition"] in ACCEPTED_DISPOSITIONS
    ]

    accepted_sessions = len(accepted)

    accepted_replay_events = sum(
        int(s["replay_events"])
        for s in accepted
    )

    accepted_market_records = sum(
        int(s["market_evidence_records"])
        for s in accepted
    )

    accepted_suppressed = sum(
        int(s["suppressed_chains"])
        for s in accepted
    )

    accepted_open_positions = sum(
        1 for s in accepted
        if s["final_positions"]
    )

    accepted_flags = Counter(
        flag
        for session in accepted
        for flag in session["review_flags"]
    )

    sessions_met = (
        accepted_sessions >= MIN_ACCEPTED_SESSIONS
    )

    events_met = (
        accepted_replay_events
        >= MIN_ACCEPTED_REPLAY_EVENTS
    )

    phase = (
        "MINIMUM_NUMERICAL_EVIDENCE_RECORDED"
        if sessions_met and events_met
        else "ACCUMULATING_EVIDENCE"
    )

    monitor = {
        "monitor_version": VERSION,
        "source": {
            "ledger_version": ledger["ledger_version"],
            "ledger_content_sha256":
                ledger["ledger_content_sha256"],
            "ledger_file_sha256":
                sha256_bytes(ledger_raw),
        },
        "reviewed_cohort": {
            "reviewed_sessions":
                ledger["summary"]["reviewed_sessions"],
            "accepted_sessions":
                accepted_sessions,
            "rejected_sessions":
                ledger["summary"]["rejected_sessions"],
        },
        "accepted_evidence": {
            "replay_events":
                accepted_replay_events,
            "market_evidence_records":
                accepted_market_records,
            "suppressed_chains":
                accepted_suppressed,
            "sessions_with_open_positions":
                accepted_open_positions,
            "review_flag_counts":
                dict(sorted(accepted_flags.items())),
        },
        "threshold_evidence": {
            "required_accepted_sessions":
                MIN_ACCEPTED_SESSIONS,
            "observed_accepted_sessions":
                accepted_sessions,
            "accepted_session_threshold_met":
                sessions_met,
            "required_accepted_replay_events":
                MIN_ACCEPTED_REPLAY_EVENTS,
            "observed_accepted_replay_events":
                accepted_replay_events,
            "accepted_replay_event_threshold_met":
                events_met,
            "both_numerical_thresholds_met":
                sessions_met and events_met,
        },
        "evidence_quality": {
            "accepted_suppressed_chains":
                accepted_suppressed,
            "accepted_sessions_with_open_positions":
                accepted_open_positions,
            "accepted_review_flag_counts":
                dict(sorted(accepted_flags.items())),
            "zero_accepted_suppressed_chains":
                accepted_suppressed == 0,
            "all_accepted_sessions_end_flat":
                accepted_open_positions == 0,
        },
        "observation_phase": phase,
        "authority": {
            "automatic_disposition": False,
            "automatic_promotion": False,
            "promotion_authority": "NONE",
            "human_promotion_decision_required": True,
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
        },
    }

    monitor["monitor_content_sha256"] = canonical_hash(
        monitor
    )

    return monitor


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--ledger",
        required=True,
    )
    ap.add_argument(
        "--output",
        required=True,
    )

    args = ap.parse_args()

    output = Path(args.output)

    if output.exists():
        raise MonitorError(
            "output already exists; refusing overwrite"
        )

    monitor = build_monitor(args.ledger)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            monitor,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    thresholds = monitor["threshold_evidence"]

    print("M006F_SHADOW_OBSERVATION_MONITOR: PASS")
    print(
        "observation_phase="
        + monitor["observation_phase"]
    )
    print(
        "accepted_sessions="
        + str(thresholds["observed_accepted_sessions"])
        + "/"
        + str(thresholds["required_accepted_sessions"])
    )
    print(
        "accepted_replay_events="
        + str(
            thresholds["observed_accepted_replay_events"]
        )
        + "/"
        + str(
            thresholds["required_accepted_replay_events"]
        )
    )
    print(
        "both_numerical_thresholds_met="
        + str(
            thresholds["both_numerical_thresholds_met"]
        ).upper()
    )
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")
    print("human_promotion_decision_required=TRUE")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")


if __name__ == "__main__":
    main()
