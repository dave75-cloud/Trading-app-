#!/usr/bin/env python3

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_capture_sealer import CaptureError, CAPTURE_VERSION, seal
from market_evidence_contract import validate_rows


AUD_BID = 0.6500
AUD_ASK = 0.6502
AUD_MID = (AUD_BID + AUD_ASK) / 2.0

PRICES = {
    "AUDUSD": {"bid": AUD_BID, "ask": AUD_ASK},
    "EURUSD": {"bid": 1.1000, "ask": 1.1002},
    "GBPUSD": {"bid": 1.3000, "ask": 1.3002},
    "USDJPY": {"bid": 150.00, "ask": 150.02},
}


def make_snapshot(pair, leg):
    return {
        "capture_version": CAPTURE_VERSION,
        "event_id": f"synthetic-{pair.lower()}-{leg}",
        "leg": leg,
        "pair": pair,
        "event_timestamp_utc": "2026-10-01T12:35:00+00:00",
        "price_timestamp_utc": "2026-10-01T12:35:01+00:00",
        "source_provider": "synthetic_fixture",
        "prices": PRICES,
    }


def seal_snapshot(snapshot):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "snapshot.json"
        raw = (
            json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        p.write_bytes(raw)

        record = seal(p)

        return record, raw


class EvidenceCaptureSealerTests(unittest.TestCase):

    def test_audusd_entry_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("AUDUSD", "entry")
        )
        self.assertEqual(record["base_to_aud"], 1.0)

    def test_audusd_exit_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("AUDUSD", "exit")
        )
        self.assertAlmostEqual(
            record["quote_to_aud"],
            1.0 / AUD_MID,
            places=12,
        )

    def test_eurusd_entry_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("EURUSD", "entry")
        )
        eur_mid = (1.1000 + 1.1002) / 2.0
        self.assertAlmostEqual(
            record["base_to_aud"],
            eur_mid / AUD_MID,
            places=12,
        )

    def test_eurusd_exit_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("EURUSD", "exit")
        )
        self.assertAlmostEqual(
            record["quote_to_aud"],
            1.0 / AUD_MID,
            places=12,
        )

    def test_gbpusd_entry_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("GBPUSD", "entry")
        )
        gbp_mid = (1.3000 + 1.3002) / 2.0
        self.assertAlmostEqual(
            record["base_to_aud"],
            gbp_mid / AUD_MID,
            places=12,
        )

    def test_gbpusd_exit_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("GBPUSD", "exit")
        )
        self.assertAlmostEqual(
            record["quote_to_aud"],
            1.0 / AUD_MID,
            places=12,
        )

    def test_usdjpy_entry_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("USDJPY", "entry")
        )
        self.assertAlmostEqual(
            record["base_to_aud"],
            1.0 / AUD_MID,
            places=12,
        )

    def test_usdjpy_exit_conversion(self):
        record, _ = seal_snapshot(
            make_snapshot("USDJPY", "exit")
        )
        jpy_mid = (150.00 + 150.02) / 2.0
        self.assertAlmostEqual(
            record["quote_to_aud"],
            1.0 / (jpy_mid * AUD_MID),
            places=12,
        )

    def test_exact_target_bid_ask_preserved(self):
        record, _ = seal_snapshot(
            make_snapshot("USDJPY", "entry")
        )
        self.assertEqual(record["bid"], 150.00)
        self.assertEqual(record["ask"], 150.02)

    def test_source_hash_is_exact_snapshot_hash(self):
        record, raw = seal_snapshot(
            make_snapshot("EURUSD", "entry")
        )
        self.assertEqual(
            record["source_artifact_sha256"],
            hashlib.sha256(raw).hexdigest(),
        )

    def test_crossed_price_rejected(self):
        snapshot = make_snapshot("GBPUSD", "entry")
        snapshot["prices"] = dict(PRICES)
        snapshot["prices"]["GBPUSD"] = {
            "bid": 1.31,
            "ask": 1.30,
        }

        with self.assertRaises(CaptureError):
            seal_snapshot(snapshot)

    def test_missing_audusd_conversion_evidence_rejected(self):
        snapshot = make_snapshot("USDJPY", "exit")
        snapshot["prices"] = {
            "USDJPY": {"bid": 150.00, "ask": 150.02}
        }

        with self.assertRaises(CaptureError):
            seal_snapshot(snapshot)


    def test_sealed_record_roundtrip_passes_contract(self):
        snapshot = make_snapshot("USDJPY", "exit")
        record, raw = seal_snapshot(snapshot)

        encoded = json.dumps(record, sort_keys=True) + "\n"
        decoded = json.loads(encoded)

        summary = validate_rows([decoded])

        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["unique_event_legs"], 1)
        self.assertFalse(summary["network_capability"])
        self.assertFalse(summary["automatic_promotion"])

        self.assertEqual(
            decoded["source_artifact_sha256"],
            hashlib.sha256(raw).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
