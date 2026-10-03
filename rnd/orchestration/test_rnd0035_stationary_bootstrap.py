#!/usr/bin/env python3

import random
import unittest

from rnd0035_stationary_bootstrap import (
    EXPECTED_BLOCK_LENGTHS,
    REPLICATIONS,
    SEEDS,
    RND0035BootstrapError,
    concurrent_portfolio_bootstrap,
    declared_configuration_grid,
    sample_statistics,
    stationary_resample,
)


class TestRND0035StationaryBootstrap(unittest.TestCase):
    def setUp(self):
        self.stream = [
            {"symbol": "AUDUSD", "net_return": 0.01},
            {"symbol": "EURUSD", "net_return": -0.02},
            {"symbol": "GBPUSD", "net_return": 0.03},
            {"symbol": "USDJPY", "net_return": 0.00},
        ]

    def test_declared_grid_is_exactly_nine_configurations(self):
        grid = declared_configuration_grid()
        self.assertEqual(len(grid), 9)
        self.assertEqual({x["seed"] for x in grid}, set(SEEDS))
        self.assertEqual(
            {x["expected_block_length_trades"] for x in grid},
            set(EXPECTED_BLOCK_LENGTHS),
        )
        self.assertEqual(REPLICATIONS, 10000)

    def test_stationary_resample_is_deterministic_for_seed(self):
        a = stationary_resample(self.stream, 10, random.Random(1729))
        b = stationary_resample(self.stream, 10, random.Random(1729))
        self.assertEqual(a, b)
        self.assertEqual(len(a), len(self.stream))
        self.assertTrue(all("symbol" in item and "net_return" in item for item in a))

    def test_sample_statistics_are_defined(self):
        out = sample_statistics(self.stream)
        self.assertIn("mean_net_return", out)
        self.assertIn("compounded_net_equity_index", out)
        self.assertIn("max_drawdown", out)
        self.assertIn("positive_total_net_return_indicator", out)

    def test_concurrent_portfolio_path_fails_closed(self):
        with self.assertRaisesRegex(RND0035BootstrapError, "sequential mixed-trade compounding is prohibited"):
            concurrent_portfolio_bootstrap(self.stream)


if __name__ == "__main__":
    unittest.main()
