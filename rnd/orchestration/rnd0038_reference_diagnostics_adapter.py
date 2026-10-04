#!/usr/bin/env python3
"""RND-0038 full-development adapter for frozen RND-0035 reference diagnostics."""

from __future__ import annotations

import hashlib
import json

from rnd0035_concurrent_reference_stats import concurrent_reference_statistics
from rnd0035_cost_diagnostics import cost_bridge
from rnd0035_stationary_bootstrap import bootstrap_configuration, declared_configuration_grid
from rnd0038_concentration_adapter import concentration_diagnostics_2015_2020

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


class RND0038ReferenceDiagnosticsAdapterError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0038ReferenceDiagnosticsAdapterError(message)


def _ledger_sha(trades):
    payload = json.dumps(trades, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def analyze_reference_results_2015_2020(per_symbol):
    _require(set(per_symbol) == set(SYMBOLS), "exact four-pair R000 result set required")

    all_trades = []
    per_pair_cost = {}
    per_pair_bootstrap = {}
    ledger_sha = {}

    for symbol in SYMBOLS:
        result = per_symbol[symbol]
        _require(result.get("symbol") == symbol, f"R000 symbol mismatch: {symbol}")
        trades = result.get("trades")
        _require(isinstance(trades, list), f"R000 trade ledger missing: {symbol}")
        all_trades.extend(trades)
        ledger_sha[symbol] = _ledger_sha(trades)
        per_pair_cost[symbol] = cost_bridge(trades)

        stream = [{"symbol": symbol, "net_return": trade["net_return"]} for trade in trades]
        per_pair_bootstrap[symbol] = [
            bootstrap_configuration(
                stream,
                config["seed"],
                config["expected_block_length_trades"],
            )
            for config in declared_configuration_grid()
        ]

    all_trades.sort(key=lambda trade: trade["exit_timestamp"])
    return {
        "contract_version": "RND0038-reference-diagnostics-v1",
        "B_concentration": concentration_diagnostics_2015_2020(all_trades),
        "D_cost_diagnostics_by_pair": per_pair_cost,
        "G_per_pair_stationary_bootstrap": per_pair_bootstrap,
        "G_four_pair_concurrent_reference": concurrent_reference_statistics(per_symbol),
        "R000_trade_ledger_sha256_by_pair": ledger_sha,
        "authority": {
            "validation_open": False,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "promotion_authority": "HUMAN_ONLY",
            "human_review_required": True,
        },
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }
