#!/usr/bin/env python3

import unittest

from rnd0035_concurrent_portfolio import (
    RND0035ConcurrentPortfolioError,
    SYMBOLS,
    build_equal_unit_concurrent_path,
)


def _mark(symbol, ts, position, value):
    return {
        "symbol": symbol,
        "timestamp": ts,
        "position": position,
        "mark_return": value,
        "strategy_signal_available": True,
    }


def _trade(symbol, entry_ts, exit_ts, value):
    return {
        "symbol": symbol,
        "entry_timestamp": entry_ts,
        "exit_timestamp": exit_ts,
        "net_return": value,
    }


def fixture():
    t0 = "2019-01-02T11:00:00Z"
    t1 = "2019-01-02T11:05:00Z"
    t2 = "2019-01-02T11:10:00Z"
    t3 = "2019-01-02T11:15:00Z"
    return {
        "AUDUSD": {
            "symbol": "AUDUSD",
            "marks": [
                _mark("AUDUSD", t0, 1, -0.001),
                _mark("AUDUSD", t1, 1, 0.010),
                _mark("AUDUSD", t2, 0, None),
                _mark("AUDUSD", t3, 0, None),
            ],
            "trades": [_trade("AUDUSD", t0, t2, 0.008)],
            "completed_trade_count": 1,
        },
        "EURUSD": {
            "symbol": "EURUSD",
            "marks": [
                _mark("EURUSD", t0, 0, None),
                _mark("EURUSD", t1, 1, -0.002),
                _mark("EURUSD", t2, 1, 0.004),
                _mark("EURUSD", t3, 0, None),
            ],
            "trades": [_trade("EURUSD", t1, t3, 0.006)],
            "completed_trade_count": 1,
        },
        "GBPUSD": {
            "symbol": "GBPUSD",
            "marks": [
                _mark("GBPUSD", t0, 0, None),
                _mark("GBPUSD", t2, 0, None),
                _mark("GBPUSD", t3, 0, None),
            ],
            "trades": [],
            "completed_trade_count": 0,
        },
        "USDJPY": {
            "symbol": "USDJPY",
            "marks": [
                _mark("USDJPY", t0, 0, None),
                _mark("USDJPY", t1, 0, None),
                _mark("USDJPY", t2, 0, None),
                _mark("USDJPY", t3, 0, None),
            ],
            "trades": [],
            "completed_trade_count": 0,
        },
    }


class TestRND0035ConcurrentPortfolio(unittest.TestCase):
    def test_exact_four_symbol_universe_required(self):
        data = fixture()
        data.pop("USDJPY")
        with self.assertRaisesRegex(RND0035ConcurrentPortfolioError, "exactly four"):
            build_equal_unit_concurrent_path(data)

    def test_overlap_and_exit_are_accounted_without_sequential_compounding(self):
        out = build_equal_unit_concurrent_path(fixture())
        path = out["path"]
        self.assertEqual(out["timestamp_count"], 4)

        # t0: only AUD active at executable spread mark.
        self.assertAlmostEqual(path[0]["equal_unit_pnl_level"], -0.001)
        self.assertEqual(path[0]["active_pair_count"], 1)

        # t1: AUD + EUR overlap, additive equal-unit marks.
        self.assertAlmostEqual(path[1]["equal_unit_pnl_level"], 0.010 - 0.002)
        self.assertEqual(path[1]["active_pair_count"], 2)

        # t2: AUD realizes +0.008 exactly once; EUR remains open at +0.004.
        self.assertAlmostEqual(path[2]["equal_unit_pnl_level"], 0.008 + 0.004)
        self.assertAlmostEqual(path[2]["per_pair"]["AUDUSD"]["realized_net_return_sum"], 0.008)
        self.assertAlmostEqual(path[2]["per_pair"]["AUDUSD"]["unrealized_executable_mark_return"], 0.0)

        # t3: EUR also realizes; final P&L is additive realized trade return sum.
        self.assertAlmostEqual(path[3]["equal_unit_pnl_level"], 0.014)
        self.assertAlmostEqual(out["realized_completed_trade_net_return_sum"], 0.014)
        self.assertAlmostEqual(out["final_unrealized_executable_mark_return_sum"], 0.0)
        self.assertFalse(out["sequential_mixed_trade_compounding"])

    def test_asynchronous_mark_is_carried_forward_without_manufactured_move(self):
        data = fixture()
        # Remove AUD's t1 observation. At EUR's t1 timestamp, AUD's genuine t0
        # executable mark remains unchanged rather than interpolated.
        data["AUDUSD"]["marks"].pop(1)
        out = build_equal_unit_concurrent_path(data)
        t1 = next(x for x in out["path"] if x["timestamp"] == "2019-01-02T11:05:00Z")
        self.assertAlmostEqual(t1["per_pair"]["AUDUSD"]["unrealized_executable_mark_return"], -0.001)
        self.assertEqual(t1["per_pair"]["AUDUSD"]["source_timestamp"], "2019-01-02T11:00:00Z")

    def test_exit_requires_same_timestamp_executable_mark_evidence(self):
        data = fixture()
        data["AUDUSD"]["marks"] = [m for m in data["AUDUSD"]["marks"] if m["timestamp"] != "2019-01-02T11:10:00Z"]
        with self.assertRaisesRegex(RND0035ConcurrentPortfolioError, "exit lacks same-timestamp"):
            build_equal_unit_concurrent_path(data)

    def test_authority_remains_closed(self):
        out = build_equal_unit_concurrent_path(fixture())
        self.assertEqual(tuple(sorted(SYMBOLS)), tuple(sorted(fixture())))
        for key in (
            "dependence_resampling",
            "validation_open",
            "final_test_open",
            "strategy_selection",
            "portfolio_sizing",
            "broker_writes",
            "capital_authority",
            "automatic_promotion",
            "automatic_merge",
        ):
            self.assertFalse(out["authority"][key])
        self.assertTrue(out["authority"]["human_review_required"])


if __name__ == "__main__":
    unittest.main()
