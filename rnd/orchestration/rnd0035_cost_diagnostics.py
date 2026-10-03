#!/usr/bin/env python3
"""Frozen RND-0035 D cost diagnostics for the R000 completed-trade ledger.

Descriptive diagnostics only. No strategy selection, parameter search, broker,
capital, validation/final, promotion or merge authority.
"""

from __future__ import annotations

import math


class RND0035CostDiagnosticError(ValueError):
    pass


def _validate_trades(trades):
    if not isinstance(trades, list) or not trades:
        raise RND0035CostDiagnosticError("non-empty completed trade ledger required")
    out = []
    for trade in trades:
        if not isinstance(trade, dict):
            raise RND0035CostDiagnosticError("trade must be mapping")
        gross = trade.get("gross_return")
        net = trade.get("net_return")
        for name, value in (("gross_return", gross), ("net_return", net)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise RND0035CostDiagnosticError(f"finite {name} required")
            if value <= -1.0:
                raise RND0035CostDiagnosticError(f"{name} <= -100% prohibited")
        out.append((float(gross), float(net)))
    return out


def _compound(values):
    equity = 1.0
    for value in values:
        if value <= -1.0:
            return 0.0
        equity *= 1.0 + value
    return equity


def stressed_net_equity(trades, additional_round_trip_bps):
    pairs = _validate_trades(trades)
    if isinstance(additional_round_trip_bps, bool) or not isinstance(additional_round_trip_bps, (int, float)):
        raise RND0035CostDiagnosticError("numeric bps required")
    bps = float(additional_round_trip_bps)
    if not math.isfinite(bps) or bps < 0:
        raise RND0035CostDiagnosticError("finite non-negative bps required")
    drag = bps / 10000.0
    return _compound([net - drag for _, net in pairs])


def break_even_additional_round_trip_bps(trades, upper_bound_bps=1000.0):
    """Additional adverse bps/trade that makes completed-trade net equity 1.0.

    Returns 0 when the observed net ledger is already at/below break-even.
    Otherwise uses deterministic bisection on the monotone stressed-equity path.
    """
    pairs = _validate_trades(trades)
    observed = _compound([net for _, net in pairs])
    if observed <= 1.0:
        return 0.0

    lo = 0.0
    hi = float(upper_bound_bps)
    if not math.isfinite(hi) or hi <= 0:
        raise RND0035CostDiagnosticError("positive finite upper bound required")
    if stressed_net_equity(trades, hi) > 1.0:
        raise RND0035CostDiagnosticError("break-even not bracketed by upper bound")

    for _ in range(100):
        mid = (lo + hi) / 2.0
        if stressed_net_equity(trades, mid) > 1.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def cost_bridge(trades, declared_stresses_bps=(0.5, 1.0, 2.0, 5.0)):
    pairs = _validate_trades(trades)
    gross_values = [gross for gross, _ in pairs]
    net_values = [net for _, net in pairs]
    gross_equity = _compound(gross_values)
    observed_net_equity = _compound(net_values)
    observed_cost_drag_sum = sum(gross - net for gross, net in pairs)

    stressed = {}
    for bps in declared_stresses_bps:
        key = f"{float(bps):g}"
        stressed[key] = {
            "additional_round_trip_bps": float(bps),
            "net_equity_index": stressed_net_equity(trades, bps),
        }

    return {
        "contract_version": "RND0035-cost-diagnostics-v1",
        "classification": "OUTCOME_INFORMED",
        "completed_trade_count": len(pairs),
        "gross_equity_index": gross_equity,
        "observed_net_equity_index": observed_net_equity,
        "gross_to_observed_net_equity_difference": gross_equity - observed_net_equity,
        "observed_execution_cost_drag_sum": observed_cost_drag_sum,
        "break_even_additional_round_trip_bps": break_even_additional_round_trip_bps(trades),
        "declared_stressed_net_equity": stressed,
        "strategy_selection_authority": False,
        "broker_writes": False,
        "capital_authority": False,
        "validation_open": False,
        "final_test_open": False,
        "status": "PASS",
    }
