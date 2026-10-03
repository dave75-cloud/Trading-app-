#!/usr/bin/env python3

import unittest
from unittest.mock import patch

import rnd0035_reference_diagnostics_runner as runner


def result(symbol):
    return {
        "symbol": symbol,
        "trades": [
            {
                "symbol": symbol,
                "entry_timestamp": "2019-01-02T11:00:00Z",
                "exit_timestamp": "2019-01-02T11:05:00Z",
                "exit_year": 2019,
                "gross_return": 0.002,
                "net_return": 0.001,
            }
        ],
        "marks": [
            {"symbol": symbol, "timestamp": "2019-01-02T11:00:00Z", "position": 1, "mark_return": -0.001},
            {"symbol": symbol, "timestamp": "2019-01-02T11:05:00Z", "position": 0, "mark_return": None},
        ],
        "completed_trade_count": 1,
    }


class TestRND0035ReferenceDiagnosticsRunner(unittest.TestCase):
    def test_repository_gate_is_closed(self):
        gate = runner.load_gate(require_open=False)
        self.assertEqual(gate["status"], "CLOSED_PENDING_LOCAL_VALIDATION")
        with self.assertRaisesRegex(runner.RND0035ReferenceDiagnosticsError, "gate remains closed"):
            runner.load_gate(require_open=True)

    @patch.object(runner, "concurrent_reference_statistics", return_value={"status": "PASS"})
    @patch.object(runner, "bootstrap_configuration", return_value={"status": "PASS"})
    @patch.object(runner, "concentration_diagnostics", return_value={"status": "PASS"})
    @patch.object(runner, "cost_bridge", return_value={"status": "PASS"})
    def test_analysis_routes_only_r000_reference_evidence(
        self, mock_cost, mock_concentration, mock_bootstrap, mock_concurrent
    ):
        per_symbol = {symbol: result(symbol) for symbol in ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")}
        out = runner.analyze_reference_results(per_symbol)
        self.assertEqual(mock_cost.call_count, 4)
        self.assertEqual(mock_concentration.call_count, 1)
        self.assertEqual(mock_bootstrap.call_count, 36)
        self.assertEqual(mock_concurrent.call_count, 1)
        self.assertEqual(set(out["R000_trade_ledger_sha256_by_pair"]), set(per_symbol))
        self.assertFalse(out["authority"]["strategy_selection"])
        self.assertFalse(out["authority"]["validation_open"])
        self.assertFalse(out["authority"]["broker_writes"])
        self.assertEqual(out["status"], "COMPLETE_REQUIRES_HUMAN_REVIEW")

    def test_requires_exact_four_pair_reference_set(self):
        with self.assertRaisesRegex(runner.RND0035ReferenceDiagnosticsError, "exact four-pair"):
            runner.analyze_reference_results({"AUDUSD": result("AUDUSD")})


if __name__ == "__main__":
    unittest.main()
