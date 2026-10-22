#!/usr/bin/env python3
"""Synthetic-only tests; no live evidence, prices or broker access."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rnd0074_development_metadata_audit import AuditError, summarize, validate_timestamp_strings

def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")

class MetadataAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.shard = Path(self.tmp.name) / "EURUSD" / "2019"
        self.shard.mkdir(parents=True)
        schedule = ["2019-01-07T21:55:00Z", "2019-01-07T22:05:00Z", "2019-01-07T22:10:00Z"]
        ledger = {"expected_count": 3, "actual_count": 3, "missing_count": 1,
                  "unexpected_count": 1, "missing_timestamps": ["2019-01-07T22:10:00Z"],
                  "unexpected_timestamps": ["2019-01-07T22:00:00Z"],
                  "resolved": False, "seal_allowed": False}
        write_json(self.shard / "standard_schedule.json", schedule)
        write_json(self.shard / "discrepancy_ledger.json", ledger)
        (self.shard / "canonical_rows.json").write_text("CANARY: DO NOT PARSE")
        (self.shard / "raw_bundle.bin").write_bytes(b"RAW NO PARSE")
        write_json(self.shard / "page_evidence.json", [])
        m = {"symbol": "EURUSD", "year": 2019, "provider": "OANDA",
             "environment": "PRACTICE", "timeframe": "M5",
             "price_components": ["bid", "ask", "mid"], "complete_candles_only": True,
             "seal_allowed": False, "status": "QUARANTINED_UNRESOLVED_DISCREPANCIES",
             "seal_block_reason": "UNRESOLVED_CALENDAR_DISCREPANCIES",
             "start_utc": "2019-01-01T00:00:00Z", "end_utc": "2020-01-01T00:00:00Z",
             "row_count": 3, "missing_count": 1, "unexpected_count": 1,
             "expected_standard_session_count": 3}
        hashes = {"raw_bundle_file_sha256": "raw_bundle.bin",
                  "canonical_rows_file_sha256": "canonical_rows.json",
                  "page_evidence_file_sha256": "page_evidence.json",
                  "standard_schedule_file_sha256": "standard_schedule.json",
                  "discrepancy_ledger_file_sha256": "discrepancy_ledger.json"}
        for key, name in hashes.items():
            m[key] = hashlib.sha256((self.shard / name).read_bytes()).hexdigest()
        write_json(self.shard / "quarantine_manifest.json", m)

    def test_valid_metadata_only(self):
        result = summarize(self.shard, "EURUSD", 2019)
        self.assertEqual(1, result["unexpected_at_1700_ny"])
        self.assertEqual(1, result["short_bars"])
        self.assertFalse(result["admitted"])

    def test_hash_tamper_fails_closed(self):
        (self.shard / "canonical_rows.json").write_text("CHANGED")
        with self.assertRaisesRegex(AuditError, "SHA-256 mismatch"):
            summarize(self.shard, "EURUSD", 2019)

    def test_missing_wrong_membership_fails(self):
        p = self.shard / "discrepancy_ledger.json"
        ledger = json.loads(p.read_text())
        ledger["missing_timestamps"] = ["2019-01-07T22:15:00Z"]
        write_json(p, ledger)
        manifest_path = self.shard / "quarantine_manifest.json"
        m = json.loads(manifest_path.read_text())
        m["discrepancy_ledger_file_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        write_json(manifest_path, m)
        with self.assertRaisesRegex(AuditError, "membership mismatch"):
            summarize(self.shard, "EURUSD", 2019)

    def test_duplicate_timestamps_rejected(self):
        with self.assertRaisesRegex(AuditError, "unique ordered"):
            validate_timestamp_strings(["2019-01-01T00:00:00Z"] * 2, "test", 2019)

    def test_wrong_year_rejected(self):
        with self.assertRaisesRegex(AuditError, "outside year"):
            validate_timestamp_strings(["2021-01-01T00:00:00Z"], "test", 2019)

    def test_quarantine_cannot_be_overridden(self):
        path = self.shard / "quarantine_manifest.json"
        m = json.loads(path.read_text())
        m["seal_allowed"] = True
        write_json(path, m)
        with self.assertRaisesRegex(AuditError, "identity/quarantine mismatch"):
            summarize(self.shard, "EURUSD", 2019)

    def test_symlink_canonical_rejected(self):
        path = self.shard / "canonical_rows.json"
        outside = Path(self.tmp.name) / "target"
        outside.write_text("TARGET")
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(AuditError, "unsafe or missing"):
            summarize(self.shard, "EURUSD", 2019)

if __name__ == "__main__":
    unittest.main()
