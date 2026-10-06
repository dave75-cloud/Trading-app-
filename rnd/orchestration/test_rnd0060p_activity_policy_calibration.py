import math
import unittest

from rnd0060p_activity_policy_calibration import (
    ADMIT,
    DEFER,
    VETO,
    RND0060PCalibrationError,
    calibrate,
    decide,
    empirical_median,
)


class TestRND0060PActivityPolicyCalibration(unittest.TestCase):
    def test_01_odd_length_median(self):
        self.assertEqual(empirical_median([3.0, 1.0, 2.0]), 2.0)

    def test_02_even_length_median(self):
        self.assertEqual(empirical_median([4.0, 1.0, 2.0, 3.0]), 2.5)

    def test_03_order_independence(self):
        a = empirical_median([0.4, 0.1, 0.3, 0.2])
        b = empirical_median([0.2, 0.3, 0.1, 0.4])
        self.assertEqual(a, b)

    def test_04_duplicate_values(self):
        self.assertEqual(empirical_median([1.0, 1.0, 1.0, 2.0]), 1.0)

    def test_05_equality_is_admit(self):
        self.assertEqual(decide(1.25, 1.25), ADMIT)

    def test_06_below_is_veto(self):
        self.assertEqual(decide(1.249, 1.25), VETO)

    def test_07_above_is_admit(self):
        self.assertEqual(decide(1.251, 1.25), ADMIT)

    def test_08_missing_state_defers(self):
        self.assertEqual(decide(None, 1.25), DEFER)

    def test_09_non_finite_state_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(RND0060PCalibrationError):
                    decide(value, 1.25)

    def test_10_non_finite_cutpoint_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(RND0060PCalibrationError):
                    decide(1.25, value)

    def test_11_empty_sample_rejected(self):
        with self.assertRaises(RND0060PCalibrationError):
            empirical_median([])

    def test_12_no_alternate_quantile_parameter(self):
        with self.assertRaises(TypeError):
            calibrate([1.0, 2.0, 3.0], quantile=0.75)

    def test_13_no_objective_or_outcome_argument(self):
        with self.assertRaises(TypeError):
            calibrate([1.0, 2.0, 3.0], pnl=[1.0, -1.0, 2.0])

    def test_14_output_contains_no_strategy_or_authority(self):
        out = calibrate([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(out["calibration_method"], "EMPIRICAL_MEDIAN")
        self.assertEqual(out["activity_cutpoint"], 2.5)
        self.assertFalse(out["threshold_search"])
        self.assertFalse(out["parameter_search"])
        self.assertFalse(out["trade_simulation"])
        self.assertFalse(out["pnl"])
        self.assertFalse(out["strategy_candidate"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])
        forbidden = {
            "direction", "signal", "position_size", "trades", "equity",
            "drawdown", "win_rate", "validation_open", "final_test_open",
        }
        self.assertTrue(forbidden.isdisjoint(out.keys()))


if __name__ == "__main__":
    unittest.main()
