# RND-0055 — Prospective Evidence Operations Hardening

Status: CONTRACT FROZEN / OUTCOME BLIND

## Purpose

Operationalize RND-0054 without opening Q003 outcomes. The workflow remains limited to prospective evidence scheduling, GET-only acquisition, structural verification, immutable ledger advancement, status reporting, and fail-closed recovery guidance.

## Invariants

- candidate remains Q003 with frozen fingerprint `25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`;
- prospective start remains `2026-10-05T07:25:00Z`;
- earliest readout remains `2027-04-03T07:25:00Z`;
- all four symbols remain AUDUSD, EURUSD, GBPUSD, USDJPY;
- strategy evaluation, signal generation, trade simulation, P&L, equity, drawdown, win rate, pair ranking, parameter selection and validation classification remain prohibited;
- reserved-final access remains prohibited;
- broker writes, order endpoints, capital authority and automatic promotion remain prohibited;
- existing ledgers and sealed evidence are immutable and never overwritten.

## Required operational features

1. Recompute status from the full ledger rather than trusting cached summary fields.
2. Provide dry-run/status output for the next exact tranche window.
3. Refuse premature acquisition before the full window closes.
4. Refuse duplicate target paths and duplicate/overlapping ledger records.
5. Preserve legitimate provider/market gaps explicitly; never synthesize candles.
6. Fail closed on interrupted/partial acquisition and do not advance the ledger.
7. Require structural verification before ledger advancement.
8. Require a new ledger file for every successful advancement.
9. Surface recovery guidance without deleting or mutating sealed evidence.
10. Produce a deterministic runbook for Tranche 002 and later weekly tranches.

## Recovery policy

- partial stage directory: may be abandoned, but never treated as sealed evidence;
- sealed tranche + failed verification: retain evidence for diagnosis, do not append ledger;
- successful verification + ledger write failure: evidence remains sealed; rerun ledger advancement against the same verified tranche only after confirming no duplicate record exists;
- duplicate run: fail closed;
- malformed/contaminated ledger: fail closed and require human review.

## Authority

RND-0055 grants no strategy, validation, execution, broker-write, capital, live-environment, promotion or merge authority.
