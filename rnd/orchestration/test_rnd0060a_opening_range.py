import unittest
from datetime import datetime, timedelta, timezone

from rnd0060a_opening_range import RND0060AError, evaluate_symbol


def z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row(dt, mid, high=None, low=None, spread=0.0002):
    high = mid if high is None else high
    low = mid if low is None else low
    half = spread / 2
    return {
        "timestamp_utc": z(dt),
        "complete": True,
        "bid_close": mid - half,
        "ask_close": mid + half,
        "mid_close": mid,
        "mid_high": high,
        "mid_low": low,
    }


def day_rows(signal="LONG", omit=None, gap_after_entry=False):
    start = datetime(2019, 1, 2, 10, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(12):
        dt = start + timedelta(minutes=5 * i)
        rows.append(row(dt, 1.1000, high=1.1010, low=1.0990))

    first_dt = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)
    first_mid = {"LONG": 1.1020, "SHORT": 1.0980, "NONE": 1.1000}[signal]
    rows.append(row(first_dt, first_mid, high=max(first_mid, 1.1022), low=min(first_mid, 1.0978)))

    levels = [
        (datetime(2019, 1, 2, 11, 5, tzinfo=timezone.utc), 1.1022 if signal != "SHORT" else 1.0978),
        (datetime(2019, 1, 2, 11, 10, tzinfo=timezone.utc), 1.1024 if signal != "SHORT" else 1.0976),
        (datetime(2019, 1, 2, 11, 15, tzinfo=timezone.utc), 1.1026 if signal != "SHORT" else 1.0974),
        (datetime(2019, 1, 2, 11, 20, tzinfo=timezone.utc), 1.1028 if signal != "SHORT" else 1.0972),
        (datetime(2019, 1, 2, 11, 25, tzinfo=timezone.utc), 1.1030 if signal != "SHORT" else 1.0970),
    ]
    if gap_after_entry:
        levels = [levels[0], levels[2], levels[3], levels[4]]
    for dt, mid in levels:
        rows.append(row(dt, mid, high=mid + 0.0002, low=mid - 0.0002))

    if omit is not None:
        rows = [r for r in rows if r["timestamp_utc"] != z(omit)]
    return rows


def weekend_gap_rows():
    rows = []
    start = datetime(2019, 1, 4, 10, 0, tzinfo=timezone.utc)
    for i in range(12):
        rows.append(row(start + timedelta(minutes=5 * i), 1.1000, high=1.1010, low=1.0990))
    rows.append(row(datetime(2019, 1, 4, 11, 0, tzinfo=timezone.utc), 1.1020, high=1.1022, low=1.1018))
    rows.append(row(datetime(2019, 1, 4, 11, 5, tzinfo=timezone.utc), 1.1022, high=1.1024, low=1.1020))
    rows.append(row(datetime(2019, 1, 7, 10, 50, tzinfo=timezone.utc), 1.1024, high=1.1026, low=1.1022))
    rows.append(row(datetime(2019, 1, 7, 10, 55, tzinfo=timezone.utc), 1.1026, high=1.1028, low=1.1024))
    rows.append(row(datetime(2019, 1, 7, 11, 0, tzinfo=timezone.utc), 1.1028, high=1.1030, low=1.1026))
    return rows


class TestRND0060AOpeningRange(unittest.TestCase):
    def test_long_breakout_executes_next_bar_and_holds_three_observed_bars(self):
        out = evaluate_symbol("AUDUSD", day_rows("LONG"))
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["side"], "long")
        self.assertEqual(trade["entry_timestamp"], "2019-01-02T11:05:00Z")
        self.assertEqual(trade["exit_timestamp"], "2019-01-02T11:20:00Z")
        self.assertEqual(trade["holding_bars"], 3)
        self.assertGreater(trade["net_return"], 0)

    def test_short_breakout_uses_bid_entry_and_ask_exit(self):
        out = evaluate_symbol("EURUSD", day_rows("SHORT"))
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["side"], "short")
        self.assertGreater(trade["entry_execution_price"], trade["exit_execution_price"])
        self.assertGreater(trade["net_return"], 0)

    def test_no_breakout_means_no_trade(self):
        out = evaluate_symbol("GBPUSD", day_rows("NONE"))
        self.assertEqual(out["trade_count"], 0)

    def test_missing_lookback_bar_blocks_signal(self):
        omit = datetime(2019, 1, 2, 10, 30, tzinfo=timezone.utc)
        out = evaluate_symbol("USDJPY", day_rows("LONG", omit=omit))
        self.assertEqual(out["trade_count"], 0)
        self.assertTrue(any(e["event_type"] == "NO_SIGNAL_LOOKBACK_GAP" for e in out["events"]))

    def test_gap_before_delayed_entry_cancels_signal(self):
        omit = datetime(2019, 1, 2, 11, 5, tzinfo=timezone.utc)
        out = evaluate_symbol("AUDUSD", day_rows("LONG", omit=omit))
        self.assertEqual(out["trade_count"], 0)
        self.assertTrue(any(e["event_type"] == "PENDING_SIGNAL_CANCELLED" for e in out["events"]))

    def test_gap_during_position_survives_and_missing_bar_does_not_count(self):
        out = evaluate_symbol("AUDUSD", day_rows("LONG", gap_after_entry=True))
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["exit_timestamp"], "2019-01-02T11:25:00Z")
        self.assertEqual(trade["holding_bars"], 3)
        self.assertEqual(trade["gap_exposure_count"], 1)

    def test_position_survives_weekend_and_blocks_second_session_signal(self):
        out = evaluate_symbol("AUDUSD", weekend_gap_rows())
        self.assertEqual(out["trade_count"], 1)
        trade = out["trades"][0]
        self.assertEqual(trade["exit_timestamp"], "2019-01-07T11:00:00Z")
        self.assertEqual(trade["holding_bars"], 3)
        self.assertEqual(trade["gap_exposure_count"], 1)
        self.assertTrue(any(e["event_type"] == "NO_SIGNAL_POSITION_ALREADY_OPEN" for e in out["events"]))

    def test_executable_marks_active_at_entry_and_flat_at_exit(self):
        out = evaluate_symbol("AUDUSD", day_rows("LONG"))
        by_ts = {m["timestamp"]: m for m in out["marks"]}
        self.assertEqual(by_ts["2019-01-02T11:05:00Z"]["position"], 1)
        self.assertIsNotNone(by_ts["2019-01-02T11:05:00Z"]["mark_return"])
        self.assertEqual(by_ts["2019-01-02T11:20:00Z"]["position"], 0)
        self.assertIsNone(by_ts["2019-01-02T11:20:00Z"]["mark_return"])

    def test_bid_ask_cost_drag_is_positive(self):
        trade = evaluate_symbol("AUDUSD", day_rows("LONG"))["trades"][0]
        self.assertGreater(trade["execution_cost_drag"], 0)
        self.assertGreater(trade["gross_return"], trade["net_return"])

    def test_development_year_firewall(self):
        rows = day_rows("LONG")
        rows[0] = dict(rows[0], timestamp_utc="2021-01-02T10:00:00Z")
        with self.assertRaises(RND0060AError):
            evaluate_symbol("AUDUSD", rows)

    def test_authority_remains_closed(self):
        out = evaluate_symbol("AUDUSD", day_rows("LONG"))
        self.assertTrue(out["development_only"])
        self.assertFalse(out["reserved_final_access"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
