#!/usr/bin/env python3

import unittest

import rnd0035_concentration_diagnostics as frozen
from rnd0038_concentration_adapter import (
    FROZEN_YEARS,
    concentration_diagnostics_2015_2020,
)


class TestRND0038ConcentrationAdapter(unittest.TestCase):
    def _trade(self, symbol, year, value):
        return {
            "symbol": symbol,
            "exit_year": year,
            "exit_timestamp": f"{year}-06-01T12:00:00Z",
            "net_return": value,
        }

    def test_accepts_2020_and_restores_frozen_years(self):
        self.assertEqual(tuple(frozen.YEARS), FROZEN_YEARS)
        result = concentration_diagnostics_2015_2020([
            self._trade("AUDUSD", 2019, -0.01),
            self._trade("EURUSD", 2020, 0.02),
        ])
        self.assertEqual(result["year"]["2020"]["trades"], 1)
        self.assertEqual(tuple(frozen.YEARS), FROZEN_YEARS)

    def test_2015_2019_parity(self):
        trades = [
            self._trade("AUDUSD", 2015, -0.01),
            self._trade("EURUSD", 2016, 0.02),
            self._trade("GBPUSD", 2017, -0.03),
            self._trade("USDJPY", 2018, 0.04),
            self._trade("AUDUSD", 2019, -0.05),
        ]
        expected = frozen.concentration_diagnostics(trades)
        actual = concentration_diagnostics_2015_2020(trades)
        for key in (
            "trade_count", "pair", "top_1_percent_absolute_net_return_contribution",
            "top_5_percent_absolute_net_return_contribution", "leave_one_pair_out_reference_aggregation",
        ):
            self.assertEqual(actual[key], expected[key])
        for year in FROZEN_YEARS:
            self.assertEqual(actual["year"][str(year)], expected["year"][str(year)])
        self.assertEqual(tuple(frozen.YEARS), FROZEN_YEARS)

    def test_restores_guard_after_failure(self):
        with self.assertRaises(Exception):
            concentration_diagnostics_2015_2020([
                {"symbol": "AUDUSD", "exit_year": 2020, "net_return": float("nan")}
            ])
        self.assertEqual(tuple(frozen.YEARS), FROZEN_YEARS)


if __name__ == "__main__":
    unittest.main()
