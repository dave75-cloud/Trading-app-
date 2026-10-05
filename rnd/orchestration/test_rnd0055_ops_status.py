import unittest

from rnd0055_ops_status import assess_operations
from rnd0054_ledger import CANDIDATE_FINGERPRINT


def _record(start="2026-10-05T07:25:00Z", end="2026-10-05T07:35:00Z"):
    hashes = {}
    for i, symbol in enumerate(("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")):
        hashes[symbol] = {
            "raw_sha256": format(i + 1, "x") * 64,
            "canonical_sha256": format(i + 5, "x") * 64,
        }
    return {
        "candidate_id": "Q003",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"],
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


def _doc():
    return {"contract_version": "RND-0054-prospective-ledger-v0.1", "records": [_record()]}


class TestRND0055OpsStatus(unittest.TestCase):
    def test_waits_before_window_close(self):
        out = assess_operations(_doc(), "2026-10-10T07:35:00Z")
        self.assertFalse(out["runnable"])
        self.assertEqual(out["recovery_action"], "WAIT_FOR_WINDOW_CLOSE")

    def test_ready_at_window_close(self):
        out = assess_operations(_doc(), "2026-10-12T07:35:00Z")
        self.assertTrue(out["runnable"])
        self.assertEqual(out["recovery_action"], "READY_FOR_GET_ONLY_ACQUISITION")

    def test_partial_stage_blocks_run(self):
        out = assess_operations(_doc(), "2026-10-12T07:35:00Z", stage_target_exists=True)
        self.assertFalse(out["runnable"])
        self.assertEqual(out["recovery_action"], "ABANDON_PARTIAL_STAGE_DO_NOT_ADVANCE_LEDGER")

    def test_existing_sealed_target_requires_review(self):
        out = assess_operations(_doc(), "2026-10-12T07:35:00Z", sealed_target_exists=True)
        self.assertFalse(out["runnable"])
        self.assertEqual(out["recovery_action"], "HUMAN_REVIEW_EXISTING_SEALED_TARGET")

    def test_authority_bits_remain_false(self):
        out = assess_operations(_doc(), "2026-10-12T07:35:00Z")
        self.assertFalse(out["strategy_evaluation"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])

    def test_recomputes_records(self):
        out = assess_operations(_doc(), "2026-10-12T07:35:00Z")
        self.assertEqual(out["records_checked"], 1)
        self.assertEqual(out["cumulative_end_utc"], "2026-10-05T07:35:00Z")


if __name__ == "__main__":
    unittest.main()
