# RND-0031 historical-calendar evidence hardening

Status: R&D CANDIDATE / STRUCTURAL EVIDENCE ONLY  
Task: RND-0031  
Base: `d9a93899a1c0fba531f67639685ce9545b2b473c`

## Purpose

RND-0031 records the first successful real historical OANDA pilot shard and
hardens the distinction between acquired evidence, historical-calendar
hypotheses and performance-grade data acceptance.

The pilot is AUDUSD, UTC calendar year 2015, wholly inside the development
partition. No strategy outcome is permitted.

## Immutable pilot evidence

The external attempt-3 shard passed the merged RND-0030 integrity verifier and
a credential-leak scan. The repository records only structural counts and
cryptographic identities, not credentials, account identity or price values.

The authoritative RND-0030 comparison remains unresolved:

- canonical rows: 74,313;
- ordinary-session expected timestamps: 74,907;
- raw pages: 22;
- missing expected timestamps: 849;
- unexpected actual timestamps: 255;
- seal allowed: false.

The raw-bundle, canonical-row and standard-schedule SHA-256 identities are
recorded in `RND0031_PILOT_EVIDENCE_RECORD.json`.

## 17:00 New York falsification hypothesis

A deliberately non-authoritative candidate schedule adds the 17:00 New York M5
start on ordinary Sunday-through-Thursday session boundaries while removing
nothing from the RND-0030 schedule.

For AUDUSD/2015 this changes unexpected timestamps from 255 to 1. It explains
254 of the original 255 unexpected observations (99.6078431372549%). The one
remaining unexpected observation is 2015-08-28T21:05:00Z, corresponding to
Friday 17:05 New York.

This result strongly falsifies applying the present-day RND-0030 17:05 baseline
unchanged to this 2015 shard. It does **not** authorize replacing the
authoritative calendar. Returned candles cannot grant calendar authority.

## Missing-data classes

After the non-authoritative 17:00 candidate is applied for diagnostic purposes,
856 expected timestamps remain absent.

The run-length structure contains:

- 648 bars in three large closure-shaped candidate runs;
- 208 bars in short residual runs: 189 one-bar runs, eight two-bar runs and one
  three-bar run.

A long run may be called only a **closure-shaped candidate** until independent
historical evidence supports a closure. A short run remains a residual source
gap. Neither class may be silently deleted, interpolated or synthesized.

## Documentary status

Current official OANDA material documents ordinary FX hours of 17:05 through
16:59 New York with a six-minute daily break, and official holiday material
shows that public holidays can alter ordinary FX hours.

Current OANDA legal material also describes FX availability more generally as
approximately Sunday 5 p.m. through Friday 5 p.m. New York.

No surviving authoritative OANDA source reviewed for RND-0031 establishes the
exact 2015 ordinary break rule or the exact 2015 holiday intervals. Therefore:

1. current rules are not projected backward as exact historical authority;
2. current holiday notices are not projected backward as 2015 evidence;
3. the empirical 17:00 result remains a falsification/corroboration hypothesis;
4. exact historical exceptions remain unresolved unless independently sourced.

## Historical acceptance policy

Performance-grade historical evidence need not contain zero unexplained missing
M5 candles. Requiring a fabricated calendar exception for every genuine source
gap would make the evidence less truthful.

A later acceptance gate may retain a shard with explicit gaps only if all of
the following are true:

1. the applicable session calendar has independent documentary support;
2. every missing/unexpected timestamp remains in an immutable gap ledger;
3. no synthetic or interpolated candle is inserted;
4. downstream simulation is explicitly gap-aware and fails closed where a gap
   makes execution semantics ambiguous;
5. cross-pair consistency is checked for shared calendar effects;
6. human review approves any calendar/exception promotion.

This policy does not itself seal the AUDUSD/2015 shard.

## Expansion gate

RND-0031 does not authorize acquisition of the remaining 39 symbol/year shards.
After independent validation and human merge decision, the next controlled
expansion should begin with EURUSD, GBPUSD and USDJPY for 2015. Agreement or
disagreement across those pairs provides structural corroboration before any
ten-year expansion.

## Authority

No broker writes, strategy evaluation, capital authority, calendar promotion,
automatic promotion or automatic merge. The reserved final test remains
outcome-sealed.
