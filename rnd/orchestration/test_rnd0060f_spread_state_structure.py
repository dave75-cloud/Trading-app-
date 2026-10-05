#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from rnd0060f_spread_state_structure import (
    RND0060FError,
    _average_ranks,
    _median,
    extract_symbol_observations,
    spearman,
    summarize_symbol,
)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _row(dt, mid=1.0, spread=0.0002, high_pad=0.0003, low_pad=0.0003):
    bid = mid - spread / 2.0
    ask = mid + spread / 2.0
    return {
        "timestamp_utc": _ts(dt),
        "complete": True,
        "bid_close": bid,
        "ask_close": ask,
        "mid_close": mid,
        "mid_high": mid + high_pad,
        "mid_low": mid - low_pad,
    }


def _day_rows(day, baseline_spread=0.0002, current_spread=0.0002, future_step=0.0001):
    start = datetime(day.year, day.month, day.day, 10, 30, tzinfo=timezone.utc)
    rows = []
    for i in range(19):  # 10:30 through 12:00 inclusive
        dt = start + timedelta(minutes=5 * i)
        mid = 1.0
        spread = baseline_spread
        if dt.hour == 11 and dt.minute == 30:
            spread = current_spread
        if dt > datetime(day.year, day.month, day.day, 11, 30, tzinfo=timezone.utc):
            mid += future_step * ((dt - datetime(day.year, day.month, day.day, 11, 30, tzinfo=timezone.utc)).seconds // 300)
        rows.append(_row(dt, mid=mid, spread=spread))
    return rows


class TestRND0060FSpreadStateStructure(unittest.TestCase):
    def test_median_even(self):
        self.assertEqual(_median([1, 4, 2, 3]), 2.5)

    def test_average_ranks_ties(self):
        self.assertEqual(_average_ranks([1, 1, 3]), [1.5, 1.5, 3.0])

    def test_spearman_positive(self):
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)

    def test_spearman_negative(self):
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)

    def test_single_day_state_ratio(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        out = extract_symbol_observations("AUDUSD", _day_rows(day, 0.0002, 0.0001))
        self.assertEqual(len(out["observations"]), 1)
        self.assertAlmostEqual(out["observations"][0]["spread_state_ratio"], 0.5)

    def test_missing_baseline_bar_excludes_day(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows = [r for r in rows if not r["timestamp_utc"].endswith("10:55:00Z")]
        out = extract_symbol_observations("AUDUSD", rows)
        self.assertEqual(len(out["observations"]), 0)
        self.assertEqual(out["exclusions"][0]["reason"], "REQUIRED_OBSERVATION_MISSING")

    def test_missing_forward_bar_excludes_day(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows = [r for r in rows if not r["timestamp_utc"].endswith("11:45:00Z")]
        out = extract_symbol_observations("AUDUSD", rows)
        self.assertEqual(len(out["observations"]), 0)

    def test_incomplete_bar_rejected(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows[0]["complete"] = False
        with self.assertRaises(RND0060FError):
            extract_symbol_observations("AUDUSD", rows)

    def test_duplicate_timestamp_rejected(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows.insert(1, dict(rows[0]))
        with self.assertRaises(RND0060FError):
            extract_symbol_observations("AUDUSD", rows)

    def test_invalid_bid_mid_ask_rejected(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows[0]["bid_close"] = rows[0]["ask_close"] + 1.0
        with self.assertRaises(RND0060FError):
            extract_symbol_observations("AUDUSD", rows)

    def test_zero_spread_rejected(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        rows = _day_rows(day)
        rows[0]["bid_close"] = rows[0]["mid_close"]
        rows[0]["ask_close"] = rows[0]["mid_close"]
        with self.assertRaises(RND0060FError):
            extract_symbol_observations("AUDUSD", rows)

    def test_forward_response_is_nonnegative(self):
        day = datetime(2019, 1, 7, tzinfo=timezone.utc)
        out = extract_symbol_observations("USDJPY", _day_rows(day, future_step=-0.0001))
        r = out["observations"][0]
        self.assertGreaterEqual(r["forward_absolute_close_return"], 0.0)
        self.assertGreaterEqual(r["forward_realized_mid_range"], 0.0)

    def test_summarize_symbol_requires_multiple_days(self):
        rows = []
        for d in (7, 8, 9, 10):
            rows.extend(_day_rows(datetime(2019, 1, d, tzinfo=timezone.utc), current_spread=0.0001 + d * 1e-6, future_step=d * 1e-5))
        out = summarize_symbol("EURUSD", rows)
        self.assertEqual(out["eligible_observation_count"], 4)
        self.assertFalse(out["trade_simulation"])
        self.assertFalse(out["pnl"])

    def test_future_year_outside_development_rejected(self):
        day = datetime(2021, 1, 4, tzinfo=timezone.utc)
        with self.assertRaises(RND0060FError):
            extract_symbol_observations("GBPUSD", _day_rows(day))


if __name__ == "__main__":
    unittest.main()
