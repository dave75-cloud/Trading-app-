#!/usr/bin/env python3
import unittest

from rnd0060n_activity_admissibility_contract import (
    RND0060NError,
    evaluate_admissibility,
)


class RND0060NContractTests(unittest.TestCase):
    def _call(self, **overrides):
        args = {
            "symbol": "EURUSD",
            "direction": 1,
            "activity_state": 0.001,
            "activity_policy_decision": "ADMIT",
            "direction_source_id": "INDEPENDENT_DIRECTIONAL_MODEL_A",
            "signal_metadata": {"tag": "fixture", "score": 0.42},
        }
        args.update(overrides)
        return evaluate_admissibility(**args)

    def test_01_admit_preserves_long(self):
        out = self._call(direction=1, activity_policy_decision="ADMIT")
        self.assertEqual(out["effective_direction_now"], 1)
        self.assertIsNone(out["deferred_direction"])

    def test_02_admit_preserves_short(self):
        out = self._call(direction=-1, activity_policy_decision="ADMIT")
        self.assertEqual(out["effective_direction_now"], -1)
        self.assertIsNone(out["deferred_direction"])

    def test_03_zero_signal_never_becomes_exposure(self):
        for policy in ("ADMIT", "VETO", "DEFER"):
            out = self._call(direction=0, activity_policy_decision=policy)
            self.assertEqual(out["effective_direction_now"], 0)
            self.assertIsNone(out["deferred_direction"])

    def test_04_veto_only_suppresses(self):
        for direction in (-1, 1):
            out = self._call(direction=direction, activity_policy_decision="VETO")
            self.assertEqual(out["effective_direction_now"], 0)
            self.assertIsNone(out["deferred_direction"])
            self.assertEqual(out["input_direction"], direction)

    def test_05_defer_only_postpones(self):
        for direction in (-1, 1):
            out = self._call(direction=direction, activity_policy_decision="DEFER")
            self.assertEqual(out["effective_direction_now"], 0)
            self.assertEqual(out["deferred_direction"], direction)

    def test_06_metadata_passed_through_without_alias(self):
        meta = {"nested": {"x": 1}}
        out = self._call(signal_metadata=meta)
        self.assertEqual(out["signal_metadata"], meta)
        self.assertIsNot(out["signal_metadata"], meta)
        meta["nested"]["x"] = 9
        self.assertEqual(out["signal_metadata"]["nested"]["x"], 1)

    def test_07_unsupported_symbol_rejected(self):
        with self.assertRaises(RND0060NError):
            self._call(symbol="NZDUSD")

    def test_08_malformed_direction_rejected(self):
        for value in (2, -2, 0.5, True, "long"):
            with self.assertRaises(RND0060NError):
                self._call(direction=value)

    def test_09_malformed_policy_rejected(self):
        for value in ("BUY", "ALLOW", "", None):
            with self.assertRaises(RND0060NError):
                self._call(activity_policy_decision=value)

    def test_10_invalid_activity_state_rejected(self):
        for value in (0, -1, float("inf"), float("nan"), True, "x"):
            with self.assertRaises(RND0060NError):
                self._call(activity_state=value)

    def test_11_missing_direction_provenance_rejected(self):
        for value in ("", "   ", None):
            with self.assertRaises(RND0060NError):
                self._call(direction_source_id=value)

    def test_12_activity_research_cannot_be_direction_source(self):
        for value in ("RND0060H", "rnd0060l-derived", "MODEL_FROM_0060H"):
            with self.assertRaises(RND0060NError):
                self._call(direction_source_id=value)

    def test_13_activity_never_creates_or_reverses_direction(self):
        for policy in ("ADMIT", "VETO", "DEFER"):
            for direction in (-1, 0, 1):
                out = self._call(direction=direction, activity_policy_decision=policy)
                self.assertFalse(out["direction_created_by_activity"])
                self.assertFalse(out["direction_reversed_by_activity"])
                self.assertNotEqual(out["effective_direction_now"], -direction if direction else 99)

    def test_14_governance_and_authority_flags_closed(self):
        out = self._call()
        for key in (
            "quantity_assigned", "position_sizing", "threshold_selected",
            "threshold_search", "trade_simulation", "pnl", "strategy_candidate",
            "validation_open", "final_test_open", "reserved_final_access",
            "prospective_candidate_outcomes_open", "broker_writes",
            "capital_authority", "automatic_promotion", "automatic_merge",
        ):
            self.assertFalse(out[key])


if __name__ == "__main__":
    unittest.main()
