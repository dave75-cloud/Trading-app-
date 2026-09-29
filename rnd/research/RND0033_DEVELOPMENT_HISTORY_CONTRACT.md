# RND-0033 development-period historical expansion

Status: R&D CANDIDATE / STRUCTURAL EVIDENCE ONLY
Task: RND-0033
Base: `4b160506e3c5c5529ceffaa8a5a6dad79c9b840e`

## Objective

RND-0033 scales the successful 2015 four-pair evidence horizontally through
time while remaining wholly inside years that are unambiguously part of the
predeclared development partition.

New acquisition is exactly AUDUSD, EURUSD, GBPUSD and USDJPY for UTC years
2016, 2017, 2018 and 2019: sixteen shards. The merged 2015 evidence is
reference-only.

2020 is deliberately excluded because the RND-0029 development/validation
boundary occurs within that UTC year. No 2021-2024 shard is authorized.

## Method

Each new shard reuses the merged RND-0030 OANDA Practice quarantine runner and
must pass its existing immutable-content verifier before structural analysis.

Analysis is restricted to timestamp identity, immutable hashes, missing and
unexpected timestamp ledgers, contiguous gap classes, and the existing
non-authoritative 17:00 New York candidate. Canonical row files contain prices,
but RND-0033 extracts only `timestamp_utc`; prices are neither compared nor
emitted.

For each year, the analysis records per-pair structure and intersections shared
by all four pairs. Across years it records structural signatures sufficient to
show persistence or change in the empirical calendar pattern. A signature or
recurrence is a research observation, not calendar authority.

## Research questions

RND-0033 asks whether the 2015 17:00 pattern persists through 2016-2019,
whether closure-shaped intervals recur cross-pair, whether residual gaps are
shared or pair-specific, and whether the structural evidence suggests one or
more historical calendar regimes.

The purpose is to obtain enough development-period evidence to make the next
step materially closer to controlled M005 reconstruction rather than repeating
single-year pilots indefinitely.

## Zero-candle raw-page handling

The 2017 AUDUSD acquisition exposed a valid OANDA response envelope for
`2017-12-31T14:00:00Z` through `2018-01-01T00:00:00Z` with an empty
`candles` array. RND-0033 does not synthesize candles for such a page and does
not relax the shared acquisition parser. The quarantine runner may preserve a
structurally valid zero-candle page as immutable raw evidence, records its
candle count as zero, binds it into the raw bundle, and contributes no
canonical rows. The independently generated schedule and discrepancy ledger
remain responsible for representing the absent timestamps.

A malformed response, wrong instrument/granularity, non-list candle field, or
a shard with no candles across the entire year remains fail-closed.

## Authority boundary

Returned candles cannot establish documentary historical trading hours.
No calendar or holiday exception is promoted by this task.

No M005 signal, trade, return, P&L, equity, drawdown, Sharpe, win rate,
strategy score, feature selection or parameter comparison is permitted.

No synthetic or interpolated candle is permitted. No broker writes, capital
authority, automatic promotion or automatic merge are granted.

Any acceptance of a historical calendar/gap treatment, any acquisition of
2020 or later, and any strategy evaluation require a later human-reviewed
decision.
