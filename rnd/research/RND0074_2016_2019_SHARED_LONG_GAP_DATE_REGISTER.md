# RND-0074 — Shared 2016–2019 Long-Gap Interval Register and Documentary Assessment

**STATUS: HUMAN-REPORTED TIMESTAMP METADATA / NON-AUTHORITATIVE CLOSURE CANDIDATES / NO ADMISSION.**
Prepared 2026-10-23. Inputs: the operator's read-only output from `EURUSD/<YEAR>/discrepancy_ledger.json` within `~/Trading-evidence/rnd0033-development-history-2016-2019`. Prior exact-overlap checks showed the same long-gap timestamp sets in all four pairs for each year. Ledger digest checks passed under the limited RND-0074 metadata audit (16/16), not a full RND-0030 raw-page verifier.

## Thirteen shared long missing-timestamp runs

The `end` column denotes the **last missing M5 candle-start timestamp**, inclusive; it is not a market reopening timestamp. Durations count missing five-minute slots, not a documentary trading halt.

| Year | First missing UTC | Last missing UTC | Missing bars | Candidate class |
|---|---|---|---:|---|
| 2016 | 2016-01-01T00:00Z | 2016-01-01T21:55Z | 264 | New Year-associated |
| 2016 | 2016-12-25T22:05Z | 2016-12-26T21:55Z | 287 | Christmas-associated |
| 2017 | 2017-01-01T22:05Z | 2017-01-02T21:55Z | 287 | New Year-associated |
| 2017 | 2017-12-24T22:05Z | 2017-12-25T21:55Z | 287 | Christmas-associated |
| 2017 | 2017-12-31T22:05Z | 2017-12-31T23:55Z | 23 | Year-end, UTC-shard-boundary fragment |
| 2018 | 2018-01-01T00:00Z | 2018-01-01T21:55Z | 264 | New Year, continuation candidate |
| 2018 | 2018-12-24T22:05Z | 2018-12-25T21:55Z | 287 | Christmas-associated |
| 2018 | 2018-12-31T22:05Z | 2018-12-31T23:55Z | 23 | Year-end, UTC-shard-boundary fragment |
| 2019 | 2019-01-01T00:00Z | 2019-01-01T21:55Z | 264 | New Year, continuation candidate |
| 2019 | 2019-10-20T21:05Z | 2019-10-20T23:50Z | 34 | UNEXPLAINED Sunday reopening |
| 2019 | 2019-12-08T22:05Z | 2019-12-08T23:35Z | 19 | UNEXPLAINED Sunday reopening |
| 2019 | 2019-12-24T22:05Z | 2019-12-25T21:55Z | 287 | Christmas-associated |
| 2019 | 2019-12-31T22:05Z | 2019-12-31T23:55Z | 23 | Year-end, UTC-shard-boundary fragment |

All 13 runs total **2,349 distinct missing five-minute timestamps per pair** (195.75 hours of M5 slots per pair). These are shared four-way, not 9,396 independent intervals. Exactly 11 runs are Christmas/New Year-associated; the other two are 2019 Sundays. Because the archive is UTC-year-sharded, 2017-12-31/2018-01-01 and 2018-12-31/2019-01-01 must not be misconstrued as independent documented market closures; merging across shards is a *diagnostic view only*, never an edit to original files.

## Documentary status
- OANDA's **current** regular trading hours specify Sunday 17:05 to Friday 16:59 New York, with daily break: https://www.oanda.com/au-en/trading/hours-of-operation/
- Its US and Australian holiday-trading-hours pages illustrate that Christmas and New Year can have altered FX schedules, but they are **not period-specific evidence for 2016–2019**: https://www.oanda.com/us-en/trading/holiday-trading-hours/ and https://www.oanda.com/au-en/trading/holiday-trading-hours/
- Older official document describing approximate Sun 5pm to Fri 5pm NY: https://www.oanda.com/assets/documents/402/Hours_of_Operation_bT4prdz.pdf ; does not establish exact 2016–2019 dates/hours.

No located independent official OANDA historical 2016–2019 notice has yet verified any of these thirteen exact missing intervals. Holiday-related runs = **PLAUSIBLE CANDIDATES / UNVERIFIED**; 2019-10-20 and 2019-12-08 = **UNEXPLAINED**, not assumed to be market closures or data acquisition defects. Missing candles cannot self-authorize removal of reference-calendar timestamps.

## Next outcome-blind steps
1. Distinguish whole missing runs from UTC-year boundary fragments; compare corresponding year-end windows across adjacent 2016–2019 development shards using timestamp-only diagnostic logic, without source mutation.
2. For two 2019 Sunday anomalies, inspect only the surrounding missing-timestamp boundaries and any preexisting non-price request/page provenance; investigate official historical OANDA system/trading notices, preserving gaps as unresolved absent such evidence.
3. Aggregate short and intermediate gap patterns (per pair/daypart/overlap), with predeclared session-research exclusion masks and explicitly stated selection limitations; avoid prices or strategy results.
4. Independently rerun the existing complete RND-0030 verifier before considering even narrowly scoped empirical access, and seek human disposition. Do not silently promote documentary candidates.

**Authority:** source manifests quarantined and `seal_allowed=False`; no calendar promotion, no strategy evaluation, no protected-period access, no broker writes, no spend.
