#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import unittest

from rnd0035_sensitive_semantics import (
    CompleteSessionCooldown,
    HundredBarCooldown,
    PendingEntry,
    PendingExit,
    reversal_action,
)

UTC = timezone.utc


def dt(hour, minute=0, day=2):
    return datetime(2019, 1, day, hour, minute, tzinfo=UTC)


class RND0035SensitiveSemanticsTests(unittest.TestCase):
    def test_e002_bar_100_still_suppressed_bar_101_eligible(self):
        state = HundredBarCooldown()
        state.on_gap()
        start = dt(8)
        for i in range(100):
            self.assertFalse(state.observe(start + timedelta(minutes=5 * i)))
        self.assertTrue(state.observe(start + timedelta(minutes=500)))

    def test_e002_gap_resets_contiguous_count(self):
        state = HundredBarCooldown()
        state.on_gap()
        start = dt(8)
        for i in range(50):
            self.assertFalse(state.observe(start + timedelta(minutes=5 * i)))
        # Ten-minute discontinuity resets count; this observation becomes bar 1.
        self.assertFalse(state.observe(start + timedelta(minutes=5 * 51)))
        self.assertEqual(1, state.contiguous_count)

    def test_e001_full_aud_session_qualifies_but_not_last_in_session_bar(self):
        state = CompleteSessionCooldown(11, 14)
        state.on_gap()
        current = dt(11)
        for i in range(36):
            self.assertFalse(state.observe(current + timedelta(minutes=5 * i)))
        self.assertTrue(state.session_completed)
        self.assertFalse(state.suppressed is False)
        # First genuine observation after session restores eligibility.
        self.assertTrue(state.observe(dt(14)))
        self.assertFalse(state.suppressed)

    def test_e001_mid_session_start_does_not_qualify(self):
        state = CompleteSessionCooldown(11, 13)
        state.on_gap()
        current = dt(11, 30)
        for i in range(18):
            self.assertFalse(state.observe(current + timedelta(minutes=5 * i)))
        self.assertFalse(state.session_completed)

    def test_e001_discontinuity_invalidates_candidate_session(self):
        state = CompleteSessionCooldown(11, 13)
        state.on_gap()
        current = dt(11)
        for i in range(6):
            self.assertFalse(state.observe(current + timedelta(minutes=5 * i)))
        self.assertFalse(state.observe(dt(11, 35)))
        self.assertEqual(0, state.candidate_count)
        self.assertFalse(state.session_completed)

    def test_f001_executes_only_on_next_contiguous_observation(self):
        pending = PendingEntry(1, dt(11))
        self.assertEqual("EXECUTE", pending.resolve(dt(11, 5), 1))
        self.assertEqual("CANCEL_GAP_OR_NONCONTIGUOUS", pending.resolve(dt(11, 10), 1))

    def test_f001_contradiction_cancels_stale_entry(self):
        pending = PendingEntry(1, dt(11))
        self.assertEqual("CANCEL_CONTRADICTED", pending.resolve(dt(11, 5), 0))
        self.assertEqual("CANCEL_CONTRADICTED", pending.resolve(dt(11, 5), -1))

    def test_f002_exit_waits_for_genuine_observation_and_marks_gap(self):
        pending = PendingExit(1, dt(11))
        self.assertEqual({"action": "EXECUTE", "gap_exposed": False}, pending.resolve(dt(11, 5)))
        self.assertEqual({"action": "EXECUTE", "gap_exposed": True}, pending.resolve(dt(11, 20)))

    def test_f004_reversal_is_exit_only(self):
        self.assertEqual(
            "EXIT_ONLY_NO_CARRIED_ENTRY",
            reversal_action(True, 1, -1),
        )
        self.assertEqual(
            "EXIT_AND_REENTER",
            reversal_action(False, 1, -1),
        )


if __name__ == "__main__":
    unittest.main()
