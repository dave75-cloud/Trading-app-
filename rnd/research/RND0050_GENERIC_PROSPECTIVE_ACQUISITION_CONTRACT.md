# RND-0050 — Generic Prospective Acquisition Engine

Status: IMPLEMENTATION / OUTCOME-BLIND

## Purpose

Replace one-off weekly tranche scripts with one deterministic, fail-closed engine that derives the next admissible RND-0048 acquisition window from the sealed cumulative ledger and current UTC time.

This task is infrastructure only. It cannot generate Q003 signals, trades, returns, equity, drawdown, rankings, or validation classifications.

## Frozen bindings

Candidate fingerprint: `25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`

Prospective start: `2026-10-05T07:25:00Z`

Tranche 001 end: `2026-10-05T07:35:00Z`

Regular tranche duration: 7 calendar days.

Accumulation boundary: `2027-04-03T07:25:00Z`.

Symbols: AUDUSD, EURUSD, GBPUSD, USDJPY.

Timeframe: M5, OANDA PRACTICE, bid/ask/mid complete candles only.

## Planner rules

1. The next tranche start is exactly the previous verified tranche end.
2. A regular next end is start + 7 days.
3. The final end is clipped to the accumulation boundary.
4. A tranche is not runnable until current UTC time is at or after its end.
5. Start and end must lie on the M5 grid.
6. No overlap, backfill before the verified ledger end, or skipped interval is permitted.
7. A ledger candidate fingerprint mismatch fails closed.
8. Any broker-write, capital, strategy-evaluation, reserved-final, or promotion authority fails closed.
9. An already-complete accumulation boundary returns `ACCUMULATION_COMPLETE` and no acquisition window.
10. The planner may expose timestamps, tranche number, and structural status only; no market prices or strategy outcomes.

## Acquisition rules

The eventual runner may invoke only the existing GET-only OANDA PRACTICE candle acquisition path. Evidence must be written outside the repository, immutable, SHA-bound, gap-aware, and non-overwriting.

## Verification and ledger update

A tranche is not appended to the cumulative ledger until its structural verifier passes. Ledger updates record evidence identity and chronology only. No Q003 economic field is allowed.

## Authority

strategy_evaluation=FALSE
reserved_final_access=FALSE
broker_writes=FALSE
capital_authority=FALSE
automatic_promotion=FALSE
automatic_merge=FALSE
