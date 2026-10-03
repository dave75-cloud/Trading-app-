#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rnd0037_development_assembly as mod


class TestRND0037DevelopmentAssembly(unittest.TestCase):
    def test_assembly_requires_24_identity_verified_pair_years_and_keeps_authority_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seal = root / "seal.json"
            seal.write_text("{}", encoding="utf-8")
            digest = mod._sha256_file(seal)
            receipt = {
                "task_id": "RND-0036",
                "status": "HUMAN_EVIDENCE_SEAL_COMPLETE",
                "boundary_pass": True,
                "report_sha256": digest,
                "strategy_evaluation": False,
                "validation_open": False,
                "final_test_open": False,
                "broker_writes": False,
                "capital_authority": False,
                "strategy_selection": False,
            }
            manifest = {
                "row_count": 10,
                "aggregate_raw_bundle_sha256": "a" * 64,
                "canonical_rows_sha256": "b" * 64,
                "standard_schedule_sha256": "c" * 64,
            }
            plan = {"validation_open": False, "final_test_open": False}
            proof = {"rows_at_or_after_validation_boundary": 0, "boundary_status": "PASS"}

            def fake_json(path):
                if Path(path) == mod.SEAL_RECEIPT:
                    return receipt
                return manifest

            with patch.object(mod, "load_plan", return_value=plan), \
                 patch.object(mod, "_verify_evidence", return_value=([{"id": i} for i in range(20)], 20, None)), \
                 patch.object(mod, "_json", side_effect=fake_json), \
                 patch.object(mod, "verify_existing_shard", return_value=True), \
                 patch.object(mod, "boundary_proof", return_value=proof):
                out = mod.assemble("a", "b", "c", root, seal)

            self.assertEqual(out["pair_year_count"], 24)
            self.assertTrue(out["full_development_structural_evidence_complete"])
            self.assertEqual(out["evidence_2015_2019"]["verified_pair_years"], 20)
            self.assertEqual(out["evidence_2020"]["verified_pair_years"], 4)
            for key in (
                "strategy_evaluation", "validation_open", "final_test_open",
                "strategy_selection", "portfolio_sizing", "broker_writes",
                "capital_authority", "automatic_promotion", "automatic_merge",
            ):
                self.assertFalse(out[key])

    def test_rejects_if_prior_identity_verification_not_20_of_20(self):
        with patch.object(mod, "load_plan", return_value={"validation_open": False, "final_test_open": False}), \
             patch.object(mod, "_verify_evidence", return_value=([], 19, None)):
            with self.assertRaisesRegex(mod.RND0037AssemblyError, "20/20"):
                mod.assemble("a", "b", "c", "d", "e")


if __name__ == "__main__":
    unittest.main()
