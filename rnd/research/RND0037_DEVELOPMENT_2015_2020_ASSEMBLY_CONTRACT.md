# RND-0037 — Governed 2015–2020 Development Evidence Assembly

Status: **PREDECLARED / STRUCTURAL ASSEMBLY ONLY**

## Purpose

RND-0037 assembles the complete predeclared RND-0029 development partition from already-governed evidence. It is an identity, coverage and boundary task only. It must not generate strategy signals, trades, returns, P&L, equity, drawdown, hit rate, rankings or parameter choices.

## Development partition

Authoritative interval:

- start inclusive: `2015-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- granularity: M5

Evidence sources:

- 2015: governed RND-0031/RND-0032 shards;
- 2016–2019: governed RND-0033 shards;
- 2020: human-sealed RND-0036 evidence.

## Required checks

1. Exact four-symbol universe.
2. Exact development interval with no row at or after validation boundary.
3. Existing 2015–2019 canonical identities must match the recorded governed identities; no rewrite or normalization is permitted.
4. 2020 evidence must match the RND-0036 human seal receipt SHA-256 and per-shard canonical identities.
5. All canonical rows remain provider evidence only; no synthetic candles, interpolation or backfill.
6. Calendar classifications remain descriptive. The empirical 17:00 New York candidate has no documentary or schedule authority.
7. Missing/gap observations remain explicit.
8. Assembly output must be an external report plus a repository receipt; raw/canonical evidence remains outside the repository.

## Explicit prohibitions

RND-0037 must not:

- evaluate R000, A016, Champion, or any strategy;
- compare strategies or rank configurations;
- open validation or final-test data;
- extend any RND-0035 parameter grid;
- alter frozen M005 semantics;
- authorize strategy selection, sizing, broker writes, capital, promotion or merge.

## Graduation

RND-0037 graduates only when the full 2015–2020 development evidence set is identity-bound and structurally complete. Graduation means only that the development data foundation is complete. Any strategy evaluation on 2020 or any 2015–2020 hypothesis test requires a separate human-reviewed authorization.

## Authority

- strategy evaluation: **FALSE**
- validation open: **FALSE**
- final test open: **FALSE**
- strategy selection: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
