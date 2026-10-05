import unittest
from unittest.mock import patch

from rnd0054_weekly_workflow import plan_next, verify_and_advance, RND0054WorkflowError
from rnd0054_ledger import CANDIDATE_FINGERPRINT


BASE_STATE = {
    "candidate_fingerprint": CANDIDATE_FINGERPRINT,
    "cumulative_end_utc": "2026-10-05T07:35:00Z",
    "strategy_evaluation": False,
    "reserved_final_access": False,
    "broker_writes": False,
    "capital_authority": False,
    "automatic_promotion": False,
}


def state(**overrides):
    out = dict(BASE_STATE)
    out.update(overrides)
    return out


def record(start="2026-10-05T07:25:00Z", end="2026-10-05T07:35:00Z", fill="a"):
    hashes = {}
    canonical_fill = ("e", "f", "a", "b")
    for i, symbol in enumerate(("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")):
        raw = (fill + str(i))[:1] * 64
        can = canonical_fill[i] * 64
        hashes[symbol] = {"raw_sha256": raw, "canonical_sha256": can}
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


class TestRND0054WeeklyWorkflow(unittest.TestCase):
    def test_not_yet_runnable(self):
        out = plan_next(state(), "2026-10-06T07:35:00Z")
        self.assertEqual(out["status"], "NOT_YET_RUNNABLE")
        self.assertEqual(out["window"]["end_utc"], "2026-10-12T07:35:00Z")

    def test_runnable_at_exact_end(self):
        out = plan_next(state(), "2026-10-12T07:35:00Z")
        self.assertEqual(out["status"], "RUNNABLE")

    def test_final_window_clips_exactly(self):
        out = plan_next(state(cumulative_end_utc="2027-03-29T07:35:00Z"), "2027-04-03T07:25:00Z")
        self.assertEqual(out["window"]["end_utc"], "2027-04-03T07:25:00Z")
        self.assertEqual(out["status"], "RUNNABLE")

    def test_complete_at_boundary(self):
        out = plan_next(state(cumulative_end_utc="2027-04-03T07:25:00Z"), "2027-04-03T07:25:00Z")
        self.assertEqual(out, {"status": "ACCUMULATION_COMPLETE", "window": None})

    def test_authority_drift_fails(self):
        with self.assertRaises(RND0054WorkflowError):
            plan_next(state(broker_writes=True), "2026-10-12T07:35:00Z")

    def test_fingerprint_drift_fails(self):
        with self.assertRaises(RND0054WorkflowError):
            plan_next(state(candidate_fingerprint="0" * 64), "2026-10-12T07:35:00Z")

    def test_verify_failure_does_not_advance(self):
        existing = [record()]
        with patch("rnd0054_weekly_workflow.verify_tranche", side_effect=ValueError("bad tranche")):
            with self.assertRaises(ValueError):
                verify_and_advance(existing, "/tmp/does-not-matter", "2026-10-05T07:35:00Z", "2026-10-12T07:35:00Z")
        self.assertEqual(len(existing), 1)

    def test_verified_tranche_advances_contiguously(self):
        first = record()
        second = record("2026-10-05T07:35:00Z", "2026-10-12T07:35:00Z", fill="b")
        with patch("rnd0054_weekly_workflow.verify_tranche", return_value=second):
            out = verify_and_advance([first], "/tmp/does-not-matter", second["start_utc"], second["end_utc"])
        self.assertEqual(out["ledger_state"]["cumulative_end_utc"], "2026-10-12T07:35:00Z")
        self.assertEqual(len(out["records"]), 2)
        self.assertFalse(out["broker_writes"])

    def test_noncontiguous_verified_record_still_fails_full_audit(self):
        first = record()
        bad = record("2026-10-05T07:40:00Z", "2026-10-12T07:40:00Z", fill="c")
        with patch("rnd0054_weekly_workflow.verify_tranche", return_value=bad):
            with self.assertRaises(Exception):
                verify_and_advance([first], "/tmp/does-not-matter", bad["start_utc"], bad["end_utc"])


if __name__ == "__main__":
    unittest.main()
