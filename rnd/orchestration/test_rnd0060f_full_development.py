#!/usr/bin/env python3
from __future__ import annotations

import unittest

from rnd0060f_spread_state_structure import SYMBOLS, classify


def _obs(symbol, year, state, response):
    return {
        "symbol": symbol,
        "timestamp_utc": f"{year}-01-02T11:30:00Z",
        "year": year,
        "current_relative_spread": state,
        "baseline_median_relative_spread": 1.0,
        "spread_state_ratio": state,
        "forward_absolute_close_return": response,
        "forward_realized_mid_range": response,
    }


def _symbol_result(symbol, sign=1):
    observations = []
    for year in range(2015, 2021):
        for i in range(1, 5):
            state = float(i)
            response = float(i if sign > 0 else 5 - i)
            observations.append(_obs(symbol, year, state, response))
    top = 4.0 if sign > 0 else 1.0
    bottom = 1.0 if sign > 0 else 4.0
    return {
        "symbol": symbol,
        "primary_spearman_spread_state_vs_forward_range": 1.0 if sign > 0 else -1.0,
        "secondary_spearman_spread_state_vs_forward_absolute_close_return": 1.0 if sign > 0 else -1.0,
        "quartile_diagnostic": {
            "quartile_size": 6,
            "bottom_quartile_mean_forward_realized_mid_range": bottom,
            "top_quartile_mean_forward_realized_mid_range": top,
        },
        "observations": observations,
    }


class TestRND0060FFullDevelopmentClassifier(unittest.TestCase):
    def test_all_positive_detects_structure(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertEqual(out["classification"], "MARKET_STATE_STRUCTURE_DETECTED")

    def test_two_negative_symbols_fails_symbol_count(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        per["AUDUSD"] = _symbol_result("AUDUSD", -1)
        per["EURUSD"] = _symbol_result("EURUSD", -1)
        out = classify(per)
        self.assertFalse(out["criteria"]["at_least_3_of_4_symbol_primary_spearman_positive"])
        self.assertEqual(out["classification"], "NO_REPRODUCIBLE_STRUCTURE")

    def test_wrong_symbol_set_rejected(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS[:-1]}
        with self.assertRaises(Exception):
            classify(per)

    def test_no_trade_authority(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertFalse(out["trade_simulation"])
        self.assertFalse(out["pnl"])
        self.assertFalse(out["strategy_candidate"])

    def test_no_validation_or_broker_authority(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertFalse(out["validation_open"])
        self.assertFalse(out["final_test_open"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])

    def test_positive_year_count_is_six_for_positive_fixture(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertEqual(out["positive_year_count"], 6)

    def test_aggregate_primary_is_positive_for_positive_fixture(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertGreaterEqual(out["aggregate_primary_spearman"], 0.05)

    def test_quartile_positive_count_is_four(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        out = classify(per)
        self.assertEqual(out["quartile_positive_count"], 4)

    def test_one_negative_symbol_can_still_pass_symbol_and_quartile_counts(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        per["USDJPY"] = _symbol_result("USDJPY", -1)
        out = classify(per)
        self.assertTrue(out["criteria"]["at_least_3_of_4_symbol_primary_spearman_positive"])
        self.assertTrue(out["criteria"]["at_least_3_of_4_symbol_top_quartile_mean_range_gt_bottom_quartile"])

    def test_classification_values_are_closed(self):
        per = {s: _symbol_result(s, 1) for s in SYMBOLS}
        self.assertIn(classify(per)["classification"], {"MARKET_STATE_STRUCTURE_DETECTED", "NO_REPRODUCIBLE_STRUCTURE"})


if __name__ == "__main__":
    unittest.main()
