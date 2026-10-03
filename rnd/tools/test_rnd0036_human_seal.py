#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rnd0036_human_seal as mod


class TestRND0036HumanSeal(unittest.TestCase):
    def test_requires_explicit_literal_confirmation(self):
        with self.assertRaisesRegex(mod.RND0036HumanSealError, "explicit human seal"):
            mod.seal("/tmp/x", "/tmp/a", "/tmp/b", "NO")

    def test_seal_preserves_closed_authority_and_candidate_non_authority(self):
        seal_review = {
            "verified_shards": 4,
            "boundary_pass": True,
            "unresolved_symbols": list(mod.SYMBOLS),
            "per_symbol": {
                s: {
                    "row_count": 10,
                    "raw_bundle_sha256": "a" * 64,
                    "canonical_rows_sha256": "b" * 64,
                    "standard_schedule_sha256": "c" * 64,
                    "boundary_proof": {"boundary_status": "PASS"},
                }
                for s in mod.SYMBOLS
            },
        }
        classification = {
            "all_candidate_unexpected_zero": True,
            "shared_remaining_unexpected_timestamps": [],
            "per_symbol": {
                s: {
                    "candidate_unexpected_count": 0,
                    "boundary_status": "PASS",
                    "baseline_missing_count": 5,
                    "baseline_unexpected_count": 2,
                    "residual_short_gap_bars": 1,
                    "closure_shaped_candidate_bars": 4,
                    "unclassified_gap_bars": 0,
                }
                for s in mod.SYMBOLS
            },
        }
        with patch.object(mod, "_sha256_file", side_effect=[mod.SEAL_REVIEW_SHA256, mod.CLASSIFICATION_SHA256]), \
             patch.object(mod, "seal_review", return_value=seal_review), \
             patch.object(mod, "calendar_review", return_value=classification):
            out = mod.seal("/tmp/x", "/tmp/a", "/tmp/b", mod.CONFIRMATION)
        self.assertEqual(out["candidate_1700_authority"], "NONE")
        self.assertFalse(out["authoritative_standard_schedule_ledgers_resolved"])
        for key in (
            "strategy_evaluation", "validation_open", "final_test_open",
            "strategy_selection", "portfolio_sizing", "broker_writes",
            "capital_authority", "automatic_promotion", "automatic_merge",
        ):
            self.assertFalse(out["authority"][key])
        self.assertTrue(out["authority"]["human_seal_confirmed"])


if __name__ == "__main__":
    unittest.main()
