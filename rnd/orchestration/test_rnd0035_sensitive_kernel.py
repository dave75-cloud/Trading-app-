#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import unittest

from rnd0035_sensitive_kernel import reconstruct_sensitive_pair
from rnd0035_trial_dispatch import run_declared_trial_pair


def rows(count, start="2019-01-02T07:00:00Z", gap_after=None):
    dt = datetime.fromisoformat(start[:-1] + "+00:00")
    price = 1.0
    out = []
    for i in range(count):
        if gap_after is not None and i == gap_after:
            dt += timedelta(minutes=10)
        price *= 1.0015 if i % 2 == 0 else 1.0002
        spread = price * 0.0001
        out.append({
            "timestamp_utc": dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": f"{price - spread / 2:.9f}",
            "ask_close": f"{price + spread / 2:.9f}",
            "mid_close": f"{price:.9f}",
        })
        dt += timedelta(minutes=5)
    return out


class RND0035SensitiveKernelTests(unittest.TestCase):
    def test_all_sensitive_trials_are_executable_on_synthetic_rows(self):
        fixture = rows(420, gap_after=56)
        for trial_id in ("E001", "E002", "F001", "F002", "F003", "F004"):
            with self.subTest(trial_id=trial_id):
                result = reconstruct_sensitive_pair(trial_id, "AUDUSD", fixture)
                self.assertEqual(trial_id, result["trial_id"])
                self.assertEqual(420, result["row_count"])
                self.assertFalse(result["authority"]["broker_writes"])
                self.assertFalse(result["authority"]["validation_open"])
                self.assertFalse(result["authority"]["final_test_open"])

    def test_e_trials_observe_real_gap_without_synthetic_price(self):
        fixture = rows(420, gap_after=56)
        for trial_id in ("E001", "E002"):
            result = reconstruct_sensitive_pair(trial_id, "AUDUSD", fixture)
            self.assertEqual(1, result["gap_count"])
            self.assertEqual(420, len(result["marks"]))
            self.assertTrue(any(not mark["entry_eligible"] for mark in result["marks"]))

    def test_f001_creates_and_resolves_pending_entries(self):
        result = reconstruct_sensitive_pair("F001", "AUDUSD", rows(120))
        created = [x for x in result["events"] if x["event_type"] == "PENDING_ENTRY_CREATED"]
        resolved = [x for x in result["events"] if x["event_type"] == "PENDING_ENTRY_RESOLVED"]
        self.assertGreater(len(created), 0)
        self.assertGreater(len(resolved), 0)

    def test_f002_creates_delayed_exit(self):
        result = reconstruct_sensitive_pair("F002", "AUDUSD", rows(160))
        created = [x for x in result["events"] if x["event_type"] == "PENDING_EXIT_CREATED"]
        executed = [x for x in result["events"] if x["event_type"] == "PENDING_EXIT_EXECUTED"]
        self.assertGreater(len(created), 0)
        self.assertGreater(len(executed), 0)

    def test_unified_dispatch_routes_sensitive_and_reference(self):
        fixture = rows(100)
        sensitive = run_declared_trial_pair("F004", "AUDUSD", fixture)
        reference = run_declared_trial_pair("R000", "AUDUSD", fixture)
        self.assertEqual("F004", sensitive["trial_id"])
        self.assertNotIn("trial_id", reference)


if __name__ == "__main__":
    unittest.main()
