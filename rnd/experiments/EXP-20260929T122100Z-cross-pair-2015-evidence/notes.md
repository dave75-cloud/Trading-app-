# RND-0032 — 2015 cross-pair evidence

Experiment: `EXP-20260929T122100Z-cross-pair-2015-evidence`

RND-0032 is intentionally horizontal rather than longitudinal. It acquires the
remaining three M005 pairs for 2015 only and compares their structural
timestamp/gap evidence with the immutable AUDUSD/2015 reference.

No strategy outcomes are permitted. Cross-pair agreement cannot by itself
authorize a historical-calendar change.

## Acquired evidence

The bounded launcher acquired exactly EURUSD/2015, GBPUSD/2015 and USDJPY/2015.
The existing AUDUSD/2015 RND-0031 attempt-3 evidence remained reference-only.
The RND-0030 quarantine runner reported three completed shards, zero verified
skips, `sealed=FALSE` and `strategy_evaluation=FALSE`.

The four-pair verifier passed integrity verification for AUDUSD, EURUSD,
GBPUSD and USDJPY. Its structural report SHA-256 is
`8d594b9c0bbbdcd771acfa2be7fc032b827c8e246265459a5448a3f24cc436fe`.

Under the existing standard schedule, baseline unexpected counts were 255,
260, 259 and 258 respectively. The non-authoritative 17:00 New York candidate
explained 254, 259, 258 and 257 respectively, leaving exactly one unexpected
timestamp in every pair.

That remaining timestamp is shared across all four pairs:
`2015-08-28T21:05:00Z`. The earlier AUDUSD anomaly therefore recurs in
EURUSD, GBPUSD and USDJPY as well.

All four pairs also contain a 648-bar closure-shaped candidate component.
Residual short-gap bars remain pair-specific (AUDUSD 208, EURUSD 128,
GBPUSD 311, USDJPY 70); USDJPY additionally retains 9 unclassified gap bars.
No gap is synthesized, interpolated or silently reconciled.

These findings corroborate a historical structural mismatch with the
present-day-derived standard calendar, but returned candles remain empirical
evidence rather than documentary authority for a 2015 session rule or holiday
exception.

The experiment remains running pending final independent validation.
Calendar promotion, sealing, longitudinal expansion and strategy evaluation
remain unauthorized.
