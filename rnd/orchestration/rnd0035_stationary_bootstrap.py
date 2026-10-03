#!/usr/bin/env python3
"""Frozen RND-0035 G stationary-bootstrap core.

This module implements the predeclared stationary bootstrap over chronological
completed net trade returns with symbol labels preserved. It does not open G
execution authority. The four-pair concurrent portfolio adapter is deliberately
separate because overlapping trades require genuine timestamped portfolio
semantics rather than sequential trade compounding.
"""

from __future__ import annotations

import math
import random


SEEDS = (1729, 271828, 314159)
EXPECTED_BLOCK_LENGTHS = (10, 20, 40)
REPLICATIONS = 10000


class RND0035BootstrapError(ValueError):
    pass


def _validate_stream(stream):
    if not isinstance(stream, list) or not stream:
        raise RND0035BootstrapError("non-empty chronological trade stream required")
    out = []
    for item in stream:
        if not isinstance(item, dict):
            raise RND0035BootstrapError("trade item must be mapping")
        symbol = item.get("symbol")
        value = item.get("net_return")
        if not isinstance(symbol, str) or not symbol:
            raise RND0035BootstrapError("symbol label required")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise RND0035BootstrapError("finite net_return required")
        out.append((symbol, float(value)))
    return out


def stationary_resample(stream, expected_block_length, rng):
    """Return one stationary-bootstrap sample of equal length.

    At each step a new random block starts with probability 1/L; otherwise the
    previous source index advances by one with circular wraparound.
    """
    source = _validate_stream(stream)
    if isinstance(expected_block_length, bool) or not isinstance(expected_block_length, int):
        raise RND0035BootstrapError("integer expected block length required")
    if expected_block_length <= 0:
        raise RND0035BootstrapError("positive expected block length required")
    if not hasattr(rng, "random") or not hasattr(rng, "randrange"):
        raise RND0035BootstrapError("random generator interface required")

    n = len(source)
    p = 1.0 / expected_block_length
    index = rng.randrange(n)
    sample = []
    for i in range(n):
        if i > 0:
            if rng.random() < p:
                index = rng.randrange(n)
            else:
                index = (index + 1) % n
        symbol, value = source[index]
        sample.append({"symbol": symbol, "net_return": value})
    return sample


def _max_drawdown(returns):
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        if peak:
            max_dd = min(max_dd, equity / peak - 1.0)
    return equity, max_dd


def sample_statistics(sample):
    values = [float(item["net_return"]) for item in sample]
    equity, max_dd = _max_drawdown(values)
    total = sum(values)
    return {
        "mean_net_return": sum(values) / len(values),
        "compounded_net_equity_index": equity,
        "max_drawdown": max_dd,
        "positive_total_net_return_indicator": total > 0.0,
    }


def bootstrap_configuration(stream, seed, expected_block_length, replications=REPLICATIONS):
    if seed not in SEEDS:
        raise RND0035BootstrapError("undeclared bootstrap seed")
    if expected_block_length not in EXPECTED_BLOCK_LENGTHS:
        raise RND0035BootstrapError("undeclared expected block length")
    if replications != REPLICATIONS:
        raise RND0035BootstrapError("replication count differs from frozen plan")

    rng = random.Random(seed)
    means = []
    equities = []
    drawdowns = []
    positives = 0
    for _ in range(replications):
        stats = sample_statistics(stationary_resample(stream, expected_block_length, rng))
        means.append(stats["mean_net_return"])
        equities.append(stats["compounded_net_equity_index"])
        drawdowns.append(stats["max_drawdown"])
        positives += int(stats["positive_total_net_return_indicator"])

    return {
        "seed": seed,
        "expected_block_length_trades": expected_block_length,
        "replications": replications,
        "mean_net_return_average": sum(means) / replications,
        "compounded_net_equity_index_average": sum(equities) / replications,
        "max_drawdown_average": sum(drawdowns) / replications,
        "positive_total_net_return_fraction": positives / replications,
        "status": "PASS",
    }


def declared_configuration_grid():
    return [
        {"seed": seed, "expected_block_length_trades": block}
        for seed in SEEDS
        for block in EXPECTED_BLOCK_LENGTHS
    ]


def concurrent_portfolio_bootstrap(*args, **kwargs):
    raise RND0035BootstrapError(
        "four-pair concurrent bootstrap requires timestamped concurrent-portfolio adapter; "
        "sequential mixed-trade compounding is prohibited"
    )
