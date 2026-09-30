#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import unittest

from gap_aware_m005_reconstruction import (
    GapAwareM005Error,
    population_std,
    reconstruct_pair,
)


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


class GapAwareM005Tests(unittest.TestCase):
    def test_population_std_is_ddof_zero(self):
        self.assertAlmostEqual(0.5, population_std([1.0, 2.0]))

    def test_outside_authorized_year_fails_closed(self):
        with self.assertRaisesRegex(GapAwareM005Error, "outside 2015-2019"):
            reconstruct_pair("AUDUSD", rows(2, "2020-01-02T07:00:00Z"))

    def test_bid_ask_execution_creates_real_cost_drag(self):
        result = reconstruct_pair("AUDUSD", rows(90))
        self.assertGreater(result["completed_trade_count"], 0)
        trade = result["trades"][0]
        self.assertGreater(trade["gross_return"], trade["net_return"])
        self.assertGreater(trade["execution_cost_drag"], 0.0)

    def test_gap_breaks_indicator_continuity(self):
        # Two 30-bar fragments must not combine into a synthetic 60-bar warm-up.
        result = reconstruct_pair("AUDUSD", rows(60, gap_after=30))
        self.assertEqual(2, result["contiguous_episode_count"])
        self.assertEqual(1, result["gap_count"])
        self.assertEqual(0, result["completed_trade_count"])
        self.assertEqual(0, result["censored_trade_count"])

    def test_open_position_at_gap_is_censored_not_closed(self):
        result = reconstruct_pair("AUDUSD", rows(70, gap_after=56))
        self.assertEqual(1, result["gap_count"])
        self.assertEqual(0, result["completed_trade_count"])
        self.assertEqual(1, result["censored_trade_count"])
        censored = result["censored_trades"][0]
        self.assertEqual("GAP_CENSORED_INDETERMINATE", censored["status"])
        self.assertIsNotNone(censored["next_observed_timestamp"])

    def test_open_position_at_sample_end_is_right_censored(self):
        result = reconstruct_pair("AUDUSD", rows(56))
        self.assertEqual(0, result["completed_trade_count"])
        self.assertEqual(1, result["censored_trade_count"])
        self.assertEqual(
            "RIGHT_CENSORED_END_OF_SAMPLE",
            result["censored_trades"][0]["status"],
        )

    def test_no_portfolio_or_promotion_authority(self):
        result = reconstruct_pair("AUDUSD", rows(90))
        authority = result["authority"]
        self.assertFalse(authority["strategy_selection"])
        self.assertFalse(authority["portfolio_sizing"])
        self.assertFalse(authority["broker_writes"])
        self.assertFalse(authority["capital_authority"])
        self.assertFalse(authority["automatic_promotion"])
        self.assertFalse(authority["automatic_merge"])
        self.assertTrue(authority["human_review_required"])

    def test_duplicate_and_out_of_order_rows_rejected(self):
        value = rows(3)
        value.append(dict(value[-1]))
        with self.assertRaisesRegex(GapAwareM005Error, "duplicate"):
            reconstruct_pair("AUDUSD", value)

    def test_bid_mid_ask_ordering_rejected(self):
        value = rows(2)
        value[0]["bid_close"] = "2"
        with self.assertRaisesRegex(GapAwareM005Error, "ordering"):
            reconstruct_pair("AUDUSD", value)


if __name__ == "__main__":
    unittest.main()
