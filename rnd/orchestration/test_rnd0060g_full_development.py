#!/usr/bin/env python3
import copy
import unittest

from rnd0060g_volatility_state_persistence import RND0060GError, SYMBOLS, classify

YEARS = (2015, 2016, 2017, 2018, 2019, 2020)


def _observations(direction_by_year=None):
    direction_by_year = direction_by_year or {y: 1 for y in YEARS}
    rows = []
    for year in YEARS:
        direction = direction_by_year[year]
        for i, state in enumerate((1.0, 2.0, 3.0, 4.0)):
            response = state if direction > 0 else 5.0 - state
            rows.append({
                "year": year,
                "timestamp_utc": f"{year}-01-{i + 2:02d}T11:30:00Z",
                "volatility_state_ratio": state,
                "forward_realized_mid_range": response * 0.001,
            })
    return rows


def _symbol_result(symbol, primary=0.2, top=0.004, bottom=0.001, observations=None):
    return {
        "symbol": symbol,
        "primary_spearman_volatility_state_vs_forward_range": primary,
        "quartile_diagnostic": {
            "quartile_size": 6,
            "bottom_quartile_mean_forward_realized_mid_range": bottom,
            "top_quartile_mean_forward_realized_mid_range": top,
        },
        "observations": list(observations if observations is not None else _observations()),
    }


def _passing_set():
    return {s: _symbol_result(s) for s in SYMBOLS}


class RND0060GClassifierTests(unittest.TestCase):
    def test_01_passing_fixture_detects_structure(self):
        out = classify(_passing_set())
        self.assertEqual(out["classification"], "MARKET_STATE_STRUCTURE_DETECTED")
        self.assertTrue(all(out["criteria"].values()))

    def test_02_requires_exact_four_symbols(self):
        data = _passing_set()
        del data["USDJPY"]
        with self.assertRaises(RND0060GError):
            classify(data)

    def test_03_symbol_sign_requirement_can_fail(self):
        data = _passing_set()
        data["AUDUSD"]["primary_spearman_volatility_state_vs_forward_range"] = -0.1
        data["EURUSD"]["primary_spearman_volatility_state_vs_forward_range"] = -0.1
        out = classify(data)
        self.assertFalse(out["criteria"]["at_least_3_of_4_symbol_primary_spearman_positive"])
        self.assertEqual(out["classification"], "NO_REPRODUCIBLE_STRUCTURE")

    def test_04_quartile_requirement_can_fail(self):
        data = _passing_set()
        for symbol in ("AUDUSD", "EURUSD"):
            data[symbol]["quartile_diagnostic"] = {
                "quartile_size": 6,
                "bottom_quartile_mean_forward_realized_mid_range": 0.004,
                "top_quartile_mean_forward_realized_mid_range": 0.001,
            }
        out = classify(data)
        self.assertFalse(out["criteria"]["at_least_3_of_4_symbol_top_quartile_mean_range_gt_bottom_quartile"])
        self.assertEqual(out["classification"], "NO_REPRODUCIBLE_STRUCTURE")

    def test_05_annual_requirement_can_fail(self):
        direction = {2015: -1, 2016: -1, 2017: -1, 2018: 1, 2019: 1, 2020: 1}
        data = {s: _symbol_result(s, observations=_observations(direction)) for s in SYMBOLS}
        out = classify(data)
        self.assertEqual(out["positive_year_count"], 3)
        self.assertFalse(out["criteria"]["at_least_4_of_6_annual_pooled_primary_spearman_positive"])
        self.assertEqual(out["classification"], "NO_REPRODUCIBLE_STRUCTURE")

    def test_06_aggregate_effect_requirement_can_fail(self):
        direction = {y: -1 for y in YEARS}
        data = {s: _symbol_result(s, observations=_observations(direction)) for s in SYMBOLS}
        out = classify(data)
        self.assertLess(out["aggregate_primary_spearman"], 0.05)
        self.assertFalse(out["criteria"]["aggregate_primary_spearman_gte_0_05"])
        self.assertEqual(out["classification"], "NO_REPRODUCIBLE_STRUCTURE")

    def test_07_passing_fixture_counts_all_symbols_and_years_positive(self):
        out = classify(_passing_set())
        self.assertEqual(out["symbol_primary_positive_count"], 4)
        self.assertEqual(out["quartile_positive_count"], 4)
        self.assertEqual(out["positive_year_count"], 6)

    def test_08_integrity_criterion_is_explicit(self):
        out = classify(_passing_set())
        self.assertIs(out["criteria"]["integrity_reconciliation_pass"], True)

    def test_09_classifier_never_creates_strategy_authority(self):
        out = classify(_passing_set())
        self.assertFalse(out["trade_simulation"])
        self.assertFalse(out["pnl"])
        self.assertFalse(out["strategy_candidate"])
        self.assertFalse(out["validation_open"])
        self.assertFalse(out["final_test_open"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])

    def test_10_input_is_not_mutated(self):
        data = _passing_set()
        before = copy.deepcopy(data)
        classify(data)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
