#!/usr/bin/env python3
"""Descriptive statistics for the RND-0035 four-pair concurrent R000 path.

This consumes the timestamped path built by rnd0035_concurrent_portfolio and
never resamples it. G's bootstrap sampling unit remains completed trade returns.
"""

from __future__ import annotations

import math

from rnd0035_concurrent_portfolio import build_equal_unit_concurrent_path


class RND0035ConcurrentReferenceStatsError(ValueError):
    pass


def _finite(value, role):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RND0035ConcurrentReferenceStatsError(f"{role}: finite number required")
    value = float(value)
    if not math.isfinite(value):
        raise RND0035ConcurrentReferenceStatsError(f"{role}: finite number required")
    return value


def concurrent_reference_statistics(per_symbol):
    concurrent = build_equal_unit_concurrent_path(per_symbol)
    path = concurrent["path"]
    equities = []
    increments = []
    peak = 1.0
    max_dd = 0.0
    active_counts = []

    for row in path:
        pnl = _finite(row["equal_unit_pnl_level"], "equal_unit_pnl_level")
        increment = _finite(row["equal_unit_pnl_increment"], "equal_unit_pnl_increment")
        equity = 1.0 + pnl / 4.0
        if equity <= 0.0:
            raise RND0035ConcurrentReferenceStatsError(
                "normalized equal-unit reference equity must remain positive"
            )
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
        equities.append(equity)
        increments.append(increment)
        active_counts.append(int(row["active_pair_count"]))

    return {
        "contract_version": "RND0035-concurrent-reference-statistics-v1",
        "normalization": "ONE_PLUS_FOUR_PAIR_EQUAL_UNIT_PNL_DIVIDED_BY_FOUR",
        "timestamp_count": len(path),
        "final_equal_unit_normalized_equity_index": equities[-1],
        "equal_unit_normalized_max_drawdown": max_dd,
        "mean_timestamp_pnl_increment": sum(increments) / len(increments),
        "max_active_pair_count": max(active_counts),
        "mean_active_pair_count": sum(active_counts) / len(active_counts),
        "realized_completed_trade_net_return_sum": concurrent[
            "realized_completed_trade_net_return_sum"
        ],
        "final_unrealized_executable_mark_return_sum": concurrent[
            "final_unrealized_executable_mark_return_sum"
        ],
        "account_currency_pnl": False,
        "capital_allocation": False,
        "portfolio_sizing": False,
        "dependence_resampling": False,
        "strategy_selection": False,
        "validation_open": False,
        "final_test_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "status": "PASS",
    }
