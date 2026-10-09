import math
import unittest
from datetime import datetime, timedelta, timezone

from rnd0060t_cross_pair_lead_lag import (
    SYMBOLS, ORIENTATION, RND0060TError, extract_observations,
    classify_observations, spearman,
)


class RND0060THostileFixtures(unittest.TestCase):
    def _row(self, dt, mid, complete=True):
        return {"timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "complete": complete, "mid_close": mid}

    def _market_rows(self, days=2):
        rows = {s: [] for s in SYMBOLS}
        base_day = datetime(2015, 1, 5, tzinfo=timezone.utc)
        bases = {"AUDUSD": 1.0, "EURUSD": 1.2, "GBPUSD": 1.5, "USDJPY": 100.0}
        for d in range(days):
            day = base_day + timedelta(days=d)
            while day.weekday() >= 5:
                day += timedelta(days=1)
            for s in SYMBOLS:
                b = bases[s]
                # 11:00, 11:30, 12:00 are sufficient for frozen close-to-close returns.
                vals = [b * (1 + 0.001 * d), b * (1 + 0.001 * d + 0.0002 * (d + 1)), b * (1 + 0.001 * d + 0.00035 * (d + 1))]
                for minute, val in zip((0, 30, 60), vals):
                    dt = day.replace(hour=11, minute=0) + timedelta(minutes=minute)
                    rows[s].append(self._row(dt, val))
        return rows

    def _obs(self, year, i, flip=None):
        # Four relationships increase monotonically unless explicitly flipped.
        eu = float(i)
        pac = float(i) + 0.25
        targets = {
            "AUDUSD": float(i),
            "USDJPY": float(i) + 0.1,
            "EURUSD": float(i) + 0.2,
            "GBPUSD": float(i) + 0.3,
        }
        if flip:
            targets[flip] = -float(i)
        return {
            "timestamp_utc": f"{year}-01-{i:02d}T11:30:00Z",
            "year": year,
            "leaders": {"EUROPEAN": eu, "PACIFIC": pac},
            "targets": targets,
            "current_usd_oriented_returns": {},
            "forward_usd_oriented_returns": {},
        }

    def _positive_dataset(self):
        out = []
        for year in range(2015, 2021):
            out.extend([self._obs(year, 2), self._obs(year, 3), self._obs(year, 4)])
        return out

    def test_01_spearman_positive_monotonic(self):
        self.assertAlmostEqual(spearman([1,2,3,4], [10,20,30,40]), 1.0)

    def test_02_spearman_negative_monotonic(self):
        self.assertAlmostEqual(spearman([1,2,3,4], [40,30,20,10]), -1.0)

    def test_03_exact_four_symbol_set_required(self):
        rows = self._market_rows()
        del rows["USDJPY"]
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_04_incomplete_candle_rejected(self):
        rows = self._market_rows()
        rows["AUDUSD"][0]["complete"] = False
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_05_nonpositive_mid_rejected(self):
        rows = self._market_rows()
        rows["EURUSD"][0]["mid_close"] = 0.0
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_06_duplicate_timestamp_rejected(self):
        rows = self._market_rows()
        rows["GBPUSD"].insert(1, dict(rows["GBPUSD"][0]))
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_07_out_of_order_timestamp_rejected(self):
        rows = self._market_rows()
        rows["USDJPY"][0], rows["USDJPY"][1] = rows["USDJPY"][1], rows["USDJPY"][0]
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_08_non_development_year_rejected(self):
        rows = self._market_rows()
        rows["AUDUSD"][0]["timestamp_utc"] = "2021-01-05T11:00:00Z"
        with self.assertRaises(RND0060TError):
            extract_observations(rows)

    def test_09_missing_required_endpoint_excludes_day(self):
        rows = self._market_rows(days=2)
        rows["EURUSD"] = [r for r in rows["EURUSD"] if r["timestamp_utc"] != "2015-01-05T12:00:00Z"]
        out = extract_observations(rows)
        self.assertEqual(len(out["exclusions"]), 1)
        self.assertEqual(out["exclusions"][0]["reason"], "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING")

    def test_10_usd_orientation_is_frozen(self):
        self.assertEqual(ORIENTATION, {"AUDUSD":-1.0,"EURUSD":-1.0,"GBPUSD":-1.0,"USDJPY":1.0})

    def test_11_classifier_detects_clean_positive_fixture(self):
        result = classify_observations(self._positive_dataset())
        self.assertEqual(result["classification"], "CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE_DETECTED")
        self.assertEqual(result["positive_year_count"], 6)
        self.assertEqual(result["positive_relationship_count"], 4)

    def test_12_aggregate_threshold_failure_rejects(self):
        obs = self._positive_dataset()
        # Reverse all targets to force negative aggregate.
        for r in obs:
            for k in r["targets"]:
                r["targets"][k] *= -1.0
        result = classify_observations(obs)
        self.assertEqual(result["classification"], "NO_REPRODUCIBLE_CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE")
        self.assertFalse(result["criteria"]["aggregate_primary_gte_0_05"])

    def test_13_relationship_breadth_failure_rejects(self):
        obs = []
        for year in range(2015, 2021):
            for i in (2,3,4):
                r = self._obs(year, i)
                r["targets"]["AUDUSD"] *= -1
                r["targets"]["USDJPY"] *= -1
                obs.append(r)
        result = classify_observations(obs)
        self.assertLess(result["positive_relationship_count"], 3)
        self.assertEqual(result["classification"], "NO_REPRODUCIBLE_CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE")

    def test_14_annual_breadth_failure_rejects(self):
        obs = []
        for year in range(2015, 2021):
            for i in (2,3,4):
                r = self._obs(year, i)
                if year in (2015, 2016, 2017):
                    for k in r["targets"]:
                        r["targets"][k] *= -1
                obs.append(r)
        result = classify_observations(obs)
        self.assertLess(result["positive_year_count"], 4)
        self.assertEqual(result["classification"], "NO_REPRODUCIBLE_CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE")

    def test_15_constant_input_correlation_rejected(self):
        with self.assertRaises(RND0060TError):
            spearman([1,1,1], [1,2,3])

    def test_16_classifier_requires_all_six_years(self):
        obs = [r for r in self._positive_dataset() if r["year"] != 2020]
        with self.assertRaises(RND0060TError):
            classify_observations(obs)

    def test_17_governance_flags_remain_closed(self):
        result = classify_observations(self._positive_dataset())
        for key in ("parameter_search","threshold_search","trade_simulation","pnl","strategy_candidate","q003_reference","activity_state_directional_input","validation_open","final_test_open","reserved_final_access","broker_writes","capital_authority","automatic_promotion"):
            self.assertFalse(result[key], key)
        self.assertEqual(result["trial_count"], 1)

    def test_18_no_relationship_dropping_in_output(self):
        result = classify_observations(self._positive_dataset())
        self.assertEqual(set(result["relationship_correlations"]), {
            "EU_TO_AUDUSD", "EU_TO_USDJPY", "PACIFIC_TO_EURUSD", "PACIFIC_TO_GBPUSD"
        })


if __name__ == "__main__":
    unittest.main()
