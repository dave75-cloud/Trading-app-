#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

from historical_evidence_falsification import (
    EXPECTED_M005_BEHAVIOUR,
    HistoricalEvidenceError,
    classify_ambiguous_bar,
    clipping_counterfactual,
    m005_performance_gate,
    overlapping_trade_pairs,
    validate_chronological_windows,
    validate_evidence_ledger,
)


def ledger():
    return {
        "contract_version": "RND-historical-evidence-ledger-v0.1",
        "base_commit": "a" * 40,
        "claims": [
            {
                "claim_id": "A",
                "status": "REPRODUCIBLE",
                "claim": "A code recipe survives.",
                "evidence": [{"path": "x.py", "git_blob": "b" * 40}],
            },
            {
                "claim_id": "B",
                "status": "UNREPRODUCIBLE",
                "claim": "Performance inputs are absent.",
                "evidence": [],
                "missing": ["input.csv"],
            },
        ],
    }


def windows():
    return {
        "development": {
            "start_utc": "2020-01-01T00:00:00Z",
            "end_utc": "2021-01-01T00:00:00Z",
        },
        "validation": {
            "start_utc": "2021-01-01T00:00:00Z",
            "end_utc": "2022-01-01T00:00:00Z",
        },
        "test": {
            "start_utc": "2022-01-01T00:00:00Z",
            "end_utc": "2023-01-01T00:00:00Z",
        },
    }


class HistoricalEvidenceTests(unittest.TestCase):
    def test_valid_ledger(self):
        self.assertTrue(validate_evidence_ledger(ledger()))

    def test_reproducible_claim_requires_evidence(self):
        value = ledger()
        value["claims"][0]["evidence"] = []
        with self.assertRaisesRegex(HistoricalEvidenceError, "requires"):
            validate_evidence_ledger(value)

    def test_unreproducible_claim_requires_missing_evidence(self):
        value = ledger()
        del value["claims"][1]["missing"]
        with self.assertRaisesRegex(HistoricalEvidenceError, "identify missing"):
            validate_evidence_ledger(value)

    def test_clipping_mechanically_inflates_crossing_loss(self):
        result = clipping_counterfactual([0.002, -0.004, 0.001], 5.0, 0.005)
        self.assertEqual(result["affected_trades"], 1)
        self.assertGreater(
            result["clipped_final_equity"], result["raw_final_equity"]
        )
        self.assertFalse(result["executable_stop_loss_evidence"])

    def test_clipping_has_no_effect_when_floor_not_crossed(self):
        result = clipping_counterfactual([0.0002, -0.0002], 5.0, 0.005)
        self.assertEqual(result["affected_trades"], 0)
        self.assertAlmostEqual(
            result["clipped_final_equity"], result["raw_final_equity"]
        )

    def test_chronological_windows_accept_touching_boundaries(self):
        self.assertTrue(validate_chronological_windows(windows()))

    def test_temporal_contamination_is_rejected(self):
        value = windows()
        value["development"]["end_utc"] = "2021-06-01T00:00:00Z"
        with self.assertRaisesRegex(HistoricalEvidenceError, "contamination"):
            validate_chronological_windows(value)

    def test_overlapping_trades_are_detected(self):
        trades = [
            {
                "trade_id": "A",
                "entry_utc": "2025-01-01T00:00:00Z",
                "exit_utc": "2025-01-01T01:00:00Z",
            },
            {
                "trade_id": "B",
                "entry_utc": "2025-01-01T00:30:00Z",
                "exit_utc": "2025-01-01T02:00:00Z",
            },
        ]
        self.assertEqual(overlapping_trade_pairs(trades), [("A", "B")])

    def test_nonoverlapping_trades_are_not_flagged(self):
        trades = [
            {
                "trade_id": "A",
                "entry_utc": "2025-01-01T00:00:00Z",
                "exit_utc": "2025-01-01T01:00:00Z",
            },
            {
                "trade_id": "B",
                "entry_utc": "2025-01-01T01:00:00Z",
                "exit_utc": "2025-01-01T02:00:00Z",
            },
        ]
        self.assertEqual(overlapping_trade_pairs(trades), [])

    def test_ambiguous_long_bar_fails_closed(self):
        self.assertEqual(
            classify_ambiguous_bar(1.02, 0.98, 0.99, 1.01, "long"),
            "AMBIGUOUS",
        )

    def test_ambiguous_short_bar_fails_closed(self):
        self.assertEqual(
            classify_ambiguous_bar(1.02, 0.98, 1.01, 0.99, "short"),
            "AMBIGUOUS",
        )

    def test_repository_ledger_is_structurally_valid(self):
        root = Path(__file__).resolve().parents[1]
        value = json.loads(
            (root / "research" / "HISTORICAL_EVIDENCE_LEDGER.json").read_text()
        )
        self.assertTrue(validate_evidence_ledger(value))

    def test_repository_m005_gap_report_is_blocked(self):
        root = Path(__file__).resolve().parents[1]
        value = json.loads(
            (root / "research" / "M005_EVIDENCE_GAPS.json").read_text()
        )
        result = m005_performance_gate(value)
        self.assertFalse(result["performance_declaration_allowed"])

    def test_m005_gap_report_cannot_grant_performance_authority(self):
        report = {
            "contract_version": "RND-m005-evidence-gap-v0.1",
            "task_id": "RND-0026",
            "base_commit": "a" * 40,
            "fixed_behaviour": EXPECTED_M005_BEHAVIOUR,
            "performance_declaration_status": "BLOCKED_INSUFFICIENT_EVIDENCE",
            "blocking_gaps": ["missing bid/ask snapshot"],
            "next_stage": "Acquire evidence without opening final test.",
        }
        result = m005_performance_gate(report)
        self.assertFalse(result["performance_declaration_allowed"])
        self.assertFalse(result["strategy_selection_authority"])
        self.assertFalse(result["promotion_authority"])

    def test_m005_behaviour_drift_is_rejected(self):
        report = {
            "contract_version": "RND-m005-evidence-gap-v0.1",
            "task_id": "RND-0026",
            "base_commit": "a" * 40,
            "fixed_behaviour": dict(EXPECTED_M005_BEHAVIOUR),
            "performance_declaration_status": "BLOCKED_INSUFFICIENT_EVIDENCE",
            "blocking_gaps": ["missing evidence"],
            "next_stage": "Acquire evidence.",
        }
        report["fixed_behaviour"]["fast_ma"] = 21
        with self.assertRaisesRegex(HistoricalEvidenceError, "behaviour mismatch"):
            m005_performance_gate(report)


if __name__ == "__main__":
    unittest.main()
