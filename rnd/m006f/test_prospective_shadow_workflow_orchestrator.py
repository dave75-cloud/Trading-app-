#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from market_evidence_contract import VERSION as MARKET_VERSION
from prospective_shadow_workflow_orchestrator import (
    NoEligibleSession,
    WorkflowError,
    discover_candidates,
    run_workflow,
)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


class ProspectiveShadowWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sessions = self.root / "sessions"
        self.reconciliation = self.root / "reconciliation"
        self.dispositions = self.root / "dispositions"
        self.market = self.root / "market"
        self.outputs = self.root / "outputs"
        for path in (
            self.sessions,
            self.reconciliation,
            self.dispositions,
            self.market,
            self.outputs,
        ):
            path.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def make_fixture(self, day="2026-10-01", verdict="CLEAN",
                     with_market=True, with_disposition=True):
        recon_name = f"recon_{day}.json"
        session_path = self.sessions / f"m006e9a_{day}.json"
        recon_path = self.reconciliation / recon_name

        entry_id = f"{day}-entry"
        exit_id = f"{day}-exit"
        rows = [
            {
                "event_id": entry_id,
                "bar_ts_utc": f"{day}T12:00:00+00:00",
                "pair": "USDJPY",
                "event_type": "entry",
                "new_position": "long",
                "bridge_actions": [{
                    "leg": "entry",
                    "decision": "ALLOW_DRY_RUN_PROPOSAL",
                    "approx_units": 1000,
                }],
                "blocked_entries": [],
            },
            {
                "event_id": exit_id,
                "bar_ts_utc": f"{day}T12:30:00+00:00",
                "pair": "USDJPY",
                "event_type": "exit",
                "new_position": "flat",
                "bridge_actions": [{
                    "leg": "exit",
                    "decision": "ALLOW_RISK_REDUCING_EXIT",
                    "approx_units": None,
                }],
                "blocked_entries": [],
            },
        ]

        write_json(recon_path, {
            "day": day,
            "summary": {"events": 2},
            "timeline": rows,
        })
        write_json(session_path, {
            "day": day,
            "events": {"authoritative_events": 2},
            "integrity": {"m006e2_hash_match": True},
            "safety": {"zero_unexplained_write_indicators": True},
            "orchestration": {"verdict": verdict},
            "bridge": {"totals": {"order_payloads": 0, "write_requests": 0}},
            "validation": {"totals": {
                "oanda_network_calls": 0,
                "order_payloads": 0,
                "write_requests": 0,
            }},
            "reconciliation": {
                "available": True,
                "events": 2,
                "mode": "READ_ONLY_POST_SESSION_RECONCILIATION",
                "network_calls": 0,
                "order_capability": False,
                "source_file": recon_name,
                "summary": {"events": 2},
            },
        })

        market_path = self.market / f"market_evidence_{day}.jsonl"
        if with_market:
            market_rows = [
                {
                    "contract_version": MARKET_VERSION,
                    "event_id": entry_id,
                    "leg": "entry",
                    "pair": "USDJPY",
                    "event_timestamp_utc": f"{day}T12:00:00+00:00",
                    "price_timestamp_utc": f"{day}T12:00:01Z",
                    "bid": 150.00,
                    "ask": 150.02,
                    "source_provider": "synthetic",
                    "source_artifact": "fixture",
                    "source_artifact_sha256": "a" * 64,
                    "base_to_aud": 1.5,
                    "quote_to_aud": None,
                },
                {
                    "contract_version": MARKET_VERSION,
                    "event_id": exit_id,
                    "leg": "exit",
                    "pair": "USDJPY",
                    "event_timestamp_utc": f"{day}T12:30:00+00:00",
                    "price_timestamp_utc": f"{day}T12:30:01Z",
                    "bid": 150.12,
                    "ask": 150.14,
                    "source_provider": "synthetic",
                    "source_artifact": "fixture",
                    "source_artifact_sha256": "a" * 64,
                    "base_to_aud": None,
                    "quote_to_aud": 0.01,
                },
            ]
            market_path.write_text(
                "".join(json.dumps(row) + "\n" for row in market_rows)
            )

        disposition_path = self.dispositions / f"session_disposition_{day}.json"
        if verdict != "CLEAN" and with_disposition:
            write_json(disposition_path, {
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

        return {
            "session": session_path,
            "reconciliation": recon_path,
            "market": market_path,
            "disposition": disposition_path,
        }

    def kwargs(self, session_date_utc=None):
        return {
            "accepted_session_root": self.sessions,
            "reconciliation_root": self.reconciliation,
            "disposition_root": self.dispositions,
            "market_evidence_root": self.market,
            "output_root": self.outputs,
            "session_date_utc": session_date_utc,
        }

    def test_exactly_one_eligible_session_runs_pipeline(self):
        self.make_fixture()
        result = run_workflow(**self.kwargs())
        self.assertEqual(result["selected_day"], "2026-10-01")
        self.assertTrue(
            (self.outputs / "shadow_session_2026-10-01/review_dossier.json").is_file()
        )

    def test_zero_eligible_sessions_publishes_nothing(self):
        with self.assertRaises(NoEligibleSession):
            run_workflow(**self.kwargs())
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_ambiguous_eligible_sessions_fail_closed(self):
        self.make_fixture("2026-10-01")
        self.make_fixture("2026-10-02")
        with self.assertRaisesRegex(WorkflowError, "ambiguous eligible sessions"):
            run_workflow(**self.kwargs())
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_explicit_date_selects_only_requested_session(self):
        self.make_fixture("2026-10-01")
        self.make_fixture("2026-10-02")
        result = run_workflow(**self.kwargs("2026-10-02"))
        self.assertEqual(result["selected_day"], "2026-10-02")
        self.assertFalse((self.outputs / "shadow_session_2026-10-01").exists())
        self.assertTrue((self.outputs / "shadow_session_2026-10-02").exists())

    def test_existing_output_is_refused_for_explicit_date(self):
        self.make_fixture()
        (self.outputs / "shadow_session_2026-10-01").mkdir()
        with self.assertRaisesRegex(WorkflowError, "refusing overwrite"):
            run_workflow(**self.kwargs("2026-10-01"))

    def test_missing_exact_market_evidence_publishes_nothing(self):
        self.make_fixture(with_market=False)
        with self.assertRaisesRegex(NoEligibleSession, "market evidence"):
            run_workflow(**self.kwargs("2026-10-01"))
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_non_clean_source_requires_existing_human_disposition(self):
        self.make_fixture(verdict="ALERT", with_disposition=False)
        with self.assertRaisesRegex(NoEligibleSession, "required disposition"):
            run_workflow(**self.kwargs("2026-10-01"))
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_source_reconciliation_day_mismatch_publishes_nothing(self):
        paths = self.make_fixture()
        recon = json.loads(paths["reconciliation"].read_text())
        recon["day"] = "2026-10-02"
        write_json(paths["reconciliation"], recon)
        with self.assertRaisesRegex(NoEligibleSession, "reconciliation day mismatch"):
            run_workflow(**self.kwargs("2026-10-01"))
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_produced_dossier_leaves_human_disposition_unset(self):
        self.make_fixture()
        run_workflow(**self.kwargs())
        dossier = json.loads(
            (self.outputs / "shadow_session_2026-10-01/review_dossier.json").read_text()
        )
        self.assertIsNone(dossier["review"]["human_disposition"])
        self.assertEqual(dossier["review"]["promotion_authority"], "NONE")

    def test_workflow_declares_no_network_submission_or_promotion_authority(self):
        self.make_fixture()
        result = run_workflow(**self.kwargs())
        safety = result["safety"]
        self.assertFalse(safety["network_capability"])
        self.assertFalse(safety["submission_capability"])
        self.assertFalse(safety["automatic_disposition"])
        self.assertFalse(safety["automatic_promotion"])
        self.assertEqual(safety["promotion_authority"], "NONE")

    def test_candidate_discovery_is_deterministic(self):
        self.make_fixture("2026-10-02")
        self.make_fixture("2026-10-01")
        roots = self.kwargs()
        roots.pop("session_date_utc")
        first = discover_candidates(**roots)
        second = discover_candidates(**roots)
        self.assertEqual(first, second)
        self.assertEqual([x["day"] for x in first], ["2026-10-01", "2026-10-02"])

    def test_non_clean_source_with_accepted_disposition_can_run(self):
        self.make_fixture(verdict="ALERT", with_disposition=True)
        result = run_workflow(**self.kwargs())
        self.assertEqual(result["selected_day"], "2026-10-01")
        self.assertTrue((self.outputs / "shadow_session_2026-10-01").is_dir())


if __name__ == "__main__":
    unittest.main()
