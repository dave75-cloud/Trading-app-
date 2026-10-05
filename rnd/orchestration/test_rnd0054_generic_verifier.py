import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from historical_data_reconstruction import canonical_rows_sha256
from rnd0054_generic_verifier import verify_tranche, RND0054VerifyError
from rnd0054_ledger import CANDIDATE_FINGERPRINT, SYMBOLS

START = "2026-10-05T07:35:00Z"
END = "2026-10-05T07:45:00Z"
TIMES = ["2026-10-05T07:35:00.000000000Z", "2026-10-05T07:40:00.000000000Z"]


def _write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def build_tranche(root):
    root = Path(root)
    receipt = {
        "task_id": "RND-0047",
        "candidate_id": "Q003",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "acquisition_window": {"start_utc": START, "end_utc": END, "human_approved": True},
        "symbols": list(SYMBOLS),
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "manifests": {},
    }
    _write(root / "rnd0047_acquisition_receipt.json", receipt)

    for symbol in SYMBOLS:
        sdir = root / symbol
        sdir.mkdir()
        rows = [
            {"timestamp_utc": TIMES[0], "complete": True, "symbol": symbol},
            {"timestamp_utc": TIMES[1], "complete": True, "symbol": symbol},
        ]
        raw = (symbol + "-raw-fixture").encode()
        (sdir / "raw_bundle.bin").write_bytes(raw)
        canonical_sha = canonical_rows_sha256(rows)
        raw_sha = hashlib.sha256(raw).hexdigest()
        manifest = {
            "symbol": symbol,
            "provider": "OANDA",
            "timeframe": "M5",
            "price_components": ["bid", "ask", "mid"],
            "start_utc": START,
            "end_utc": END,
            "complete": True,
            "complete_candles_only": True,
            "immutable": True,
            "row_count": 2,
            "canonical_rows_sha256": canonical_sha,
            "sha256": raw_sha,
        }
        gap = {
            "expected_count": 2,
            "actual_count": 2,
            "missing_timestamps": [],
            "unexpected_timestamps": [],
            "complete": True,
        }
        _write(sdir / "canonical_rows.json", rows)
        _write(sdir / "snapshot_manifest.json", manifest)
        _write(sdir / "gap_ledger.json", gap)
    return root


class TestRND0054GenericVerifier(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = build_tranche(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_fixture_passes_and_emits_ledger_record(self):
        out = verify_tranche(self.root, START, END)
        self.assertTrue(out["integrity_pass"])
        self.assertEqual(out["start_utc"], START)
        self.assertEqual(out["end_utc"], END)
        self.assertEqual(set(out["hashes"]), set(SYMBOLS))
        self.assertFalse(out["strategy_evaluation"])
        self.assertFalse(out["broker_writes"])

    def test_candidate_drift_fails(self):
        p = self.root / "rnd0047_acquisition_receipt.json"
        receipt = json.loads(p.read_text())
        receipt["candidate_fingerprint"] = "0" * 64
        _write(p, receipt)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_authority_drift_fails(self):
        p = self.root / "rnd0047_acquisition_receipt.json"
        receipt = json.loads(p.read_text())
        receipt["broker_writes"] = True
        _write(p, receipt)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_wrong_window_fails(self):
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, "2026-10-05T07:30:00Z", END)

    def test_timestamp_tamper_fails(self):
        p = self.root / "AUDUSD" / "canonical_rows.json"
        rows = json.loads(p.read_text())
        rows[1]["timestamp_utc"] = "2026-10-05T07:45:00.000000000Z"
        _write(p, rows)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_raw_hash_tamper_fails(self):
        p = self.root / "EURUSD" / "raw_bundle.bin"
        p.write_bytes(b"tampered")
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_canonical_hash_tamper_fails(self):
        p = self.root / "GBPUSD" / "snapshot_manifest.json"
        manifest = json.loads(p.read_text())
        manifest["canonical_rows_sha256"] = "0" * 64
        _write(p, manifest)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_gap_ledger_missing_timestamp_fails(self):
        p = self.root / "USDJPY" / "gap_ledger.json"
        gap = json.loads(p.read_text())
        gap["missing_timestamps"] = ["2026-10-05T07:40:00Z"]
        gap["complete"] = False
        _write(p, gap)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)


if __name__ == "__main__":
    unittest.main()
