#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from market_evidence_contract import ContractError, VERSION, validate_rows
from accepted_event_replay_adapter import ReplayError, adapt
from shadow_simulator import simulate


def entry():
    return {
        "contract_version": VERSION,
        "event_id": "entry-1",
        "leg": "entry",
        "pair": "USDJPY",
        "event_timestamp_utc": "2026-10-01T12:35:00+00:00",
        "price_timestamp_utc": "2026-10-01T12:35:01+00:00",
        "bid": 155.54,
        "ask": 155.56,
        "base_to_aud": 1.50,
        "source_provider": "local_fixture",
        "source_artifact": "fixture.json",
        "source_artifact_sha256": "a" * 64,
    }


def exit_row():
    r = entry()
    r.update({
        "event_id": "exit-1",
        "leg": "exit",
        "event_timestamp_utc": "2026-10-01T13:05:00+00:00",
        "price_timestamp_utc": "2026-10-01T13:05:01+00:00",
        "bid": 155.70,
        "ask": 155.72,
        "quote_to_aud": 0.00965,
    })
    r.pop("base_to_aud")
    return r


class MarketEvidenceContractTests(unittest.TestCase):

    def test_valid_entry_and_exit(self):
        r = validate_rows([entry(), exit_row()])
        self.assertEqual(r["records"], 2)
        self.assertEqual(r["unique_event_legs"], 2)
        self.assertFalse(r["network_capability"])
        self.assertFalse(r["automatic_promotion"])

    def test_duplicate_event_leg_fails(self):
        with self.assertRaises(ContractError):
            validate_rows([entry(), entry()])

    def test_crossed_market_fails(self):
        r = entry()
        r["bid"] = 155.60
        r["ask"] = 155.50
        with self.assertRaises(ContractError):
            validate_rows([r])

    def test_wrong_conversion_field_fails(self):
        r = entry()
        r["quote_to_aud"] = 0.01
        with self.assertRaises(ContractError):
            validate_rows([r])

    def test_non_utc_timestamp_fails(self):
        r = entry()
        r["price_timestamp_utc"] = "2026-10-01T22:35:00+10:00"
        with self.assertRaises(ContractError):
            validate_rows([r])

    def test_adapter_rejects_pair_mismatch(self):
        rows = [{
            "event_id": "entry-1",
            "bar_ts_utc": "2026-10-01T12:35:00+00:00",
            "pair": "USDJPY",
            "event_type": "entry",
            "old_position": "flat",
            "new_position": "long",
            "bridge_actions": [{
                "leg": "entry",
                "decision": "ALLOW_DRY_RUN_PROPOSAL",
                "approx_units": 70000,
            }],
            "blocked_entries": [],
        }]

        m = entry()
        m["pair"] = "AUDUSD"

        with self.assertRaises(ReplayError):
            adapt(rows, {("entry-1", "entry"): m})


    def test_full_contract_adapter_simulator_chain(self):
        market_rows = [entry(), exit_row()]
        validated = validate_rows(market_rows)

        self.assertEqual(validated["records"], 2)

        accepted_rows = [
            {
                "event_id": "entry-1",
                "bar_ts_utc": "2026-10-01T12:35:00+00:00",
                "pair": "USDJPY",
                "event_type": "entry",
                "old_position": "flat",
                "new_position": "long",
                "bridge_actions": [{
                    "leg": "entry",
                    "decision": "ALLOW_DRY_RUN_PROPOSAL",
                    "approx_units": 71174,
                }],
                "blocked_entries": [],
            },
            {
                "event_id": "exit-1",
                "bar_ts_utc": "2026-10-01T13:05:00+00:00",
                "pair": "USDJPY",
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

        market = {
            (r["event_id"], r["leg"]): r
            for r in market_rows
        }

        adapted = adapt(accepted_rows, market)

        self.assertEqual(
            adapted["summary"]["replay_events"],
            2,
        )

        result = simulate(
            adapted["replay_events"],
            initial_equity_aud=100000,
            slippage_bps=0,
        )

        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["open_positions"], {})
        self.assertFalse(result["network_capability"])
        self.assertFalse(result["submission_capability"])
        self.assertAlmostEqual(
            result["realized_pnl_aud"],
            96.156074,
            places=5,
        )


if __name__ == "__main__":
    unittest.main()
