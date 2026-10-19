# RND-0074 — Exact 2017 Cross-Pair Rollover Exceptions

Status: USER-REPORTED READ-ONLY TIMESTAMP METADATA; NO ADMISSION OR RESEAL.

The four 2017 development discrepancy ledgers report the **same two non-17:00 America/New_York unexpected timestamps** in each of AUDUSD, EURUSD, GBPUSD and USDJPY:

| UTC timestamp | New York timestamp | Occurrences |
| --- | --- | ---: |
| 2017-10-06T21:05:00+00:00 | 2017-10-06T17:05:00-04:00 (Friday) | 4 pairs |
| 2017-10-20T21:10:00+00:00 | 2017-10-20T17:10:00-04:00 (Friday) | 4 pairs |

These eight pair-timestamp anomalies constitute exactly **two distinct shared UTC timestamps**, five and ten minutes after the conventional Friday 17:00 New York FX close. Both fall in US daylight saving time, and neither is on a US DST transition date. This supersedes speculation in the earlier aggregate receipts that the exceptions might be associated with a DST change.

Combined with earlier human-reported aggregates: of 4,085 unexpected pair-timestamps for 2016–2019, 4,077 map to 17:00 New York; the eight others are the two repeated Friday timestamps above. This points to a shared reference-calendar versus provider-timestamp convention, but does **not** demonstrate the validity of any particular candle or rule out late-labelled candles, trading interruptions, or acquisition/clock artefacts.

Next evidence-admission questions: provider's exact M5 candle labelling convention (opening vs closing time), how Sunday open and Friday close are defined, whether the two post-close entries are incomplete/complete candles, original standard schedule declarations, and independent provenance/integrity verification. Inspect development-only metadata; do not open protected validation or prospective outcomes, quote prices, or returns.

Original manifests remain `QUARANTINED_UNRESOLVED_DISCREPANCIES`; `seal_allowed=False`. No source ledger/calendar or hashes modified, no discretionary acceptance of discrepancies, no broker writes and no incremental vendor spend. This receipt records results reported by the human operator and is not independent hash verification.
