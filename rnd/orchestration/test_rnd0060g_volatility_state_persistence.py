#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060g_volatility_state_persistence import (
    RND0060GError,
    extract_symbol_observations,
    spearman,
    summarize_symbol,
    validate_rows,
)


START = datetime(2019, 1, 2, 9, 30, tzinfo=timezone.utc)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _day_rows(baseline_return=0.001, current_return=0.003, forward_return=0.001):
    rows = []
    mid = 1.0
    for i in range(31):
        dt = START + timedelta(minutes=5 * i)
        if i > 0:
            if i <= 18:
                r = baseline_return
            elif i <= 24:
                r = current_return
            else:
                r = forward_return
            mid *= (1.0 + r)
        rows.append({
            "timestamp_utc": _ts(dt),
            "complete": True,
            "mid_close": mid,
            "mid_high": mid * 1.0002,
            "mid_low": mid * 0.9998,
        })
    return rows


class RND0060GKernelTests(unittest.TestCase):
    def test_01_rejects_unsupported_symbol(self):
        with self.assertRaises(RND0060GError):
            extract_symbol_observations("NZDUSD", _day_rows())

    def test_02_rejects_empty_rows(self):
        with self.assertRaises(RND0060GError):
            validate_rows([])

    def test_03_rejects_non_development_year(self):
        rows = _day_rows()
        rows[0]["timestamp_utc"] = "2021-01-04T09:30:00Z"
        with self.assertRaises(RND0060GError):
            validate_rows(rows)

    def test_04_rejects_incomplete_candle(self):
        rows = _day_rows()
        rows[3]["complete"] = False
        with self.assertRaises(RND0060GError):
            validate_rows(rows)

    def test_05_rejects_duplicate_or_unordered_timestamps(self):
        rows = _day_rows()
        rows[5]["timestamp_utc"] = rows[4]["timestamp_utc"]
        with self.assertRaises(RND0060GError):
            validate_rows(rows)

    def test_06_rejects_missing_required_field(self):
        rows = _day_rows()
        del rows[2]["mid_high"]
        with self.assertRaises(RND0060GError):
            validate_rows(rows)

    def test_07_rejects_invalid_mid_ohlc_ordering(self):
        rows = _day_rows()
        rows[4]["mid_low"] = rows[4]["mid_close"] * 1.01
        with self.assertRaises(RND0060GError):
            validate_rows(rows)

    def test_08_exact_nonoverlapping_state_ratio(self):
        out = extract_symbol_observations("AUDUSD", _day_rows())
        self.assertEqual(len(out["observations"]), 1)
        obs = out["observations"][0]
        self.assertAlmostEqual(obs["baseline_mean_absolute_m5_mid_return"], 0.001, places=12)
        self.assertAlmostEqual(obs["current_mean_absolute_m5_mid_return"], 0.003, places=12)
        self.assertAlmostEqual(obs["volatility_state_ratio"], 3.0, places=10)

    def test_09_missing_required_bar_excludes_observation(self):
        rows = _day_rows()
        rows = [r for r in rows if r["timestamp_utc"] != "2019-01-02T10:15:00Z"]
        out = extract_symbol_observations("EURUSD", rows)
        self.assertEqual(out["observations"], [])
        self.assertEqual(out["exclusions"][0]["reason"], "REQUIRED_OBSERVATION_MISSING")

    def test_10_zero_baseline_volatility_excludes_observation(self):
        out = extract_symbol_observations("GBPUSD", _day_rows(baseline_return=0.0))
        self.assertEqual(out["observations"], [])
        self.assertEqual(out["exclusions"][0]["reason"], "ZERO_BASELINE_REALIZED_VOLATILITY")

    def test_11_forward_responses_are_nonnegative(self):
        obs = extract_symbol_observations("USDJPY", _day_rows())["observations"][0]
        self.assertGreaterEqual(obs["forward_realized_mid_range"], 0.0)
        self.assertGreaterEqual(obs["forward_absolute_close_return"], 0.0)

    def test_12_spearman_handles_ties_with_average_ranks(self):
        value = spearman([1, 1, 2, 3], [1, 2, 3, 4])
        self.assertGreater(value, 0.9)
        self.assertLessEqual(value, 1.0)

    def test_13_spearman_rejects_constant_input(self):
        with self.assertRaises(RND0060GError):
            spearman([1, 1, 1], [1, 2, 3])

    def test_14_summary_preserves_no_authority_flags(self):
        rows = []
        for d, cr in enumerate((0.0015, 0.0020, 0.0025, 0.0030)):
            day = _day_rows(current_return=cr, forward_return=0.0005 + d * 0.0002)
            shift = timedelta(days=d)
            for r in day:
                dt = datetime.fromisoformat(r["timestamp_utc"][:-1] + "+00:00") + shift
                r = dict(r)
                r["timestamp_utc"] = _ts(dt)
                rows.append(r)
        rows.sort(key=lambda r: r["timestamp_utc"])
        result = summarize_symbol("AUDUSD", rows)
        self.assertFalse(result["trade_simulation"])
        self.assertFalse(result["pnl"])
        self.assertFalse(result["validation_open"])
        self.assertFalse(result["final_test_open"])
        self.assertFalse(result["reserved_final_access"])
        self.assertFalse(result["broker_writes"])
        self.assertFalse(result["capital_authority"])
        self.assertFalse(result["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
