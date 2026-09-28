#!/usr/bin/env python3

import copy
import unittest

from quant_research_contract import (
    AUTHORITY,
    SIMULATOR,
    VALIDATION,
    VERSION,
    QuantResearchContractError,
    validate_research_declaration,
)


def declaration():
    return {
        "contract_version": VERSION,
        "experiment_id": "EXP-BASELINE-001",
        "objective": "Falsify a fixed strategy hypothesis under declared rules.",
        "strategy_family": "fixed-baseline",
        "data_snapshots": [{
            "snapshot_id": "OANDA-AUDUSD-M5-001",
            "sha256": "a" * 64,
            "provider": "OANDA",
            "symbol": "AUDUSD",
            "timeframe": "M5",
            "price_components": ["bid", "ask", "mid"],
            "start_utc": "2020-01-01T00:00:00Z",
            "end_utc": "2025-12-31T23:55:00Z",
            "complete": True,
            "provenance": "immutable provider export with acquisition manifest",
        }],
        "windows": {
            "development": {
                "start_utc": "2020-01-01T00:00:00Z",
                "end_utc": "2022-12-31T23:55:00Z",
            },
            "validation": {
                "start_utc": "2023-01-01T00:00:00Z",
                "end_utc": "2024-12-31T23:55:00Z",
            },
            "test": {
                "start_utc": "2025-01-01T00:00:00Z",
                "end_utc": "2025-12-31T23:55:00Z",
            },
        },
        "search_space": {"fast_ma": [10, 20], "slow_ma": [40, 50, 60]},
        "declared_trial_count": 6,
        "metrics": ["net_return", "max_drawdown", "sharpe", "turnover"],
        "simulator": dict(SIMULATOR),
        "validation": dict(VALIDATION),
        "authority": dict(AUTHORITY),
    }


class QuantResearchContractTests(unittest.TestCase):
    def test_valid_declaration_is_accepted_without_authority(self):
        result = validate_research_declaration(declaration())
        self.assertEqual(result["declared_trial_count"], 6)
        self.assertFalse(result["authority"]["strategy_selection"])
        self.assertFalse(result["authority"]["broker_writes"])

    def test_missing_provenance_is_rejected(self):
        value = declaration()
        value["data_snapshots"][0]["provenance"] = ""
        with self.assertRaisesRegex(QuantResearchContractError, "provenance"):
            validate_research_declaration(value)

    def test_future_bar_access_is_rejected(self):
        value = declaration()
        value["simulator"]["future_bar_access"] = True
        with self.assertRaisesRegex(QuantResearchContractError, "simulator"):
            validate_research_declaration(value)

    def test_synthetic_return_clipping_is_rejected(self):
        value = declaration()
        value["simulator"]["synthetic_return_clipping"] = True
        with self.assertRaisesRegex(QuantResearchContractError, "simulator"):
            validate_research_declaration(value)

    def test_train_test_contamination_is_rejected(self):
        value = declaration()
        value["windows"]["development"]["end_utc"] = "2023-06-01T00:00:00Z"
        with self.assertRaisesRegex(QuantResearchContractError, "overlap"):
            validate_research_declaration(value)

    def test_undeclared_trials_are_rejected(self):
        value = declaration()
        value["declared_trial_count"] = 5
        with self.assertRaisesRegex(QuantResearchContractError, "trial_count"):
            validate_research_declaration(value)

    def test_incomplete_snapshot_is_rejected(self):
        value = declaration()
        value["data_snapshots"][0]["complete"] = False
        with self.assertRaisesRegex(QuantResearchContractError, "complete"):
            validate_research_declaration(value)

    def test_execution_baseline_without_bid_ask_is_rejected(self):
        value = declaration()
        value["data_snapshots"][0]["price_components"] = ["mid"]
        with self.assertRaisesRegex(QuantResearchContractError, "bid and ask"):
            validate_research_declaration(value)

    def test_authority_escalation_is_rejected(self):
        value = declaration()
        value["authority"]["strategy_selection"] = True
        with self.assertRaisesRegex(QuantResearchContractError, "authority"):
            validate_research_declaration(value)

    def test_post_hoc_winner_field_is_rejected(self):
        value = declaration()
        value["selected_strategy"] = "winner"
        with self.assertRaisesRegex(QuantResearchContractError, "field mismatch"):
            validate_research_declaration(value)


if __name__ == "__main__":
    unittest.main()
