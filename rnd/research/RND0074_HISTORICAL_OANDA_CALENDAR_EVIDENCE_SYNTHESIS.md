# RND-0074 — Historical OANDA calendar evidence synthesis

**Disposition: RESEARCH REVIEW ONLY / NO CALENDAR ADMISSION / NO RESEAL.**
Prepared 2026-10-22. Scope: already-existing development-period acquisition diagnostics, not strategy returns.

## Prior controlling work
- `rnd/orchestration/oanda_market_calendar.py` (RND-0030) intentionally excludes 17:00 New York M5 candle starts, uses Sunday 17:05, Friday final 16:55 and `America/New_York` for DST.
- `rnd/research/OANDA_CALENDAR_QUARANTINE_CONTRACT.md` distinguishes outcome-blind acquisition from sealing and requires *independent* documentary evidence of historical exceptions; returned candles cannot establish their own calendar authority.
- `rnd/orchestration/historical_calendar_evidence.py` (RND-0031) already implements a **non-authoritative** candidate that adds Sunday–Thursday 17:00 NY candle starts, preserves the baseline and classifies gap runs.
- `rnd/research/RND0031_HISTORICAL_CALENDAR_EVIDENCE_CONTRACT.md`: AUDUSD 2015 unexpected 255 -> candidate remaining 1; 254 explained (99.6078%). One residual Friday 17:05 NY observation; candidate missing = 856, of which 648 closure-shaped and 208 short-run bars. Prior review explicitly could not locate precise 2015 calendar authority.
- `rnd/research/RND0036_CALENDAR_CLASSIFICATION_RECEIPT.json`: 2020 baseline unexpected AUDUSD 243, EURUSD 258, GBPUSD 258, USDJPY 256; candidate unexpected **0 across all four**. Missing remains unresolved (reported short 568/272/318/294, closure-shaped 564/564/564/563, unclassified 38/22/20/41 bars).

## Newly reported 2016–2019 metadata
Operator-read development-only discrepancy ledgers (unverified independently against file SHA in this review):

| Year | Unexpected pair-timestamps | At 17:00 New York | Other |
| --- | ---: | ---: | ---: |
| 2016 | 1008 | 1008 | 0 |
| 2017 | 1014 | 1006 | 8 |
| 2018 | 1037 | 1037 | 0 |
| 2019 | 1026 | 1026 | 0 |
| **Total** | **4085** | **4077** | **8** |

2017 eight exceptions = 2017-10-06 21:05 UTC (Friday 17:05 EDT) and 2017-10-20 21:10 UTC (Friday 17:10 EDT), each shared by all four pairs. They were **not** New York DST changeovers.
The EURUSD/2019 standard schedule has 74,907 entries and **zero** 17:00 New York starts; nearby starts are included Monday–Thursday. EURUSD/2019 baseline: actual 73,983; expected 74,907; missing 1,182; unexpected 258; 467 missing are in NY clock hours 16, 17 or 18; 715 elsewhere. Do not treat any missing interval as an authorized closure based on this aggregation.

2015 + 2016–2019 + 2020 constitute six development years, though sources, review status and evidence construction differ. Do not combine into a single performance-grade admission statistic.

## Independent official-source review (2026-10-22)
1. OANDA v20 **Instrument Definitions** identifies `Candlestick.time` as the **start time** of a candlestick and `complete` as a separate flag; M5 is hour-aligned: https://developer.oanda.com/rest-live-v20/instrument-df/
2. Current OANDA Australia operating hours specify ordinary FX daily break 16:59–17:05 NY, weekly opening Sunday 17:05 and Friday closing 16:59: https://www.oanda.com/au-en/trading/hours-of-operation/
3. Current OANDA US operating hours provide the same ordinary trading hours: https://www.oanda.com/us-en/trading/hours-of-operation/
4. An older OANDA *Hours of Operation* PDF, found with publication age ~6.8 years as of 2026-10-22, describes approximate Sunday 5 pm–Friday 5 pm New York but does not in the excerpt specify precise historical daily breaks: https://www.oanda.com/assets/documents/471/Hours_of_operation_6.pdf

**Temporal caveat:** API schema explains v20 candle labelling but by itself does not establish invariant 2015–2020 feed behavior. Current trading-hours pages cannot be projected backward. The PDF does not authoritatively establish a precise historical daily six-minute break. The exact historical 17:00 rule, holiday exceptions, post-Friday entries, and why candles may exist during today's declared daily break remain unproven.

## Governing inference and stop conditions
- The candidate 17:00 boundary pattern is strongly corroborated structurally across pairs and years.
- That does **not** imply the baseline generator is a programming bug: it implements the declared contemporary reference rule. Its applicability to older data is the open issue.
- The source `QUARANTINED_UNRESOLVED_DISCREPANCIES` remains controlling. A candidate added to the expected schedule would also cause *missing* 17:00 entries on days without actual candles; the missing ledger must be recomputed, never erased.
- No synthetic price interpolation, forced closure classifications, order endpoints, strategy metrics, protected validation or prospective data, retroactive parameter selection, evidence overwrite, or automatic evidence promotion.
- No authorized Trading Economics or other provider spending.

## Next admitted work
1. Verify provenance/integrity digests of already-held development-only files, with a bounded read-only tool and explicit excludes for protected 2021–2024, prospective and 2025+.
2. Cross-check existing RND-0031 and RND-0036 gap taxonomy; collect aggregate gap-run counts (length and weekday/time bands) from development-only ledgers without opening price rows; treat closure-shaped runs only as candidates.
3. Seek period-specific OANDA notices/archived operating-hour documentary evidence, date and coverage clearly recorded.
4. Human-reviewable split decisions: structural-research use / performance-grade use / continued quarantine; no admission based solely on matching return-data patterns.
