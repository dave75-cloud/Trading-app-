#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from accepted_event_replay_adapter import (
    ReplayError,
    accepted_reconciliation_files,
    adapt,
    load_rows,
)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def clean_session(day, recon_name, events=2):
    return {
        "day": day,
        "events": {"authoritative_events": events},
        "integrity": {"m006e2_hash_match": True},
        "safety": {"zero_unexplained_write_indicators": True},
        "orchestration": {"verdict": "CLEAN"},
        "bridge": {
            "totals": {
                "order_payloads": 0,
                "write_requests": 0,
            }
        },
        "validation": {
            "totals": {
                "oanda_network_calls": 0,
                "order_payloads": 0,
                "write_requests": 0,
            }
        },
        "reconciliation": {
            "available": True,
            "events": events,
            "mode": "READ_ONLY_POST_SESSION_RECONCILIATION",
            "network_calls": 0,
            "order_capability": False,
            "source_file": recon_name,
            "summary": {"events": events},
        },
    }


def round_trip_rows():
    return [
        {
            "event_id": "entry-1",
            "bar_ts_utc": "2026-10-01T12:00:00+00:00",
            "pair": "AUDUSD",
            "event_type": "entry",
            "old_position": "flat",
            "new_position": "long",
            "bridge_actions": [{
                "leg": "entry",
                "decision": "ALLOW_DRY_RUN_PROPOSAL",
                "approx_units": 100000,
            }],
            "blocked_entries": [],
        },
        {
            "event_id": "exit-1",
            "bar_ts_utc": "2026-10-01T12:30:00+00:00",
            "pair": "AUDUSD",
            "event_type": "exit",
            "old_position": "long",
            "new_position": "flat",
            "bridge_actions": [{
                "leg": "exit",
                "decision": "ALLOW_RISK_REDUCING_EXIT",
                "approx_units": None,
            }],
            "blocked_entries": [],
        },
    ]


class ReplayAdapterTests(unittest.TestCase):

    def fixture(self, verdict="CLEAN", disposition=True, writes=0, recon_events=2):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)

        sessions = root / "sessions"
        recon = root / "reconciliation"
        dispositions = root / "dispositions"

        sessions.mkdir()
        recon.mkdir()
        dispositions.mkdir()

        day = "2026-10-01"
        rname = "recon.json"

        sess = clean_session(day, rname, events=2)
        sess["orchestration"]["verdict"] = verdict
        sess["bridge"]["totals"]["write_requests"] = writes

        write_json(sessions / "m006e9a_2026-10-01.json", sess)

        write_json(recon / rname, {
            "day": day,
            "summary": {"events": recon_events},
            "timeline": round_trip_rows()[:recon_events],
        })

        if disposition:
            write_json(dispositions / "session_disposition_2026-10-01.json", {
                "day": day,
                "accepted": True,
                "authoritative_events": 2,
                "reviewed_disposition": "ACCEPTED_WITH_CONTAINED_FAILURES",
                "integrity": {
                    "freeze_manifest_pass": True,
                    "m006e2_hash_match": True,
                    "trading_order_writes": 0,
                },
            })

        return td, sessions, recon, dispositions

    def test_clean_session_with_exact_market_evidence_replays(self):
        td, sessions, recon, dispositions = self.fixture()

        try:
            accepted = accepted_reconciliation_files(
                sessions, recon, dispositions
            )
            rows = load_rows(recon, accepted)

            market = {
                ("entry-1", "entry"): {
                    "bid": 0.6500,
                    "ask": 0.6502,
                    "base_to_aud": 1.0,
                },
                ("exit-1", "exit"): {
                    "bid": 0.6510,
                    "ask": 0.6512,
                    "quote_to_aud": 1.5,
                },
            }

            result = adapt(rows, market)

            self.assertEqual(result["summary"]["source_events"], 2)
            self.assertEqual(result["summary"]["source_legs"], 2)
            self.assertEqual(result["summary"]["replay_events"], 2)
            self.assertEqual(result["summary"]["suppressed_chains"], 0)

            replay = result["replay_events"]
            self.assertEqual(replay[0]["action"], "entry")
            self.assertEqual(replay[0]["units"], 100000)
            self.assertEqual(replay[1]["action"], "exit")

        finally:
            td.cleanup()

    def test_missing_market_evidence_suppresses_whole_chain(self):
        td, sessions, recon, dispositions = self.fixture()

        try:
            accepted = accepted_reconciliation_files(
                sessions, recon, dispositions
            )
            rows = load_rows(recon, accepted)

            result = adapt(rows, {})

            self.assertEqual(result["summary"]["replay_events"], 0)
            self.assertEqual(result["summary"]["suppressed_chains"], 1)

        finally:
            td.cleanup()

    def test_alert_without_disposition_fails_closed(self):
        td, sessions, recon, dispositions = self.fixture(
            verdict="ALERT",
            disposition=False,
        )

        try:
            with self.assertRaises(ReplayError):
                accepted_reconciliation_files(
                    sessions, recon, dispositions
                )
        finally:
            td.cleanup()

    def test_alert_with_operational_disposition_schema_is_accepted(self):
        td, sessions, recon, dispositions = self.fixture(
            verdict="ALERT",
            disposition=False,
        )

        try:
            write_json(dispositions / "session_disposition_2026-10-01.json", {
                "day": "2026-10-01",
                "reviewed_disposition": "ACCEPTED_WITH_CONTAINED_FAILURES",
                "accepted": True,
                "contained_upstream_failures": 1,
                "contained_local_concurrency_failures": 0,
                "raw_verdict": "ALERT",
                "review_basis": "Contained upstream failure; safety gates intact.",
                "human_reviewed": True,
                "automatic_promotion": False,
            })
            accepted = accepted_reconciliation_files(
                sessions, recon, dispositions
            )
            self.assertEqual(accepted, ["recon.json"])
        finally:
            td.cleanup()

    def test_nonzero_write_evidence_fails_closed(self):
        td, sessions, recon, dispositions = self.fixture(writes=1)

        try:
            with self.assertRaises(ReplayError):
                accepted_reconciliation_files(
                    sessions, recon, dispositions
                )
        finally:
            td.cleanup()

    def test_event_count_mismatch_fails_closed(self):
        td, sessions, recon, dispositions = self.fixture(recon_events=1)

        try:
            with self.assertRaises(ReplayError):
                accepted_reconciliation_files(
                    sessions, recon, dispositions
                )
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
