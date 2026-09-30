#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shadow_observation_monitor import (
    MonitorError,
    build_monitor,
)
from shadow_session_ledger import VERSION as LEDGER_VERSION
from shadow_session_packager import canonical_hash


def make_session(
    number,
    disposition="ACCEPTED",
    replay_events=2,
    market_records=2,
    suppressed_chains=0,
    final_positions=None,
    flags=None,
):
    if final_positions is None:
        final_positions = {}

    if flags is None:
        flags = []

    return {
        "session_id": f"session-{number:03d}",
        "session_date_utc": f"2026-10-{number:02d}",
        "dossier_content_sha256": f"{number:064x}"[-64:],
        "disposition_content_sha256": f"{number + 1000:064x}"[-64:],
        "disposition": disposition,
        "reviewer_label": "human-reviewer",
        "reviewed_at_utc": f"2026-10-{number:02d}T15:00:00Z",
        "machine_status": (
            "CLEAN" if not flags else "REVIEW_REQUIRED"
        ),
        "review_flags": list(flags),
        "market_evidence_records": market_records,
        "replay_events": replay_events,
        "suppressed_chains": suppressed_chains,
        "final_positions": final_positions,
        "realized_pnl_aud": float(number),
        "final_equity_aud": 100000.0 + float(number),
    }


def make_ledger(sessions):
    dispositions = Counter(
        s["disposition"] for s in sessions
    )

    flags = Counter(
        flag
        for session in sessions
        for flag in session["review_flags"]
    )

    payload = {
        "ledger_version": LEDGER_VERSION,
        "reviewed_cohort_only": True,
        "sessions": sessions,
        "summary": {
            "reviewed_sessions": len(sessions),
            "accepted_sessions":
                dispositions["ACCEPTED"],
            "accepted_with_review_sessions":
                dispositions["ACCEPTED_WITH_REVIEW"],
            "rejected_sessions":
                dispositions["REJECTED"],
            "replay_events": sum(
                s["replay_events"] for s in sessions
            ),
            "market_evidence_records": sum(
                s["market_evidence_records"]
                for s in sessions
            ),
            "suppressed_chains": sum(
                s["suppressed_chains"]
                for s in sessions
            ),
            "sessions_with_open_positions": sum(
                1 for s in sessions
                if s["final_positions"]
            ),
            "review_flag_counts":
                dict(sorted(flags.items())),
            "total_realized_pnl_aud": sum(
                s["realized_pnl_aud"]
                for s in sessions
            ),
            "final_equity_observations_aud": [
                s["final_equity_aud"]
                for s in sessions
            ],
        },
        "integrity": {
            "all_sessions_have_verified_human_disposition": True,
            "duplicate_session_ids": False,
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_disposition": False,
            "automatic_promotion": False,
            "promotion_authority": "NONE",
        },
    }

    payload["ledger_content_sha256"] = canonical_hash(
        payload
    )

    return payload


