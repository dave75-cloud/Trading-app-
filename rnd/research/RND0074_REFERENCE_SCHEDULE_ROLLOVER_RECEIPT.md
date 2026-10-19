# RND-0074 — EURUSD 2019 Reference Schedule Boundary Receipt

Status: USER-REPORTED DEVELOPMENT-ONLY METADATA OBSERVATION. NOT AN EVIDENCE RESEAL.

The operator inspected the string-only `standard_schedule.json` for `~/Trading-evidence/rnd0033-development-history-2016-2019/EURUSD/2019`. It contains 74,907 scheduled ISO timestamps, equal to the discrepancy ledger's `expected_count`. The first and last schedule entries are `2019-01-01T00:00:00Z` and `2019-12-31T23:55:00Z`.

Count of scheduled entries at specified New York local clock times:

| Local weekday | 16:55 | 17:00 | 17:05 |
| --- | ---: | ---: | ---: |
| Sunday | 0 | 0 | 52 |
| Monday | 52 | 0 | 52 |
| Tuesday | 53 | 0 | 53 |
| Wednesday | 52 | 0 | 52 |
| Thursday | 52 | 0 | 52 |
| Friday | 52 | 0 | 0 |
| Saturday | 0 | 0 | 0 |

The reference schedule excludes `17:00 America/New_York` on every day, includes the immediately preceding and following times Monday–Thursday, and includes Sunday 17:05 but not Sunday 17:00. This confirms a boundary exclusion in the reference schedule; the source reason and its fitness for OANDA M5 candle labelling remain unverified.

Prior operator findings: in 2016–2019, 4,077 of 4,085 unexpected pair-timestamp occurrences map to 17:00 New York. The eight exceptions are two Friday post-close timestamps, each repeated across all four pairs: 2017-10-06 17:05 EDT and 2017-10-20 17:10 EDT. These are separate cases, not explained by the 17:00 exclusion alone.

Outstanding: verify calendar generator specification and OANDA candle timestamp semantics; account for missing intervals, source completeness and evidence hashes. DO NOT accept, modify, delete or reseal any discrepancy by default. Original `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False` remain authoritative. No prices, strategy outcomes, protected evidence, orders or vendor subscriptions accessed.

Next permitted step: inspect the source calendar declaration metadata (keys, then allowlisted non-sensitive schedule-convention fields) for this development-only pair-year; compare actual and reference semantics without changing them.
