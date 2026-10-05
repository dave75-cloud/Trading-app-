import unittest
from datetime import datetime, timedelta, timezone

from rnd0060d_three_bar_directional_persistence import RND0060DError, evaluate_symbol


def z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row(dt, mid, spread=0.0002):
    half = spread / 2
    return {
        "timestamp_utc": z(dt),
        "complete": True,
        "bid_close": mid - half,
        "ask_close": mid + half,
        "mid_close": mid,
    }


def rows_from_mids(mids, start=None, omit=None):
    start = start or datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)
    omit = omit or set()
    out = []
    for i, mid in enumerate(mids):
        dt = start + timedelta(minutes=5 * i)
        if z(dt) not in omit:
            out.append(row(dt, mid))
    return out


class TestRND0060DThreeBarDirectionalPersistence(unittest.TestCase):
    def test_three_positive_returns_signal_long_next_bar_hold_three(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        out = evaluate_symbol("AUDUSD", rows)
        t = out["trades"][0]
        self.assertEqual(t["side"], "long")
        self.assertEqual(t["entry_timestamp"], "2019-01-02T11:20:00Z")
        self.assertEqual(t["exit_timestamp"], "2019-01-02T11:35:00Z")
        self.assertEqual(t["holding_bars"], 3)

    def test_three_negative_returns_signal_short(self):
        rows = rows_from_mids([1.0030, 1.0025, 1.0020, 1.0015, 1.0014, 1.0012, 1.0010, 1.0008])
        out = evaluate_symbol("EURUSD", rows)
        self.assertEqual(out["trades"][0]["side"], "short")

    def test_zero_return_breaks_streak(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0005, 1.0010, 1.0009, 1.0008])
        out = evaluate_symbol("AUDUSD", rows)
        self.assertEqual(out["trade_count"], 0)

    def test_gap_inside_signal_window_blocks_streak(self):
        omit = {"2019-01-02T11:10:00Z"}
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018], omit=omit)
        out = evaluate_symbol("AUDUSD", rows)
        self.assertEqual(out["trade_count"], 0)

    def test_missing_delayed_entry_cancels_signal(self):
        omit = {"2019-01-02T11:20:00Z"}
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020], omit=omit)
        out = evaluate_symbol("AUDUSD", rows)
        self.assertEqual(out["trade_count"], 0)
        self.assertTrue(any(e["event_type"] == "PENDING_SIGNAL_CANCELLED" for e in out["events"]))

    def test_entry_bar_does_not_count_as_holding_bar_one(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        t = evaluate_symbol("AUDUSD", rows)["trades"][0]
        self.assertEqual(t["entry_timestamp"], "2019-01-02T11:20:00Z")
        self.assertEqual(t["exit_timestamp"], "2019-01-02T11:35:00Z")

    def test_gap_during_position_survives_and_missing_bar_does_not_count(self):
        omit = {"2019-01-02T11:30:00Z"}
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022, 1.0024], omit=omit)
        t = evaluate_symbol("AUDUSD", rows)["trades"][0]
        self.assertEqual(t["gap_exposure_count"], 1)
        self.assertEqual(t["exit_timestamp"], "2019-01-02T11:40:00Z")
        self.assertEqual(t["holding_bars"], 3)

    def test_first_qualifying_streak_consumes_day(self):
        rows = rows_from_mids([
            1.0000, 1.0005, 1.0010, 1.0015, 1.0014, 1.0013, 1.0012, 1.0011,
            1.0010, 1.0009, 1.0008, 1.0007,
        ])
        out = evaluate_symbol("AUDUSD", rows)
        self.assertEqual(out["trade_count"], 1)
        self.assertEqual(sum(e["event_type"] == "THREE_BAR_PERSISTENCE_SIGNAL" for e in out["events"]), 1)

    def test_signal_whose_entry_would_leave_session_is_cancelled(self):
        start = datetime(2019, 1, 2, 12, 40, tzinfo=timezone.utc)
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016], start=start)
        out = evaluate_symbol("EURUSD", rows)
        self.assertEqual(out["trade_count"], 0)
        self.assertTrue(any(e.get("reason") == "ENTRY_OUTSIDE_FROZEN_SESSION" for e in out["events"]))

    def test_short_uses_bid_entry_and_ask_exit(self):
        rows = rows_from_mids([1.0030, 1.0025, 1.0020, 1.0015, 1.0014, 1.0012, 1.0010, 1.0008])
        t = evaluate_symbol("GBPUSD", rows)["trades"][0]
        self.assertLess(t["entry_execution_price"], t["entry_mid_price"])
        self.assertGreater(t["exit_execution_price"], t["exit_mid_price"])

    def test_execution_cost_drag_positive(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        t = evaluate_symbol("AUDUSD", rows)["trades"][0]
        self.assertGreater(t["execution_cost_drag"], 0)
        self.assertGreater(t["gross_return"], t["net_return"])

    def test_executable_marks_active_at_entry_and_flat_at_exit(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        out = evaluate_symbol("AUDUSD", rows)
        marks = {m["timestamp"]: m for m in out["marks"]}
        self.assertEqual(marks["2019-01-02T11:20:00Z"]["position"], 1)
        self.assertEqual(marks["2019-01-02T11:35:00Z"]["position"], 0)

    def test_development_year_firewall(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        rows[0] = dict(rows[0], timestamp_utc="2021-01-02T11:00:00Z")
        with self.assertRaises(RND0060DError):
            evaluate_symbol("AUDUSD", rows)

    def test_authority_remains_closed(self):
        rows = rows_from_mids([1.0000, 1.0005, 1.0010, 1.0015, 1.0016, 1.0018, 1.0020, 1.0022])
        out = evaluate_symbol("AUDUSD", rows)
        self.assertTrue(out["development_only"])
        self.assertFalse(out["reserved_final_access"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
