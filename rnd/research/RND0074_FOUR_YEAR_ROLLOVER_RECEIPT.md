# RND-0074 — 2016–2019 Cross-Pair Unexpected Timestamp Receipt

## Authority and source
Human-reported read-only UTC-to-`America/New_York` clock summaries of `unexpected_timestamps` from the four-pair 2016–2019 development-only RND-0033 discrepancy ledgers. Counts are not independently SHA-verified by this receipt, and no market price or strategy outcome data were inspected.

| Year | Unexpected | Exactly 17:00 New York | Other |
| --- | ---: | ---: | ---: |
| 2016 | 1008 | 1008 | 0 |
| 2017 | 1014 | 1006 | 8 |
| 2018 | 1037 | 1037 | 0 |
| 2019 | 1026 | 1026 | 0 |
| **Total** | **4085** | **4077** | **8** |

2017 exceptions: **exactly two per pair** (AUDUSD, EURUSD, GBPUSD, USDJPY). Other years: zero exceptions for all pairs. The result strongly supports a shared calendar-boundary or timestamp-convention issue, but does not establish that the eight exception timestamps are identical across pairs, nor their causes.

## Research interpretation
- 99.804% (=4077/4085) of the listed unexpected timestamps align with 17:00 New York local time.
- The repeated 2017 exception counts merit a narrowly scoped check of exception timestamps and DST/calendar transitions. **Do not presume DST is the cause**.
- This test concerns unexpected timestamps **only**. Missing timestamps, completeness by session, and broader provenance remain unresolved.
- Status `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False` remain authoritative; no automated resealing, schedule editing or research admission follows from this summary.
- AUDUSD 2016 was originally marked `verified_skipped` in the RND-0033 run summary; this receipt only records the existence and pattern of that year's local ledger, not independent verification or authority to change its status.
- No OANDA broker writes, protected validation/prospective evidence, spend, or Trading Economics activation.

## Next narrow check
For 2017 alone, report each non-17:00 New York discrepancy timestamp with UTC date/time and New York date/time across four pairs, using only the development discrepancy ledgers. Compare dates across instruments and independently review calendar construction and candle timestamp semantics. Retain immutable raw ledgers/hashes and every quarantine decision.
