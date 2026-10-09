import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from rnd0060r_prospective_confirmation_accumulator import (
    ADMIT, VETO, DEFER, CUTPOINT, POLICY_VERSION,
    RND0060RAccumulatorError, accumulate, frozen_decision, validate_observation,
)

START = "2026-10-10T00:00:00Z"


def rec(day=0, state=CUTPOINT, decision=ADMIT, source_kind="PROSPECTIVE_ACTIVITY_CONFIRMATION"):
    obs = datetime(2026, 10, 10, tzinfo=timezone.utc) + timedelta(days=day, hours=11, minutes=30)
    avail = obs + timedelta(minutes=30)
    return {
        "observation_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "available_at_utc": avail.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_kind": source_kind,
        "source_id": f"fixture-{day}",
        "policy_version": POLICY_VERSION,
        "activity_cutpoint": CUTPOINT,
        "activity_state": state,
        "decision": decision,
        "market_wide_movement_to_friction": 10.0,
        "per_symbol_movement_to_friction": {
            "AUDUSD": 10.0, "EURUSD": 11.0, "GBPUSD": 9.0, "USDJPY": 10.0,
        },
    }


class TestRND0060RAccumulator(unittest.TestCase):
    def test_01_boundary_state_admits(self):
        self.assertEqual(frozen_decision(CUTPOINT), ADMIT)

    def test_02_below_cutpoint_vetoes(self):
        self.assertEqual(frozen_decision(CUTPOINT - 1e-12), VETO)

    def test_03_missing_state_defers(self):
        self.assertEqual(frozen_decision(None), DEFER)

    def test_04_cutpoint_mismatch_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            frozen_decision(CUTPOINT, CUTPOINT + 1e-12)

    def test_05_pre_start_observation_rejected(self):
        r = rec()
        r["observation_utc"] = "2026-10-09T11:30:00Z"
        r["available_at_utc"] = "2026-10-09T12:00:00Z"
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(r, START)

    def test_06_early_availability_rejected(self):
        r = rec()
        r["available_at_utc"] = r["observation_utc"]
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(r, START)

    def test_07_historical_backfill_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(rec(source_kind="HISTORICAL_BACKFILL"), START)

    def test_08_consumed_validation_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(rec(source_kind="VALIDATION_2021_2022"), START)

    def test_09_reserved_final_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(rec(source_kind="RESERVED_FINAL_2023_2024"), START)

    def test_10_q003_outcome_source_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(rec(source_kind="Q003_PROSPECTIVE_OUTCOME"), START)

    def test_11_policy_version_mismatch_rejected(self):
        r = rec(); r["policy_version"] = "wrong"
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(r, START)

    def test_12_decision_mismatch_rejected(self):
        r = rec(state=CUTPOINT - 1e-6, decision=ADMIT)
        with self.assertRaises(RND0060RAccumulatorError):
            validate_observation(r, START)

    def test_13_duplicate_timestamp_rejected(self):
        a = rec(0); b = deepcopy(a); b["source_id"] = "other"
        with self.assertRaises(RND0060RAccumulatorError):
            accumulate([a, b], START)

    def test_14_out_of_order_rejected(self):
        with self.assertRaises(RND0060RAccumulatorError):
            accumulate([rec(2), rec(1)], START)

    def test_15_readout_locked_before_180_days(self):
        records = [rec(i) for i in range(100)]
        out = accumulate(records, START)
        self.assertFalse(out["readout_eligible"])
        self.assertFalse(out["economic_group_summary_exposed"])

    def test_16_readout_locked_below_100_non_defer(self):
        records = [rec(i) for i in range(99)]
        records.append(rec(180, state=None, decision=DEFER))
        out = accumulate(records, START)
        self.assertFalse(out["readout_eligible"])
        self.assertEqual(out["non_defer_count"], 99)

    def test_17_readout_eligible_only_when_both_conditions_met(self):
        records = [rec(i) for i in range(100)] + [rec(180)]
        out = accumulate(records, START)
        self.assertTrue(out["readout_eligible"])
        self.assertFalse(out["economic_group_summary_exposed"])

    def test_18_governance_remains_closed(self):
        out = accumulate([rec(0)], START)
        for key in (
            "trade_simulation", "pnl", "strategy_interaction", "validation_open",
            "final_test_open", "reserved_final_access", "q003_prospective_outcomes_open",
            "broker_writes", "capital_authority", "automatic_promotion",
        ):
            self.assertFalse(out[key])


if __name__ == "__main__":
    unittest.main()
