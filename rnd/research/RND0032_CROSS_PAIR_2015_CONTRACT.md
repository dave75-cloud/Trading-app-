# RND-0032 controlled 2015 cross-pair historical evidence

Status: R&D CANDIDATE / STRUCTURAL EVIDENCE ONLY
Task: RND-0032
Base: `8a633aa22cce48aa42f192ce8eae36fe06a0862d`

## Objective

RND-0032 extends the successful AUDUSD/2015 pilot horizontally across the
remaining M005 universe pairs before any extension through time.

New acquisition is restricted to:

- EURUSD / UTC year 2015;
- GBPUSD / UTC year 2015;
- USDJPY / UTC year 2015.

AUDUSD/2015 attempt-3 is reference evidence only. No later year is authorized.

## Acquisition path

RND-0032 reuses the merged RND-0030 OANDA Practice quarantine runner. The
bounded RND-0032 launcher fixes the symbol set and year rather than exposing a
general selection surface.

The source remains read-only historical candles: M5, bid/ask/mid, complete
candles only, external immutable evidence, no overwrite, no broker writes.

Current OANDA developer documentation continues to describe the authenticated
instrument-candles endpoint as GET, supports M5, permits bid/ask/mid pricing
components, and caps candle history responses at 5000 records per request.
These current interface facts do not establish historical 2015 trading hours.

## Cross-pair corroboration

Every acquired shard must first pass the existing RND-0030
`verify_existing_shard` integrity verifier.

The RND-0032 comparison then uses only:

- timestamp identity;
- missing/unexpected timestamp ledgers;
- contiguous missing-run structure;
- non-authoritative 17:00 New York candidate results;
- immutable manifest hashes and counts.

Although canonical row files contain prices, RND-0032 extracts only
`timestamp_utc`; bid/ask/mid values are neither compared nor emitted.

The comparison asks whether the AUDUSD/2015 findings recur independently:
the 17:00 pattern, closure-shaped runs, residual gaps, and the isolated Friday
2015-08-28 17:05 New York observation.

## Authority boundary

Cross-pair agreement is corroborating structural evidence only. It cannot
become documentary authority for a historical session rule or holiday
exception. Disagreement is preserved rather than reconciled.

No M005 signal, trade, return, P&L, equity, drawdown, Sharpe, win rate,
strategy score, feature or parameter comparison is permitted.

No synthetic candle is permitted.

## Expansion gate

RND-0032 does not authorize 2016-2024 acquisition. A later human-reviewed task
must decide whether the 2015 cross-pair evidence is sufficient to define the
next historical acquisition/calendaring step.
