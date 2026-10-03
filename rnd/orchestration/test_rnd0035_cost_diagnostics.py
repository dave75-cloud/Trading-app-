#!/usr/bin/env python3

import unittest

from rnd0035_cost_diagnostics import (
    RND0035CostDiagnosticError,
    break_even_additional_round_trip_bps,
    cost_bridge,
    stressed_net_equity,
)


class TestRND0035CostDiagnostics(unittest.TestCase):
    def test_already_adverse_reference_has_zero_additional_break_even(self):
        trades = [
            {"gross_return": 0.01, "net_return": -0.01},
            {"gross_return": 0.01, "net_return": 0.0},
        ]
        self.assertEqual(break_even_additional_round_trip_bps(trades), 0.0)

    def test_positive_reference_break_even_is_deterministic(self):
        trades = [
            {"gross_return": 0.011, "net_return": 0.01},
            {"gross_return": 0.011, "net_return": 0.01},
        ]
        bps = break_even_additional_round_trip_bps(trades)
        self.assertGreater(bps, 0.0)
        self.assertAlmostEqual(stressed_net_equity(trades, bps), 1.0, places=12)

    def test_bridge_reports_declared_cost_grid_and_authority_false(self):
        trades = [
            {"gross_return": 0.02, "net_return": 0.015},
            {"gross_return": -0.005, "net_return": -0.01},
        ]
        out = cost_bridge(trades)
        self.assertEqual(set(out["declared_stressed_net_equity"]), {"0.5", "1", "2", "5"})
        self.assertFalse(out["strategy_selection_authority"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["validation_open"])
        self.assertFalse(out["final_test_open"])

    def test_rejects_invalid_trade_return(self):
        with self.assertRaises(RND0035CostDiagnosticError):
            cost_bridge([{"gross_return": 0.01, "net_return": float("nan")}])


if __name__ == "__main__":
    unittest.main()
