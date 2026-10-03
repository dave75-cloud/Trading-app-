#!/usr/bin/env python3

import unittest
from pathlib import Path
from unittest.mock import patch

import rnd0035_development_runner as runner


class TestRND0035DevelopmentRunner(unittest.TestCase):
    def setUp(self):
        self.plan = runner.load_plan(runner.PLAN_PATH)

    def test_declared_strategy_trial_count_is_frozen_36(self):
        ids = runner.declared_strategy_trial_ids(self.plan)
        self.assertEqual(len(ids), 36)
        self.assertEqual(ids[0], "R000")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("A001", ids)
        self.assertIn("C004", ids)
        self.assertIn("D004", ids)
        self.assertIn("E002", ids)
        self.assertIn("F004", ids)

    def test_historical_outcomes_fail_closed_while_gate_closed(self):
        with self.assertRaisesRegex(
            runner.RND0035DevelopmentRunnerError, "execution gate remains closed"
        ):
            runner.historical_outcomes(self.plan, "a", "b", "c")

    def test_preflight_rejects_any_open_prohibited_authority(self):
        for key in ("validation_open", "final_test_open", "strategy_selection", "broker_writes", "capital_authority"):
            altered = dict(self.plan)
            altered[key] = True
            with self.subTest(key=key):
                with self.assertRaises(runner.RND0035DevelopmentRunnerError):
                    runner.preflight(altered, "a", "b", "c")

    @patch.object(runner, "_sha256", return_value="abc123")
    @patch.object(runner, "year_shards")
    @patch.object(runner, "verify_existing_shard", return_value=True)
    @patch.object(runner, "_json")
    def test_preflight_verifies_20_bound_shards_without_outcomes(
        self, mock_json, mock_verify, mock_year_shards, mock_sha
    ):
        mock_year_shards.return_value = [{"year": y} for y in runner.DEVELOPMENT_YEARS]

        r32 = {"per_symbol": {}}
        r33 = {"per_year": {str(y): {"per_symbol": {}} for y in runner.DEVELOPMENT_YEARS if y != 2015}}
        manifests = {}
        for symbol in self.plan["authorized_symbols"]:
            r32["per_symbol"][symbol] = {
                "raw_bundle_sha256": f"raw-{symbol}-2015",
                "canonical_rows_sha256": f"rows-{symbol}-2015",
                "standard_schedule_sha256": f"sched-{symbol}-2015",
                "row_count": 10,
            }
            for year in runner.DEVELOPMENT_YEARS:
                expected = r32["per_symbol"][symbol] if year == 2015 else {
                    "raw_bundle_sha256": f"raw-{symbol}-{year}",
                    "canonical_rows_sha256": f"rows-{symbol}-{year}",
                    "standard_schedule_sha256": f"sched-{symbol}-{year}",
                    "row_count": 10,
                }
                if year != 2015:
                    r33["per_year"][str(year)]["per_symbol"][symbol] = expected
                manifests[(symbol, year)] = {
                    "aggregate_raw_bundle_sha256": expected["raw_bundle_sha256"],
                    "canonical_rows_sha256": expected["canonical_rows_sha256"],
                    "standard_schedule_sha256": expected["standard_schedule_sha256"],
                    "row_count": expected["row_count"],
                }

        def json_side_effect(path):
            text = str(path)
            if text.endswith("OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"):
                return {"fixture": "acquisition"}
            if text.endswith("OANDA_CALENDAR_QUARANTINE_DECLARATION.json"):
                return {"fixture": "calendar"}
            if text.endswith("RND0032_CROSS_PAIR_2015_EVIDENCE_RECORD.json"):
                return r32
            if text.endswith("RND0033_DEVELOPMENT_HISTORY_EVIDENCE_RECORD.json"):
                return r33
            if text.endswith("quarantine_manifest.json"):
                p = Path(path)
                year = int(p.parent.name)
                symbol = p.parent.parent.name
                return manifests[(symbol, year)]
            raise AssertionError(f"unexpected json path: {path}")

        mock_json.side_effect = json_side_effect
        result = runner.preflight(self.plan, "/aud/2015", "/cross", "/development")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["verified_shards"], 20)
        self.assertEqual(result["evidence_identity_pass_match"], "20/20")
        self.assertEqual(result["declared_strategy_trial_count"], 36)
        self.assertFalse(result["historical_outcomes_generated"])
        self.assertFalse(result["outcome_gate_open"])
        self.assertFalse(result["validation_open"])
        self.assertFalse(result["final_test_open"])
        self.assertFalse(result["broker_writes"])
        self.assertFalse(result["capital_authority"])
        self.assertEqual(result["promotion_authority"], "HUMAN_ONLY")
        self.assertEqual(mock_verify.call_count, 20)


if __name__ == "__main__":
    unittest.main()
