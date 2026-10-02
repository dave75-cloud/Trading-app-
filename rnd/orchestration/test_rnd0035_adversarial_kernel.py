#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import unittest

from gap_aware_m005_reconstruction import reconstruct_pair
from rnd0035_adversarial_kernel import (
    D_BPS,
    RND0035KernelError,
    run_trial_pair,
    trial_configuration,
)


def rows(count, start="2019-01-02T07:00:00Z", gap_after=None):
    dt = datetime.fromisoformat(start[:-1] + "+00:00")
    price = 1.0
    out = []
    for i in range(count):
        if gap_after is not None and i == gap_after:
            dt += timedelta(minutes=10)
        price *= 1.0015 if i % 2 == 0 else 1.0002
        spread = price * 0.0001
        out.append({
            "timestamp_utc": dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": f"{price - spread / 2:.9f}",
            "ask_close": f"{price + spread / 2:.9f}",
            "mid_close": f"{price:.9f}",
        })
        dt += timedelta(minutes=5)
    return out


class RND0035AdversarialKernelTests(unittest.TestCase):
    def test_r000_delegates_exactly_to_rnd0034(self):
        value = rows(90)
        self.assertEqual(
            reconstruct_pair("AUDUSD", value),
            run_trial_pair("R000", "AUDUSD", value),
        )

    def test_local_parameter_trial_changes_only_declared_field(self):
        config = trial_configuration("A001")
        self.assertEqual(16, config["fast_ma"])
        self.assertEqual(50, config["slow_ma"])
        self.assertEqual(12, config["volatility_window"])
        self.assertEqual(0.0005, config["volatility_threshold"])

    def test_signal_delay_variants_are_frozen(self):
        self.assertEqual(2, trial_configuration("A017")["signal_delay_observed_bars"])
        self.assertEqual(3, trial_configuration("A018")["signal_delay_observed_bars"])

    def test_session_transforms_are_exact_and_global(self):
        minus = trial_configuration("C001")["sessions_utc"]
        plus = trial_configuration("C002")["sessions_utc"]
        self.assertEqual((10, 13), minus["AUDUSD"])
        self.assertEqual((10, 12), minus["GBPUSD"])
        self.assertEqual((12, 15), plus["AUDUSD"])
        self.assertEqual((12, 14), plus["USDJPY"])

    def test_cost_stress_is_monotonically_adverse_per_trade(self):
        value = rows(90)
        reference = run_trial_pair("R000", "AUDUSD", value)
        stressed = run_trial_pair("D001", "AUDUSD", value)
        self.assertEqual(reference["completed_trade_count"], stressed["completed_trade_count"])
        self.assertGreater(reference["completed_trade_count"], 0)
        expected = D_BPS["D001"] / 10000.0
        for before, after in zip(reference["trades"], stressed["trades"]):
            self.assertAlmostEqual(before["net_return"] - expected, after["net_return"])
            self.assertGreater(after["execution_cost_drag"], before["execution_cost_drag"])

    def test_more_cost_stress_cannot_improve_trade_net_return(self):
        value = rows(90)
        low = run_trial_pair("D001", "AUDUSD", value)
        high = run_trial_pair("D004", "AUDUSD", value)
        for a, b in zip(low["trades"], high["trades"]):
            self.assertGreater(a["net_return"], b["net_return"])

    def test_gap_still_resets_parameterized_strategy_state(self):
        result = run_trial_pair("A001", "AUDUSD", rows(70, gap_after=56))
        self.assertEqual(1, result["gap_count"])
        reset = [x for x in result["events"] if x["event_type"] == "STRATEGY_RESET"]
        self.assertEqual(1, len(reset))

    def test_sensitive_e_and_f_families_remain_fail_closed(self):
        for trial_id in ("E001", "E002", "F001", "F004"):
            with self.subTest(trial_id=trial_id):
                with self.assertRaisesRegex(RND0035KernelError, "not executable"):
                    trial_configuration(trial_id)

    def test_undeclared_trial_fails_closed(self):
        with self.assertRaisesRegex(RND0035KernelError, "undeclared"):
            trial_configuration("A999")

    def test_authority_remains_closed_for_parameterized_trial(self):
        result = run_trial_pair("A001", "AUDUSD", rows(90))
        authority = result["authority"]
        self.assertFalse(authority["broker_writes"])
        self.assertFalse(authority["capital_authority"])
        self.assertFalse(authority["automatic_promotion"])
        self.assertFalse(authority["validation_open"])
        self.assertFalse(authority["final_test_open"])
        self.assertTrue(authority["human_review_required"])


if __name__ == "__main__":
    unittest.main()
