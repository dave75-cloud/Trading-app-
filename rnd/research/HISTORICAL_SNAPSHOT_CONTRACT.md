# Historical snapshot and reserved-test contract

Status: R&D CANDIDATE / NON-OPERATIONAL
Task: RND-0027
Base: `09f839920a0bf7bede40d8e346ca6c7fcba02cc8`

## Purpose

This contract closes the methodological gap between a reproducible M005 state
machine and a performance-grade historical reconstruction. It does not assert
that the required historical data are already available and it does not open a
reserved final-test interval.

## Execution-grade snapshot

An AVAILABLE snapshot must bind all of the following before strategy evaluation:

- immutable snapshot ID;
- SHA-256 of the exact serialized source snapshot;
- provider and provider dataset/instrument identity;
- pair and M5 timeframe;
- UTC start and end;
- bid and ask OHLC components, with midpoint optional;
- complete-candle-only status;
- expected five-minute cadence;
- row count;
- duplicate/out-of-order/missing-bar checks;
- non-empty acquisition provenance;
- acquisition timestamp; and
- immutable/read-only status.

A correction creates a new snapshot ID and digest. It never mutates an earlier
research input.

A required snapshot that has not yet been acquired is represented as
`MISSING`. MISSING data have no invented digest, row count, or coverage claim
and cannot satisfy the reconstruction gate.

## Reserved final test

The final test is a sealed research partition, not merely another date filter.

Before a later human-authorized opening, permitted operations are limited to
identity/provenance checks, cryptographic verification, structural completeness
checks, timestamp/cadence checks and storage integrity. The following are
prohibited on the reserved interval:

- M005 signal generation;
- trade simulation;
- return/P&L/equity/drawdown/Sharpe or win-rate calculation;
- parameter comparison;
- strategy ranking;
- feature/threshold selection; and
- any report that reveals strategy performance.

A future task may open the reserved test only after the data identities,
reconstruction implementation, execution assumptions and validation protocol
are frozen and a human explicitly authorizes the opening.

## Fixed M005 reconstruction

RND-0027 pins the already reconstructed M005 behaviour:

- AUDUSD, EURUSD, GBPUSD and USDJPY;
- M5;
- MA20 / MA50;
- 12-bar return volatility, ddof=0;
- volatility threshold 0.0005;
- UTC sessions AUDUSD 11–14, EURUSD 11–13, GBPUSD 11–13, USDJPY 11–13;
- one-bar delayed signal; and
- minimum three-bar hold.

There is exactly one declared configuration. There is no parameter search
space, ranking, tuning or strategy-selection authority.

## Reconstruction output contract

A later event-driven reconstruction must preserve explicit signal time, decision
time, execution time, side/state transition, bid/ask execution price and cost,
open-position state, mark-to-market equity, pair exposure and currency-leg
exposure. Simultaneous positions must remain simultaneous; completed returns
must not be lower-tail clipped.

RND-0027 defines and tests these requirements but does not fabricate the absent
historical observations or claim an economic edge.
