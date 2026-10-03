#!/usr/bin/env python3
"""Timestamped equal-unit concurrent portfolio adapter for RND-0035 G.

This is accounting/research infrastructure only. It does not authorize G
execution, strategy selection, sizing, validation/final access, broker writes,
capital, promotion or merge.

The adapter converts four per-symbol R000 result objects into a synchronized
portfolio P&L path. One fixed return-unit is assigned to each pair. Portfolio
P&L at each timestamp is:

    cumulative realized completed-trade net returns
    + current executable mark return of each still-open pair.

This preserves overlapping positions and avoids the invalid alternative of
sequentially compounding completed trades that were economically concurrent.
"""

from __future__ import annotations

import math
from datetime import datetime


SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


class RND0035ConcurrentPortfolioError(ValueError):
    pass


def _utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RND0035ConcurrentPortfolioError("UTC Z timestamp required")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0035ConcurrentPortfolioError("invalid UTC timestamp") from exc


def _finite(value, role):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RND0035ConcurrentPortfolioError(f"{role}: finite number required")
    value = float(value)
    if not math.isfinite(value):
        raise RND0035ConcurrentPortfolioError(f"{role}: finite number required")
    return value


def _validate_symbol_result(symbol, result):
    if not isinstance(result, dict):
        raise RND0035ConcurrentPortfolioError(f"{symbol}: result mapping required")
    if result.get("symbol") != symbol:
        raise RND0035ConcurrentPortfolioError(f"{symbol}: symbol identity mismatch")
    marks = result.get("marks")
    trades = result.get("trades")
    if not isinstance(marks, list) or not isinstance(trades, list):
        raise RND0035ConcurrentPortfolioError(f"{symbol}: marks and trades required")

    mark_by_ts = {}
    previous = None
    for mark in marks:
        if not isinstance(mark, dict):
            raise RND0035ConcurrentPortfolioError(f"{symbol}: mark mapping required")
        if mark.get("symbol") != symbol:
            raise RND0035ConcurrentPortfolioError(f"{symbol}: mark symbol mismatch")
        ts = mark.get("timestamp")
        dt = _utc(ts)
        if previous is not None and dt <= previous:
            raise RND0035ConcurrentPortfolioError(f"{symbol}: marks not strictly chronological")
        previous = dt
        if ts in mark_by_ts:
            raise RND0035ConcurrentPortfolioError(f"{symbol}: duplicate mark timestamp")
        position = mark.get("position")
        if position not in (-1, 0, 1):
            raise RND0035ConcurrentPortfolioError(f"{symbol}: invalid position")
        mark_return = mark.get("mark_return")
        if position == 0:
            if mark_return is not None:
                raise RND0035ConcurrentPortfolioError(f"{symbol}: flat mark_return must be null")
        else:
            mark_return = _finite(mark_return, f"{symbol}: mark_return")
        mark_by_ts[ts] = {
            "position": position,
            "mark_return": mark_return,
        }

    exits = {}
    for trade in trades:
        if not isinstance(trade, dict) or trade.get("symbol") != symbol:
            raise RND0035ConcurrentPortfolioError(f"{symbol}: invalid trade ledger item")
        ts = trade.get("exit_timestamp")
        _utc(ts)
        value = _finite(trade.get("net_return"), f"{symbol}: trade net_return")
        exits[ts] = exits.get(ts, 0.0) + value
        if ts not in mark_by_ts:
            raise RND0035ConcurrentPortfolioError(
                f"{symbol}: completed trade exit lacks same-timestamp executable mark evidence"
            )

    declared = result.get("completed_trade_count")
    if declared is not None and declared != len(trades):
        raise RND0035ConcurrentPortfolioError(f"{symbol}: completed trade count mismatch")
    return mark_by_ts, exits


def build_equal_unit_concurrent_path(per_symbol):
    """Build a synchronized additive equal-unit P&L path.

    The global timeline is the union of genuine mark timestamps. For a symbol
    that has no new observation at a timestamp, its latest genuine executable
    active-position mark is carried forward unchanged. Missing observations do
    not manufacture price movement. Realized trade returns are booked exactly
    once at their genuine exit timestamp.
    """
    if not isinstance(per_symbol, dict) or set(per_symbol) != set(SYMBOLS):
        raise RND0035ConcurrentPortfolioError("exactly four RND-0035 symbols required")

    marks = {}
    exits = {}
    timeline = set()
    for symbol in SYMBOLS:
        marks[symbol], exits[symbol] = _validate_symbol_result(symbol, per_symbol[symbol])
        timeline.update(marks[symbol])

    latest = {symbol: None for symbol in SYMBOLS}
    realized = {symbol: 0.0 for symbol in SYMBOLS}
    path = []
    previous_total = 0.0

    for ts in sorted(timeline, key=_utc):
        for symbol in SYMBOLS:
            if ts in exits[symbol]:
                realized[symbol] += exits[symbol][ts]
            if ts in marks[symbol]:
                latest[symbol] = marks[symbol][ts]

        per_pair = {}
        total = 0.0
        active_count = 0
        for symbol in SYMBOLS:
            mark = latest[symbol]
            unrealized = 0.0
            position = 0
            source_timestamp = None
            if mark is not None:
                position = mark["position"]
                if position != 0:
                    unrealized = mark["mark_return"]
                    active_count += 1
                # latest mark timestamp is needed for stale-evidence audit.
                # Resolve without scanning by using the current ts for updated
                # marks; otherwise retain prior source timestamp below.
            prior = path[-1]["per_pair"][symbol] if path else None
            if ts in marks[symbol]:
                source_timestamp = ts
            elif prior is not None:
                source_timestamp = prior["source_timestamp"]

            pair_total = realized[symbol] + unrealized
            per_pair[symbol] = {
                "realized_net_return_sum": realized[symbol],
                "unrealized_executable_mark_return": unrealized,
                "position": position,
                "source_timestamp": source_timestamp,
                "unit_pnl_level": pair_total,
            }
            total += pair_total

        increment = total - previous_total
        path.append({
            "timestamp": ts,
            "active_pair_count": active_count,
            "per_pair": per_pair,
            "equal_unit_pnl_level": total,
            "equal_unit_pnl_increment": increment,
        })
        previous_total = total

    if not path:
        raise RND0035ConcurrentPortfolioError("concurrent path is empty")

    realized_total = sum(realized.values())
    final_unrealized = sum(
        row["unrealized_executable_mark_return"] for row in path[-1]["per_pair"].values()
    )
    return {
        "contract_version": "RND0035-equal-unit-concurrent-path-v1",
        "normalization": "FIXED_ONE_RETURN_UNIT_PER_PAIR",
        "account_currency_pnl": False,
        "capital_allocation": False,
        "portfolio_sizing": False,
        "synthetic_prices": False,
        "sequential_mixed_trade_compounding": False,
        "timestamp_count": len(path),
        "realized_completed_trade_net_return_sum": realized_total,
        "final_unrealized_executable_mark_return_sum": final_unrealized,
        "final_equal_unit_pnl_level": path[-1]["equal_unit_pnl_level"],
        "path": path,
        "authority": {
            "dependence_resampling": False,
            "validation_open": False,
            "final_test_open": False,
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "human_review_required": True,
        },
    }
