#!/usr/bin/env python3

import unittest

from rnd0035_concurrent_reference_stats import concurrent_reference_statistics


def mark(symbol, ts, position, value):
    return {"symbol": symbol, "timestamp": ts, "position": position, "mark_return": value}


def trade(symbol, entry_ts, exit_ts, value):
    return {"symbol": symbol, "entry_timestamp": entry_ts, "exit_timestamp": exit_ts, "net_return": value}


def fixture():
    t0 = "2019-01-02T11:00:00Z"
    t1 = "2019-01-02T11:05:00Z"
    t2 = "2019-01-02T11:10:00Z"
    empty = lambda symbol: {
        "symbol": symbol,
        "marks": [mark(symbol, t0, 0, None), mark(symbol, t1, 0, None), mark(symbol, t2, 0, None)],
        "trades": [],
        "completed_trade_count": 0,
    }
    return {
        "AUDUSD": {
            "symbol": "AUDUSD",
            "marks": [mark("AUDUSD", t0, 1, -0.004), mark("AUDUSD", t1, 1, 0.004), mark("AUDUSD", t2, 0, None)],
            "trades": [trade("AUDUSD", t0, t2, 0.008)],
            "completed_trade_count": 1,
        },
        "EURUSD": empty("EURUSD"),
        "GBPUSD": empty("GBPUSD"),
        "USDJPY": empty("USDJPY"),
    }


class TestRND0035ConcurrentReferenceStats(unittest.TestCase):
    def test_fixed_four_unit_normalization(self):
        out = concurrent_reference_statistics(fixture())
        self.assertEqual(out["timestamp_count"], 3)
        self.assertAlmostEqual(out["final_equal_unit_normalized_equity_index"], 1.002)
        self.assertEqual(out["normalization"], "ONE_PLUS_FOUR_PAIR_EQUAL_UNIT_PNL_DIVIDED_BY_FOUR")

    def test_drawdown_uses_timestamped_concurrent_path(self):
        out = concurrent_reference_statistics(fixture())
        self.assertLessEqual(out["equal_unit_normalized_max_drawdown"], 0.0)
        self.assertGreaterEqual(out["max_active_pair_count"], 1)

    def test_no_resampling_or_authority_is_granted(self):
        out = concurrent_reference_statistics(fixture())
        for key in (
            "dependence_resampling",
            "strategy_selection",
            "validation_open",
            "final_test_open",
            "broker_writes",
            "capital_authority",
            "capital_allocation",
            "portfolio_sizing",
        ):
            self.assertFalse(out[key])


if __name__ == "__main__":
    unittest.main()
