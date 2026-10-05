import unittest

from rnd0050_weekly_planner import plan_next, RND0050PlannerError, CANDIDATE_FINGERPRINT


def ledger(**overrides):
    base = {
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "verified_end_utc": "2026-10-05T07:35:00Z",
        "next_tranche_number": 2,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
    base.update(overrides)
    return base


class TestRND0050Planner(unittest.TestCase):
    def test_not_yet_runnable(self):
        out = plan_next(ledger(), "2026-10-06T07:35:00Z")
        self.assertEqual(out["status"], "NOT_YET_RUNNABLE")
        self.assertEqual(out["window"]["start_utc"], "2026-10-05T07:35:00Z")
        self.assertEqual(out["window"]["end_utc"], "2026-10-12T07:35:00Z")

    def test_runnable_at_end(self):
        out = plan_next(ledger(), "2026-10-12T07:35:00Z")
        self.assertEqual(out["status"], "RUNNABLE")
        self.assertEqual(out["tranche_number"], 2)

    def test_contiguous_next_week(self):
        out = plan_next(ledger(verified_end_utc="2026-10-12T07:35:00Z", next_tranche_number=3), "2026-10-19T07:35:00Z")
        self.assertEqual(out["window"], {"start_utc": "2026-10-12T07:35:00Z", "end_utc": "2026-10-19T07:35:00Z"})

    def test_final_window_clips_to_boundary(self):
        out = plan_next(ledger(verified_end_utc="2027-03-29T07:35:00Z", next_tranche_number=27), "2027-04-03T07:25:00Z")
        self.assertEqual(out["status"], "RUNNABLE")
        self.assertEqual(out["window"]["end_utc"], "2027-04-03T07:25:00Z")

    def test_complete_at_boundary(self):
        out = plan_next(ledger(verified_end_utc="2027-04-03T07:25:00Z", next_tranche_number=28), "2027-04-03T07:25:00Z")
        self.assertEqual(out, {"status": "ACCUMULATION_COMPLETE", "window": None})

    def test_fingerprint_drift_fails(self):
        with self.assertRaises(RND0050PlannerError):
            plan_next(ledger(candidate_fingerprint="0" * 64), "2026-10-12T07:35:00Z")

    def test_broker_authority_fails(self):
        with self.assertRaises(RND0050PlannerError):
            plan_next(ledger(broker_writes=True), "2026-10-12T07:35:00Z")

    def test_strategy_evaluation_fails(self):
        with self.assertRaises(RND0050PlannerError):
            plan_next(ledger(strategy_evaluation=True), "2026-10-12T07:35:00Z")

    def test_non_m5_now_fails(self):
        with self.assertRaises(RND0050PlannerError):
            plan_next(ledger(), "2026-10-12T07:36:00Z")


if __name__ == "__main__":
    unittest.main()
