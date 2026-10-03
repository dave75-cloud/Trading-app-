#!/usr/bin/env python3

import unittest

from rnd0035_concentration_diagnostics import concentration_diagnostics


class TestRND0035ConcentrationDiagnostics(unittest.TestCase):
    def test_frozen_b_diagnostics_cover_declared_views(self):
        trades = [
            {"symbol": "AUDUSD", "exit_year": 2015, "net_return": 0.10},
            {"symbol": "AUDUSD", "exit_year": 2016, "net_return": -0.05},
            {"symbol": "EURUSD", "exit_year": 2017, "net_return": 0.02},
            {"symbol": "GBPUSD", "exit_year": 2018, "net_return": -0.01},
            {"symbol": "USDJPY", "exit_year": 2019, "net_return": 0.03},
        ]
        out = concentration_diagnostics(trades)
        self.assertEqual(out["trade_count"], 5)
        self.assertEqual(out["pair"]["AUDUSD"]["trades"], 2)
        self.assertEqual(out["year"]["2017"]["trades"], 1)
        self.assertEqual(out["period_concentration"]["early_2015_2016"]["trades"], 2)
        self.assertEqual(out["period_concentration"]["middle_2017"]["trades"], 1)
        self.assertEqual(out["period_concentration"]["late_2018_2019"]["trades"], 2)
        self.assertEqual(out["trade_count_density_by_pair_year"]["USDJPY"]["2019"], 1)
        self.assertEqual(out["leave_one_year_out_reference_aggregation"]["2015"]["trades"], 4)
        self.assertEqual(out["leave_one_pair_out_reference_aggregation"]["AUDUSD"]["trades"], 3)
        self.assertFalse(out["strategy_selection_authority"])
        self.assertFalse(out["deletion_authority"])
        self.assertFalse(out["reweighting_authority"])

    def test_top_absolute_contribution_uses_absolute_magnitude(self):
        trades = []
        for i in range(100):
            trades.append({
                "symbol": "AUDUSD",
                "exit_year": 2015 + (i % 5),
                "net_return": -1.0 if i == 0 else 0.01,
            })
        out = concentration_diagnostics(trades)
        top1 = out["top_1_percent_absolute_net_return_contribution"]
        self.assertEqual(top1["selected_trade_count"], 1)
        self.assertEqual(top1["selected_signed_net_return"], -1.0)
        self.assertGreater(top1["share_of_total_abs_net_return"], 0.5)


if __name__ == "__main__":
    unittest.main()
