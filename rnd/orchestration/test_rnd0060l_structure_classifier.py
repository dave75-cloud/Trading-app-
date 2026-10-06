#!/usr/bin/env python3
import unittest
from rnd0060h_cross_sectional_dispersion_state import SYMBOLS
from rnd0060l_activity_state_economic_utility import classify_observations


def _obs(year, state, primary, per_symbol=None, i=0):
    if per_symbol is None:
        per_symbol={s:primary for s in SYMBOLS}
    return {
        "timestamp_utc": f"{year}-01-{2+i:02d}T11:30:00Z",
        "year": year,
        "cross_sectional_dispersion_state": float(state),
        "market_wide_movement_to_friction_ratio": float(primary),
        "per_symbol_movement_to_friction_ratio": {s:float(per_symbol[s]) for s in SYMBOLS},
        "per_symbol_contemporaneous_relative_spread": {s:0.0002 for s in SYMBOLS},
        "per_symbol_forward_relative_realized_movement": {s:0.001 for s in SYMBOLS},
    }


def _passing():
    rows=[]
    for y in range(2015,2021):
        rows.extend([
            _obs(y,1,1,i=0),
            _obs(y,2,2,i=1),
            _obs(y,3,3,i=2),
            _obs(y,4,4,i=3),
        ])
    return rows


class RND0060LClassifierTests(unittest.TestCase):
    def test_01_passing_fixture_detects(self):
        self.assertEqual(classify_observations(_passing())["classification"],"ACTIVITY_STATE_ECONOMIC_UTILITY_DETECTED")

    def test_02_aggregate_threshold_failure_rejects(self):
        rows=_passing()
        # Symmetric 1,2,2,1 response against state 1,2,3,4 has zero
        # rank correlation. This isolates the frozen aggregate >= 0.05 gate.
        for r in rows:
            day=int(r["timestamp_utc"][8:10])
            r["market_wide_movement_to_friction_ratio"]=1.0 if day in (2,5) else 2.0
        self.assertEqual(classify_observations(rows)["classification"],"NO_REPRODUCIBLE_ACTIVITY_STATE_ECONOMIC_UTILITY")

    def test_03_annual_breadth_failure_rejects(self):
        rows=_passing()
        for r in rows:
            if r["year"] in (2015,2016,2017): r["market_wide_movement_to_friction_ratio"]*=-1.0
        self.assertFalse(classify_observations(rows)["criteria"]["at_least_4_of_6_annual_primary_spearman_positive"])

    def test_04_symbol_breadth_failure_rejects(self):
        rows=_passing()
        for r in rows:
            x=r["cross_sectional_dispersion_state"]
            r["per_symbol_movement_to_friction_ratio"]={"AUDUSD":-x,"EURUSD":-x,"GBPUSD":x,"USDJPY":-x}
        self.assertFalse(classify_observations(rows)["criteria"]["at_least_3_of_4_symbol_primary_spearman_positive"])

    def test_05_quartile_failure_rejects(self):
        rows=_passing()
        for r in rows: r["market_wide_movement_to_friction_ratio"]=-r["cross_sectional_dispersion_state"]
        self.assertFalse(classify_observations(rows)["criteria"]["top_quartile_mean_primary_response_gt_bottom_quartile"])

    def test_06_counts_preserved(self):
        out=classify_observations(_passing(),[{"reason":"X"}])
        self.assertEqual(out["eligible_observation_count"],24)
        self.assertEqual(out["excluded_market_day_count"],1)

    def test_07_positive_year_count_six(self):
        self.assertEqual(classify_observations(_passing())["positive_year_count"],6)

    def test_08_positive_symbol_count_four(self):
        self.assertEqual(classify_observations(_passing())["positive_symbol_count"],4)

    def test_09_governance_flags_closed(self):
        out=classify_observations(_passing())
        for k in ("trade_simulation","pnl","strategy_candidate","validation_open","final_test_open","reserved_final_access","prospective_candidate_outcomes_open","broker_writes","capital_authority","automatic_promotion"):
            self.assertFalse(out[k])

    def test_10_no_search_and_one_trial(self):
        out=classify_observations(_passing())
        self.assertEqual(out["declared_trial_count"],1)
        self.assertFalse(out["parameter_search"])
        self.assertFalse(out["threshold_search"])


if __name__=="__main__": unittest.main()
