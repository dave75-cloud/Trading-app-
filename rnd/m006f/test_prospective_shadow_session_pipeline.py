#!/usr/bin/env python3

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prospective_shadow_session_pipeline import PipelineError, run_pipeline
from accepted_event_replay_adapter import ReplayError
from market_evidence_contract import ContractError, VERSION as MARKET_VERSION


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


class ProspectivePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.session = self.root / "m006e9a_2026-10-01.json"
        self.reconciliation = self.root / "recon.json"
        self.market = self.root / "market.jsonl"
        rows = [
            {
                "event_id": "usdjpy-entry", "bar_ts_utc": "2026-10-01T12:00:00+00:00",
                "pair": "USDJPY", "event_type": "entry", "new_position": "long",
                "bridge_actions": [{"leg": "entry", "decision": "ALLOW_DRY_RUN_PROPOSAL", "approx_units": 1000}],
                "blocked_entries": [],
            },
            {
                "event_id": "usdjpy-exit", "bar_ts_utc": "2026-10-01T12:30:00+00:00",
                "pair": "USDJPY", "event_type": "exit", "new_position": "flat",
                "bridge_actions": [{"leg": "exit", "decision": "ALLOW_RISK_REDUCING_EXIT", "approx_units": None}],
                "blocked_entries": [],
            },
        ]
        write_json(self.reconciliation, {"day": "2026-10-01", "summary": {"events": 2}, "timeline": rows})
        write_json(self.session, {
            "day": "2026-10-01", "events": {"authoritative_events": 2},
            "integrity": {"m006e2_hash_match": True},
            "safety": {"zero_unexplained_write_indicators": True},
            "orchestration": {"verdict": "CLEAN"},
            "bridge": {"totals": {"order_payloads": 0, "write_requests": 0}},
            "validation": {"totals": {"oanda_network_calls": 0, "order_payloads": 0, "write_requests": 0}},
            "reconciliation": {"available": True, "events": 2,
                "mode": "READ_ONLY_POST_SESSION_RECONCILIATION", "network_calls": 0,
                "order_capability": False, "source_file": "recon.json", "summary": {"events": 2}},
        })
        market_rows = [
            {"contract_version": MARKET_VERSION, "event_id": "usdjpy-entry", "leg": "entry",
             "pair": "USDJPY", "event_timestamp_utc": "2026-10-01T12:00:00+00:00",
             "price_timestamp_utc": "2026-10-01T12:00:01Z", "bid": 150.00, "ask": 150.02,
             "source_provider": "synthetic", "source_artifact": "fixture", "source_artifact_sha256": "a" * 64,
             "base_to_aud": 1.5, "quote_to_aud": None},
            {"contract_version": MARKET_VERSION, "event_id": "usdjpy-exit", "leg": "exit",
             "pair": "USDJPY", "event_timestamp_utc": "2026-10-01T12:30:00+00:00",
             "price_timestamp_utc": "2026-10-01T12:30:01Z", "bid": 150.12, "ask": 150.14,
             "source_provider": "synthetic", "source_artifact": "fixture", "source_artifact_sha256": "a" * 64,
             "base_to_aud": None, "quote_to_aud": 0.01},
        ]
        self.market.write_text("".join(json.dumps(row) + "\n" for row in market_rows))

    def tearDown(self):
        self.temp.cleanup()

    def run(self, result=None, output_name="output"):
        if result is not None:  # unittest invokes run(result)
            return super().run(result)
        return run_pipeline(session_id="prospective-2026-10-01", session_date_utc="2026-10-01",
                            accepted_session=self.session, reconciliation=self.reconciliation,
                            disposition=None, market_evidence=self.market,
                            output_dir=self.root / output_name)

    def test_successful_complete_offline_pipeline(self):
        manifest = self.run()
        output = self.root / "output"
        self.assertEqual(len(list(output.iterdir())), 7)
        self.assertEqual(manifest["market_evidence_validation"]["records"], 2)

    def test_known_synthetic_usdjpy_round_trip(self):
        self.run()
        result = json.loads((self.root / "output/shadow_result.json").read_text())
        self.assertEqual(result["event_count"], 2)
        self.assertAlmostEqual(result["realized_pnl_aud"], 1.0)
        self.assertEqual(result["open_positions"], {})

    def test_invalid_market_evidence_fails_before_simulation(self):
        self.market.write_text("{}\n")
        with self.assertRaises(ContractError):
            self.run()
        self.assertFalse((self.root / "output").exists())

    def test_missing_market_leg_fails_before_simulation(self):
        self.market.write_text(self.market.read_text().splitlines()[0] + "\n")
        with self.assertRaises(PipelineError):
            self.run()
        self.assertFalse((self.root / "output").exists())

    def test_source_integrity_failure_prevents_packaging(self):
        session = json.loads(self.session.read_text())
        session["integrity"]["m006e2_hash_match"] = False
        write_json(self.session, session)
        with self.assertRaises(ReplayError):
            self.run()
        self.assertFalse((self.root / "output").exists())

    def test_overwrite_refusal(self):
        self.run()
        with self.assertRaises(PipelineError):
            self.run()

    def test_output_hashes_are_deterministic(self):
        first = self.run(output_name="one")
        second = self.run(output_name="two")
        self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])

    def test_dossier_leaves_human_authority_unset(self):
        self.run()
        dossier = json.loads((self.root / "output/review_dossier.json").read_text())
        self.assertIsNone(dossier["review"]["human_disposition"])
        self.assertEqual(dossier["review"]["promotion_authority"], "NONE")
        self.assertFalse(dossier["safety"]["automatic_promotion"])

    def test_no_network_or_submission_capability(self):
        manifest = self.run()
        self.assertFalse(manifest["safety"]["network_capability"])
        self.assertFalse(manifest["safety"]["submission_capability"])
        self.assertFalse(manifest["safety"]["broker_transport"])
        self.assertFalse(manifest["safety"]["automatic_disposition"])


if __name__ == "__main__":
    unittest.main()
