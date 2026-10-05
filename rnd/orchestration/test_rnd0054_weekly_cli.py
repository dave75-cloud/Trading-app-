import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "rnd" / "tools"
sys.path.insert(0, str(TOOLS))

from rnd0054_weekly_cli import LEDGER_VERSION, execute, recompute_ledger, _write_new, RND0054CLIError
from rnd0054_ledger import CANDIDATE_FINGERPRINT


SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


def record(start="2026-10-05T07:25:00Z", end="2026-10-05T07:35:00Z"):
    hashes = {}
    for i, symbol in enumerate(SYMBOLS):
        hashes[symbol] = {
            "raw_sha256": format(i + 1, "x") * 64,
            "canonical_sha256": format(i + 5, "x") * 64,
        }
    return {
        "candidate_id": "Q003",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "start_utc": start,
        "end_utc": end,
        "hashes": hashes,
        "integrity_pass": True,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def document():
    return {"contract_version": LEDGER_VERSION, "records": [record()]}


class TestRND0054WeeklyCLI(unittest.TestCase):
    def test_recompute_ignores_untrusted_stored_state(self):
        doc = document()
        doc["state"] = {"cumulative_end_utc": "2099-01-01T00:00:00Z"}
        _, state = recompute_ledger(doc)
        self.assertEqual(state["cumulative_end_utc"], "2026-10-05T07:35:00Z")

    def test_premature_run_never_reaches_acquisition(self):
        with patch("rnd0054_weekly_cli.acquire_window") as acquire:
            with self.assertRaises(RND0054CLIError):
                execute(document(), "2026-10-06T07:35:00Z", "/tmp/not-used")
        acquire.assert_not_called()

    def test_runnable_flow_calls_acquire_then_advances(self):
        advanced = {
            "records": [record(), record("2026-10-05T07:35:00Z", "2026-10-12T07:35:00Z")],
            "ledger_state": {
                "candidate_id": "Q003",
                "candidate_fingerprint": CANDIDATE_FINGERPRINT,
                "symbols": list(SYMBOLS),
                "tranche_count": 2,
                "cumulative_start_utc": "2026-10-05T07:25:00Z",
                "cumulative_end_utc": "2026-10-12T07:35:00Z",
                "state": "ACCUMULATING",
                "strategy_evaluation": False,
                "reserved_final_access": False,
                "broker_writes": False,
                "capital_authority": False,
                "automatic_promotion": False,
            },
        }
        with patch("rnd0054_weekly_cli.acquire_window", return_value=Path("/tmp/tranche")) as acquire:
            with patch("rnd0054_weekly_cli.verify_and_advance", return_value=advanced) as verify:
                out = execute(document(), "2026-10-12T07:35:00Z", "/tmp/tranche")
        acquire.assert_called_once()
        verify.assert_called_once()
        self.assertEqual(out["state"]["tranche_count"], 2)
        self.assertFalse(out["strategy_evaluation"])
        self.assertFalse(out["broker_writes"])

    def test_bad_contract_version_fails(self):
        doc = document()
        doc["contract_version"] = "wrong"
        with self.assertRaises(RND0054CLIError):
            recompute_ledger(doc)

    def test_new_ledger_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text("existing")
            with self.assertRaises(RND0054CLIError):
                _write_new(path, document())


if __name__ == "__main__":
    unittest.main()
