import unittest
from datetime import datetime, timedelta, timezone

from rnd0060b_displacement_mean_reversion import (
    DISPLACEMENT_THRESHOLD,
    RND0060BError,
    evaluate_symbol,
)


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


def displacement_fixture(direction="UP", omit=None, second_signal=False):
    start = datetime(2019, 1, 2, 10, 30, tzinfo=timezone.utc)
    rows = []
    base = 1.0
    for i in range(7):
        dt = start + timedelta(minutes=5 * i)
        if i < 6:
            mid = base
        else:
            mid = 1.0021 if direction == "UP" else (0.9979 if direction == "DOWN" else 1.0010)
        rows.append(row(dt, mid))

    # signal at 11:00, entry 11:05, then three post-entry observations
    levels = [
        (datetime(2019, 1, 2, 11, 5, tzinfo=timezone.utc), 1.0018 if direction == "UP" else 0.9982),
        (datetime(2019, 1, 2, 11, 10, tzinfo=timezone.utc), 1.0014 if direction == "UP" else 0.9986),
        (datetime(2019, 1, 2, 11, 15, tzinfo=timezone.utc), 1.0010 if direction == "UP" else 0.9990),
        (datetime(2019, 1, 2, 11, 20, tzinfo=timezone.utc), 1.0007 if direction == "UP" else 0.9993),
    ]
    for dt, mid in levels:
        rows.append(row(dt, mid))

    if second_signal:
        rows.append(row(datetime(2019, 1, 2, 11, 25, tzinfo=timezone.utc), 1.0040 if direction == "UP" else 0.9960))
        rows.append(row(datetime(2019, 1, 2, 11, 30, tzinfo=timezone.utc), 1.0035 if direction == "UP" else 0.9965))
        rows.append(row(datetime(2019, 1, 2, 11, 35, tzinfo=timezone.utc), 1.0030 if direction == "UP" else 0.9970))
        rows.append(row(datetime(2019, 1, 2, 11, 40, tzinfo=timezone.utc), 1.0025 if direction == "UP" else 0.9975))

    if omit is not None:
        rows = [r for r in rows if r["timestamp_utc"] != z(omit)]
    return rows


class TestRND0060BDisplacementMeanReversion(unittest.TestCase):
    def test_up_displacement_fades_short(self):
        out = evaluate_symbol("AUDUSD", displacement_fixture("UP"))
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["side"], "short")
        self.assertEqual(trade["entry_timestamp"], "2019-01-02T11:05:00Z")
        self.assertEqual(trade["exit_timestamp"], "2019-01-02T11:20:00Z")
        self.assertEqual(trade["holding_bars"], 3)
        self.assertGreater(trade["net_return"], 0)

    def test_down_displacement_fades_long(self):
        out = evaluate_symbol("EURUSD", displacement_fixture("DOWN"))
        self.assertEqual(out["trade_count"], 1)
        self.assertEqual(out["trades"][0]["side"], "long")
        self.assertGreater(out["trades"][0]["net_return"], 0)

    def test_subthreshold_displacement_has_no_trade(self):
        out = evaluate_symbol("GBPUSD", displacement_fixture("NONE"))
        self.assertEqual(out["trade_count"], 0)

    def test_threshold_is_fixed_at_twenty_basis_points(self):
        self.assertEqual(DISPLACEMENT_THRESHOLD, 0.0020)

    def test_gap_inside_six_bar_window_blocks_signal(self):
        omit = datetime(2019, 1, 2, 10, 45, tzinfo=timezone.utc)
        out = evaluate_symbol("USDJPY", displacement_fixture("UP", omit=omit))
        self.assertEqual(out["trade_count"], 0)

    def test_gap_before_delayed_entry_cancels_and_no_same_day_retry(self):
        omit = datetime(2019, 1, 2, 11, 5, tzinfo=timezone.utc)
        out = evaluate_symbol("AUDUSD", displacement_fixture("UP", omit=omit, second_signal=True))
        self.assertEqual(out["trade_count"], 0)
        cancelled = [e for e in out["events"] if e["event_type"] == "PENDING_SIGNAL_CANCELLED"]
        self.assertEqual(len(cancelled), 1)
        signals = [e for e in out["events"] if e["event_type"] == "DISPLACEMENT_SIGNAL"]
        self.assertEqual(len(signals), 1)

    def test_one_trade_per_symbol_day(self):
        out = evaluate_symbol("AUDUSD", displacement_fixture("UP", second_signal=True))
        self.assertEqual(out["trade_count"], 1)
        signals = [e for e in out["events"] if e["event_type"] == "DISPLACEMENT_SIGNAL"]
        self.assertEqual(len(signals), 1)

    def test_gap_during_position_survives_and_missing_bar_does_not_count(self):
        rows = displacement_fixture("UP")
        omit = z(datetime(2019, 1, 2, 11, 10, tzinfo=timezone.utc))
        rows = [r for r in rows if r["timestamp_utc"] != omit]
        rows.append(row(datetime(2019, 1, 2, 11, 25, tzinfo=timezone.utc), 1.0005))
        rows.sort(key=lambda r: r["timestamp_utc"])
        out = evaluate_symbol("AUDUSD", rows)
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["holding_bars"], 3)
        self.assertEqual(trade["gap_exposure_count"], 1)
        self.assertEqual(trade["exit_timestamp"], "2019-01-02T11:25:00Z")

    def test_entry_bar_is_not_counted_as_hold_bar(self):
        trade = evaluate_symbol("AUDUSD", displacement_fixture("UP"))["trades"][0]
        self.assertEqual(trade["entry_timestamp"], "2019-01-02T11:05:00Z")
        self.assertEqual(trade["exit_timestamp"], "2019-01-02T11:20:00Z")

    def test_bid_ask_cost_drag_positive(self):
        trade = evaluate_symbol("AUDUSD", displacement_fixture("UP"))["trades"][0]
        self.assertGreater(trade["execution_cost_drag"], 0)
        self.assertGreater(trade["gross_return"], trade["net_return"])

    def test_last_session_bar_signal_cannot_enter_outside_session(self):
        rows = []
        start = datetime(2019, 1, 2, 12, 25, tzinfo=timezone.utc)
        for i in range(7):
            dt = start + timedelta(minutes=5 * i)
            mid = 1.0 if i < 6 else 1.0021
            rows.append(row(dt, mid))
        # EURUSD session is [11,13), so signal at 12:55, next bar 13:00 is ineligible.
        rows.append(row(datetime(2019, 1, 2, 13, 0, tzinfo=timezone.utc), 1.0018))
        out = evaluate_symbol("EURUSD", rows)
        self.assertEqual(out["trade_count"], 0)
        self.assertTrue(any(e["event_type"] == "PENDING_SIGNAL_CANCELLED" for e in out["events"]))

    def test_development_year_firewall(self):
        rows = displacement_fixture("UP")
        rows[0] = dict(rows[0], timestamp_utc="2021-01-02T10:30:00Z")
        with self.assertRaises(RND0060BError):
            evaluate_symbol("AUDUSD", rows)

    def test_authority_remains_closed(self):
        out = evaluate_symbol("AUDUSD", displacement_fixture("UP"))
        self.assertTrue(out["development_only"])
        self.assertFalse(out["reserved_final_access"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
