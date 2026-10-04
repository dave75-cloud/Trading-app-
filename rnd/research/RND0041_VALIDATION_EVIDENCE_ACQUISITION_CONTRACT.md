# RND-0041 — Validation Evidence Acquisition and Structural Seal

Status: **PREDECLARED / NOT AUTHORIZED TO ACQUIRE**

## Purpose

RND-0041 defines the outcome-blind acquisition and structural sealing of the RND-0029 validation partition required before any RND-0040 candidate evaluation may occur.

This task is strictly about evidence identity, boundaries, provenance, completeness, gap/calendar discrepancy accounting and human sealing. It does not authorize strategy outcomes.

## Exact validation interval

- start inclusive: `2020-12-31T19:15:00Z`
- end exclusive: `2023-01-01T09:40:00Z`
- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY
- granularity: M5
- provider: OANDA
- environment: PRACTICE
- price components: bid, ask, mid
- complete candles only

Any canonical row at or after `2023-01-01T09:40:00Z` is a fail-closed reserved-final boundary breach.

## Acquisition requirements

For each symbol, RND-0041 must preserve and record:

- exact authorized request interval;
- immutable raw response pages;
- aggregate raw-bundle SHA-256;
- canonical complete-candle rows;
- canonical row SHA-256;
- first and last canonical timestamps;
- row count;
- standard schedule identity;
- explicit missing/unexpected discrepancy ledger;
- provider/environment/instrument/granularity identity;
- proof of zero canonical rows at or after the reserved-final boundary.

No synthetic candles, interpolation, imputation or backfill may be created.

## Calendar discrepancy policy

Historical calendar discrepancies remain quarantine evidence, not defects to be rewritten away.

The existing empirical 17:00 New York candidate may be used only as a non-authoritative structural classification diagnostic. It must not:

- replace the authoritative standard schedule;
- modify canonical rows;
- convert unresolved ledger entries into documentary authority;
- generate or suppress strategy outcomes.

Any residual unexpected timestamps or qualitatively new structural anomaly must remain explicit for human review.

## Common coverage requirement

All four symbols must be acquired over the identical validation interval. Pair-specific date truncation is prohibited.

A structural seal may be issued only if:

1. all four shard identities verify;
2. all four reserved-final boundary proofs pass;
3. the exact common validation interval is preserved;
4. evidence hashes are stable;
5. discrepancies are explicitly classified and retained;
6. no strategy outcome fields are produced;
7. human review authorizes the structural seal.

## Warm-up evidence

RND-0041 may additionally identify, but must not mix into validation outcomes, at most the final 50 genuine development M5 rows immediately preceding `2020-12-31T19:15:00Z` for each symbol.

Warm-up rows must remain separately labeled as state-only evidence and must not be counted in validation row counts, trade counts, returns, P&L, equity, drawdown or diagnostics.

## Required external artifacts

- per-symbol acquired validation evidence directories outside the repository;
- acquisition summary;
- outcome-blind structural/classification review;
- human structural-seal report with immutable SHA-256;
- repository receipt binding the external seal report SHA-256.

## Prohibited operations

- strategy evaluation;
- R000 or `.0006` signals/trades/outcomes;
- validation candidate scoring;
- pair selection;
- parameter search;
- access to reserved-final rows;
- broker order endpoints;
- broker writes;
- portfolio sizing;
- capital allocation;
- automatic promotion;
- automatic merge.

## Graduation

Successful RND-0041 completion only makes the validation evidence **structurally available for a later human-authorized RND-0042 candidate evaluation**.

It does not itself open validation strategy outcomes.

## Authority

- acquisition authorization: **FALSE pending human approval**;
- structural seal authority: **HUMAN ONLY after acquisition review**;
- validation strategy outcomes: **FALSE**;
- reserved final test open: **FALSE**;
- broker writes: **FALSE**;
- capital authority: **FALSE**;
- strategy selection: **FALSE**;
- automatic promotion: **FALSE**;
- automatic merge: **FALSE**;
- human review required: **TRUE**.
