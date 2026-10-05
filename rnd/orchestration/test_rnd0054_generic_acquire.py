import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "rnd" / "tools"
sys.path.insert(0, str(TOOLS))

from rnd0054_generic_acquire import acquire_window, wall_clock_m5, RND0054AcquireError
from rnd0054_generic_verifier import verify_tranche


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _candle(ts, base="1.1000"):
    px = {"o": base, "h": "1.1010", "l": "1.0990", "c": "1.1005"}
    return {"time": ts, "complete": True, "bid": dict(px), "ask": dict(px), "mid": dict(px)}


def fake_fetcher(*, omit_index=None):
    def fetch(url, token):
        parsed = urlparse(url)
        instrument = parsed.path.split("/")[-2]
        q = parse_qs(parsed.query)
        start = datetime.fromisoformat(q["from"][0][:-1] + "+00:00")
        end = datetime.fromisoformat(q["to"][0][:-1] + "+00:00")
        candles = []
        cursor = start
        i = 0
        while cursor < end:
            if i != omit_index:
                candles.append(_candle(_z(cursor)))
            cursor += timedelta(minutes=5)
            i += 1
        raw = json.dumps({"instrument": instrument, "granularity": "M5", "candles": candles}).encode()
        return {"raw_bytes": raw, "request_id": "fixture-request"}
    return fetch


class TestRND0054GenericAcquire(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.TemporaryDirectory()
        self.out_parent = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.repo.cleanup()
        self.out_parent.cleanup()

    def target(self, name="tranche"):
        return Path(self.out_parent.name) / name

    def test_wall_clock_grid(self):
        values = wall_clock_m5("2026-10-05T07:35:00Z", "2026-10-05T07:55:00Z")
        self.assertEqual(len(values), 4)
        self.assertEqual(values[0], "2026-10-05T07:35:00Z")
        self.assertEqual(values[-1], "2026-10-05T07:50:00Z")

    def test_four_symbol_acquisition_seals_and_verifies(self):
        target = acquire_window(
            "2026-10-05T07:35:00Z",
            "2026-10-05T07:55:00Z",
            self.target(),
            self.repo.name,
            token="fixture-token",
            account_id="fixture_account",
            page_fetcher=fake_fetcher(),
        )
        self.assertTrue((target / "rnd0054_acquisition_receipt.json").is_file())
        out = verify_tranche(target, "2026-10-05T07:35:00Z", "2026-10-05T07:55:00Z")
        self.assertTrue(out["integrity_pass"])
        self.assertFalse(out["broker_writes"])

    def test_explicit_missing_slot_is_preserved_and_verifies(self):
        target = acquire_window(
            "2026-10-05T07:35:00Z",
            "2026-10-05T07:55:00Z",
            self.target("gap"),
            self.repo.name,
            token="fixture-token",
            account_id="fixture_account",
            page_fetcher=fake_fetcher(omit_index=1),
        )
        gap = json.loads((target / "AUDUSD" / "gap_ledger.json").read_text())
        self.assertEqual(gap["missing_timestamps"], ["2026-10-05T07:40:00Z"])
        self.assertFalse(gap["complete"])
        self.assertTrue(verify_tranche(target, "2026-10-05T07:35:00Z", "2026-10-05T07:55:00Z")["integrity_pass"])

    def test_missing_credentials_fail_closed(self):
        with self.assertRaises(RND0054AcquireError):
            acquire_window(
                "2026-10-05T07:35:00Z",
                "2026-10-05T07:55:00Z",
                self.target("creds"),
                self.repo.name,
                token="",
                account_id="",
                page_fetcher=fake_fetcher(),
            )

    def test_existing_target_cannot_be_overwritten(self):
        target = self.target("existing")
        target.mkdir()
        with self.assertRaises(Exception):
            acquire_window(
                "2026-10-05T07:35:00Z",
                "2026-10-05T07:55:00Z",
                target,
                self.repo.name,
                token="fixture-token",
                account_id="fixture_account",
                page_fetcher=fake_fetcher(),
            )


if __name__ == "__main__":
    unittest.main()
