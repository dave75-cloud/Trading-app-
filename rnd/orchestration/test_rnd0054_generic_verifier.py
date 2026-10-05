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


def candle(ts):
    return {
        "timestamp_utc": ts,
        "complete": True,
        "bid_open": "1.1000",
        "bid_high": "1.1010",
        "bid_low": "1.0990",
        "bid_close": "1.1005",
        "ask_open": "1.1002",
        "ask_high": "1.1012",
        "ask_low": "1.0992",
        "ask_close": "1.1007",
        "mid_open": "1.1001",
        "mid_high": "1.1011",
        "mid_low": "1.0991",
        "mid_close": "1.1006",
    }


def _seal_symbol(root, symbol, rows, missing):
    sdir = Path(root) / symbol
    sdir.mkdir(exist_ok=True)
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
        "row_count": len(rows),
        "canonical_rows_sha256": canonical_sha,
        "sha256": raw_sha,
    }
    gap = {
        "expected_count": 2,
        "actual_count": len(rows),
        "missing_timestamps": missing,
        "unexpected_timestamps": [],
        "complete": len(missing) == 0,
    }
    _write(sdir / "canonical_rows.json", rows)
    _write(sdir / "snapshot_manifest.json", manifest)
    _write(sdir / "gap_ledger.json", gap)


def build_tranche(root):
    root = Path(root)
    receipt = {
        "task_id": "RND-0054",
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
    _write(root / "rnd0054_acquisition_receipt.json", receipt)
    for symbol in SYMBOLS:
        _seal_symbol(root, symbol, [candle(TIMES[0]), candle(TIMES[1])], [])
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

    def test_explicit_market_gap_is_preserved_and_accepted(self):
        for symbol in SYMBOLS:
            sdir = self.root / symbol
            for name in ("canonical_rows.json", "snapshot_manifest.json", "gap_ledger.json", "raw_bundle.bin"):
                (sdir / name).unlink()
            sdir.rmdir()
            _seal_symbol(self.root, symbol, [candle(TIMES[0])], ["2026-10-05T07:40:00Z"])
        out = verify_tranche(self.root, START, END)
        self.assertTrue(out["integrity_pass"])

    def test_candidate_drift_fails(self):
        p = self.root / "rnd0054_acquisition_receipt.json"
        receipt = json.loads(p.read_text())
        receipt["candidate_fingerprint"] = "0" * 64
        _write(p, receipt)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)

    def test_authority_drift_fails(self):
        p = self.root / "rnd0054_acquisition_receipt.json"
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

    def test_gap_ledger_mismatch_fails(self):
        sdir = self.root / "USDJPY"
        rows = [candle(TIMES[0])]
        _write(sdir / "canonical_rows.json", rows)
        manifest = json.loads((sdir / "snapshot_manifest.json").read_text())
        manifest["row_count"] = 1
        manifest["canonical_rows_sha256"] = canonical_rows_sha256(rows)
        _write(sdir / "snapshot_manifest.json", manifest)
        gap = json.loads((sdir / "gap_ledger.json").read_text())
        gap["actual_count"] = 1
        gap["complete"] = False
        gap["missing_timestamps"] = []
        _write(sdir / "gap_ledger.json", gap)
        with self.assertRaises(RND0054VerifyError):
            verify_tranche(self.root, START, END)


if __name__ == "__main__":
    unittest.main()
