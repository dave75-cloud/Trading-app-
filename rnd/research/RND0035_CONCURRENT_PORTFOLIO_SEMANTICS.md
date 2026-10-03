# RND-0035 Concurrent Four-Pair Portfolio Semantics

Status: **IMPLEMENTED / FIXTURE-TESTED / G EXECUTION REMAINS CLOSED**

This note freezes the accounting semantics for the four-pair equal-unit concurrent reference adapter used by RND-0035 family G.

## Purpose

The frozen G plan requires reporting for a `FOUR_PAIR_EQUAL_UNIT_CONCURRENT_REFERENCE_AGGREGATION`. Completed trades can overlap in clock time. Therefore a mixed list of completed trade returns must **not** be compounded sequentially as though each trade followed the previous one economically.

## Unit convention

Each of AUDUSD, EURUSD, GBPUSD and USDJPY receives one fixed return-unit. This is an accounting diagnostic only. It is not account-currency P&L, portfolio sizing, risk allocation or capital authority.

At each genuine timestamp, pair-level unit P&L is:

`cumulative realized completed-trade net return + current executable unrealized mark return if position remains open`.

The four-pair portfolio level is the arithmetic sum of those four pair-level unit P&L values.

For reporting only, the equal-unit reference equity index is `1 + four_pair_pnl_level / 4`. Division by four normalizes the four fixed return-units to a unit starting index; it does not allocate capital or authorize sizing.

## Timestamp semantics

The global timeline is the union of genuine mark timestamps from the four pair reconstructions.

For a pair with no new genuine observation at a global timestamp, its most recent genuine executable mark is carried forward unchanged. This is a zero-price-change accounting carry, not interpolation or a synthetic candle. Missing observations never manufacture return.

A completed trade is realized exactly once at its genuine exit timestamp. The exit must have same-timestamp executable mark evidence. After a flat exit the prior unrealized mark disappears and the completed net return enters cumulative realized P&L. On a same-observation reversal, the old trade is realized and the new position's executable mark may coexist at that timestamp.

## Frozen G reporting interpretation

The trial plan freezes the G sampling unit as `CHRONOLOGICAL_COMPLETED_TRADE_NET_RETURNS_WITH_SYMBOL_LABEL_PRESERVED` and separately requires reporting for `PER_PAIR` and `FOUR_PAIR_EQUAL_UNIT_CONCURRENT_REFERENCE_AGGREGATION`.

These clauses are reconciled as follows:

1. **Stationary-bootstrap distributions are per-pair.** Each pair's chronological completed R000 net-trade return sequence is resampled independently under all 9 declared seed/block configurations and 10,000 replications per configuration.
2. **The four-pair concurrent result is the observed R000 reference aggregation.** It is constructed from genuine timestamped bid/ask executable marks and completed-trade evidence using this adapter and reported alongside the per-pair bootstrap distributions.
3. **No synthetic concurrent bootstrap is permitted.** A resampled completed-trade return does not carry enough information to reconstruct its original overlapping mark-to-market path after reordering. Reusing original timestamps for resampled returns, sequentially compounding mixed trades, or bootstrapping timestamp increments would silently change the frozen sampling unit.
4. `concurrent_portfolio_bootstrap` therefore remains fail-closed. This is intentional compliance with the frozen plan, not missing functionality.

This interpretation is frozen before G outcomes are authorized and does not alter the declared seeds, block lengths, replication count, sampling unit or strategy trials.

## Concurrent reference statistics

The observed concurrent reference report may include:

- final equal-unit normalized equity index;
- maximum drawdown of that normalized equity path;
- mean timestamp P&L increment;
- final realized completed-trade net-return sum;
- final unrealized executable mark-return sum;
- timestamp count and active-pair counts.

These are descriptive reference statistics, not bootstrap replications or strategy-selection criteria.

## Prohibitions

The adapter and G reporting must not:

- sequentially compound overlapping completed trades;
- assign resampled trade returns to invented timestamps;
- bootstrap timestamp increments as a substitute for the frozen completed-trade sampling unit;
- create synthetic prices or missing candles;
- use mid-price execution in place of bid/ask evidence;
- infer account-currency P&L;
- allocate capital or size positions;
- open validation or final-test data;
- authorize broker writes, strategy selection, promotion or merge.