def write_ledger(root, ledger):
    path = root / "ledger.json"
    path.write_text(
        json.dumps(
            ledger,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return path


def rehash(ledger):
    ledger = dict(ledger)
    ledger.pop("ledger_content_sha256", None)
    ledger["ledger_content_sha256"] = canonical_hash(
        ledger
    )
    return ledger


class ShadowObservationMonitorTests(unittest.TestCase):

    def test_current_one_session_two_event_progress(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = make_ledger([
                make_session(
                    1,
                    replay_events=2,
                    market_records=2,
                )
            ])

            path = write_ledger(Path(td), ledger)
            monitor = build_monitor(path)

            t = monitor["threshold_evidence"]

            self.assertEqual(
                t["observed_accepted_sessions"], 1
            )
            self.assertEqual(
                t["observed_accepted_replay_events"], 2
            )
            self.assertFalse(
                t["accepted_session_threshold_met"]
            )
            self.assertFalse(
                t["accepted_replay_event_threshold_met"]
            )
            self.assertFalse(
                t["both_numerical_thresholds_met"]
            )
            self.assertEqual(
                monitor["observation_phase"],
                "ACCUMULATING_EVIDENCE",
            )

    def test_exact_25_sessions_100_events_crosses_thresholds(self):
        with tempfile.TemporaryDirectory() as td:
            sessions = [
                make_session(
                    n,
                    replay_events=4,
                    market_records=4,
                )
                for n in range(1, 26)
            ]

            ledger = make_ledger(sessions)
            path = write_ledger(Path(td), ledger)

            monitor = build_monitor(path)
            t = monitor["threshold_evidence"]

            self.assertEqual(
                t["observed_accepted_sessions"], 25
            )
            self.assertEqual(
                t["observed_accepted_replay_events"], 100
            )
            self.assertTrue(
                t["both_numerical_thresholds_met"]
            )
            self.assertEqual(
                monitor["observation_phase"],
                "MINIMUM_NUMERICAL_EVIDENCE_RECORDED",
            )
            self.assertFalse(
                monitor["authority"]["automatic_promotion"]
            )
            self.assertEqual(
                monitor["authority"]["promotion_authority"],
                "NONE",
            )

    def test_rejected_session_excluded_from_accepted_progress(self):
        with tempfile.TemporaryDirectory() as td:
            sessions = [
                make_session(
                    1,
                    disposition="ACCEPTED",
                    replay_events=3,
                ),
                make_session(
                    2,
                    disposition="REJECTED",
                    replay_events=50,
                ),
            ]

            ledger = make_ledger(sessions)
            path = write_ledger(Path(td), ledger)

            monitor = build_monitor(path)

            self.assertEqual(
                monitor["reviewed_cohort"][
                    "reviewed_sessions"
                ],
                2,
            )
            self.assertEqual(
                monitor["reviewed_cohort"][
                    "accepted_sessions"
                ],
                1,
            )
            self.assertEqual(
                monitor["accepted_evidence"][
                    "replay_events"
                ],
                3,
            )

    def test_accepted_with_review_counts_as_accepted_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            sessions = [
                make_session(
                    1,
                    disposition="ACCEPTED_WITH_REVIEW",
                    replay_events=5,
                    flags=["SUPPRESSED_CHAINS_PRESENT"],
                    suppressed_chains=1,
                )
            ]

            ledger = make_ledger(sessions)
            path = write_ledger(Path(td), ledger)

            monitor = build_monitor(path)

            self.assertEqual(
                monitor["reviewed_cohort"][
                    "accepted_sessions"
                ],
                1,
            )
            self.assertEqual(
                monitor["accepted_evidence"][
                    "replay_events"
                ],
                5,
            )
            self.assertEqual(
                monitor["accepted_evidence"][
                    "suppressed_chains"
                ],
                1,
            )
            self.assertEqual(
                monitor["accepted_evidence"][
                    "review_flag_counts"
                ],
                {"SUPPRESSED_CHAINS_PRESENT": 1},
            )

    def test_open_position_and_flags_reported_as_quality_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            sessions = [
                make_session(
                    1,
                    final_positions={
                        "USDJPY": {
                            "side": "long",
                            "units": 1000,
                        }
                    },
                    flags=["OPEN_POSITIONS_AT_SESSION_END"],
                )
            ]

            ledger = make_ledger(sessions)
            path = write_ledger(Path(td), ledger)

            monitor = build_monitor(path)
            q = monitor["evidence_quality"]

            self.assertEqual(
                q[
                    "accepted_sessions_with_open_positions"
                ],
                1,
            )
            self.assertFalse(
                q["all_accepted_sessions_end_flat"]
            )
            self.assertEqual(
                q["accepted_review_flag_counts"],
                {"OPEN_POSITIONS_AT_SESSION_END": 1},
            )

    def test_tampered_ledger_hash_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = make_ledger([
                make_session(1)
            ])

            ledger["sessions"][0]["replay_events"] = 999

            path = write_ledger(Path(td), ledger)

            with self.assertRaises(MonitorError):
                build_monitor(path)

    def test_summary_inconsistency_rejected_even_if_rehashed(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = make_ledger([
                make_session(1)
            ])

            ledger["summary"]["reviewed_sessions"] = 99
            ledger = rehash(ledger)

            path = write_ledger(Path(td), ledger)

            with self.assertRaises(MonitorError):
                build_monitor(path)

    def test_duplicate_session_ids_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a = make_session(1)
            b = make_session(2)
            b["session_id"] = a["session_id"]

            ledger = make_ledger([a, b])
            path = write_ledger(Path(td), ledger)

            with self.assertRaises(MonitorError):
                build_monitor(path)

    def test_safety_authority_violation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = make_ledger([
                make_session(1)
            ])

            ledger["safety"]["automatic_promotion"] = True
            ledger = rehash(ledger)

            path = write_ledger(Path(td), ledger)

            with self.assertRaises(MonitorError):
                build_monitor(path)

    def test_monitor_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = make_ledger([
                make_session(1)
            ])

            path = write_ledger(Path(td), ledger)

            a = build_monitor(path)
            b = build_monitor(path)

            self.assertEqual(
                a["monitor_content_sha256"],
                b["monitor_content_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
