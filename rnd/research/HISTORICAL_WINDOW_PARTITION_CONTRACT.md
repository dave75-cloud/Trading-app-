# Predeclared historical window and sealed chronological partition

Status: R&D CANDIDATE / NO STRATEGY EVALUATION
Task: RND-0029
Base: `f342a3b2aa4bca021346df7915f8e9aaed2f5cab`

## Purpose

RND-0029 binds the historical research horizon and chronological partition
before the project is permitted to calculate M005 signals, trades or
performance from the acquired evidence.

## Horizon

The requested evidence horizon is fixed at:

- start: **2015-01-01T00:00:00Z**
- end (exclusive): **2025-01-01T00:00:00Z**
- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY
- timeframe: M5
- price evidence: bid, ask and midpoint
- complete candles only

The horizon was declared before historical acquisition or M005 performance
reconstruction. It must not be changed because a strategy performs better or
worse in any subperiod.

## Full-coverage rule

All four symbols must support the requested horizon under the governed
structural evidence contract. RND-0029 deliberately does **not** permit an
automatic "largest common intersection" fallback. A missing structural interval
therefore fails closed and requires a new, separately reviewed research
decision rather than silently moving a partition boundary.

Structural inspection may use timestamps, provider/instrument identity,
granularity, completeness, row counts, gap ledgers and cryptographic evidence
identities. It may not use signals, positions, trades, returns, P&L, equity,
drawdown, Sharpe, win rate or strategy scores.

## Partition rule

Partitions are determined from elapsed UTC duration, not candle count:

- development: first 60%;
- validation: next 20%;
- reserved final test: final 20%.

Raw fractional boundaries are snapped **forward** to the next M5 grid point.
For the fixed horizon this yields:

- development: 2015-01-01 00:00Z to 2020-12-31 19:15Z;
- validation: 2020-12-31 19:15Z to 2023-01-01 09:40Z;
- reserved final test: 2023-01-01 09:40Z to 2025-01-01 00:00Z.

The implementation recomputes these boundaries from the rule and rejects a
declaration whose stored boundaries drift.

## Warm-up isolation

At a later reconstruction stage, at most 50 immediately preceding M5 **bars**
may initialize MA/volatility state at a partition boundary. Warm-up observations
belong to the preceding partition and cannot create trades, returns or
selection evidence in the later partition. Final-test rows can never be used
to warm up development or validation.

## Reserved final test

RND-0029 changes the reserved test from an unbound boundary to a **bound but
sealed** boundary. Structural integrity and cryptographic identity may be
verified. Strategy signals, simulations, P&L/equity metrics, parameter
selection and ranking remain prohibited. Opening the seal requires a later
explicit human gate.

## Acquisition calendar

The acquisition window is now human-approved as a research-data boundary only.
This does not authorize broker writes or strategy evaluation.

Completeness still requires an explicit expected M5 timestamp schedule. A
weekly FX-session rule alone is not sufficient evidence for provider holidays
or exceptional closures; those exceptions must be declared and reviewed
rather than inferred from missing returned candles.
