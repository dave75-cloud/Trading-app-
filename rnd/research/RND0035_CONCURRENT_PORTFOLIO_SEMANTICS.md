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

## Timestamp semantics

The global timeline is the union of genuine mark timestamps from the four pair reconstructions.

For a pair with no new genuine observation at a global timestamp, its most recent genuine executable mark is carried forward unchanged. This is a zero-price-change accounting carry, not interpolation or a synthetic candle. Missing observations never manufacture return.

A completed trade is realized exactly once at its genuine exit timestamp. The exit must have same-timestamp executable mark evidence. After a flat exit the prior unrealized mark disappears and the completed net return enters cumulative realized P&L. On a same-observation reversal, the old trade is realized and the new position's executable mark may coexist at that timestamp.

## Prohibitions

The adapter must not:

- sequentially compound overlapping completed trades;
- create synthetic prices or missing candles;
- use mid-price execution in place of bid/ask evidence;
- infer account-currency P&L;
- allocate capital or size positions;
- open validation or final-test data;
- authorize broker writes, strategy selection, promotion or merge.

## Relationship to stationary bootstrap

This adapter defines the **reference concurrent portfolio path** only.

The frozen G sampling unit remains `CHRONOLOGICAL_COMPLETED_TRADE_NET_RETURNS_WITH_SYMBOL_LABEL_PRESERVED`. A later integration layer must explicitly reconcile that sampling unit with the timestamped concurrent path. Until that mapping is fixture-proven, `concurrent_portfolio_bootstrap` must remain fail-closed. The adapter itself does not authorize G outcomes.
