# RND-0074 — 2019 NY CLOSE Four-Pair Offset Sensitivity Receipt

**Status:** OPERATOR-REPORTED, DEVELOPMENT-ONLY, TIMESTAMP-ONLY SENSITIVITY; NO ADMISSION, NO CALENDAR PROMOTION.

Using existing `standard_schedule.json` and `discrepancy_ledger.json` in the 2019 RND-0033 quarantined development archive, the operator compared the ±30-minute window around illustrative 16:00 America/New_York local closing boundary on weekdays. For this *separate sensitivity calculation only*, January 1 and December 25 were excluded; original source ledgers and baseline calendar remain unchanged. All 12 offset slots are baseline-eligible on 259 remaining weekdays per pair (259 × 12 = 3,108).

| Offset from 16:00 NY | Expected each pair | AUDUSD missing | EURUSD missing | GBPUSD missing | USDJPY missing |
|---|---:|---:|---:|---:|---:|
| -30 | 259 | 11 | 5 | 1 | 2 |
| -25 | 259 | 12 | 2 | 2 | 2 |
| -20 | 259 | 12 | 4 | 2 | 2 |
| -15 | 259 | 8 | 2 | 3 | 2 |
| -10 | 259 | 6 | 2 | 1 | 1 |
| -5 | 259 | 4 | 1 | 2 | 1 |
| 0 | 259 | 6 | 2 | 1 | 1 |
| +5 | 259 | 21 | 3 | 1 | 1 |
| +10 | 259 | 24 | 3 | 5 | 1 |
| +15 | 259 | 43 | 3 | 7 | 2 |
| +20 | 259 | 32 | 9 | 8 | 3 |
| +25 | 259 | 10 | 2 | 6 | 2 |
| **Total missing** | **3108** | **189** | **38** | **39** | **20** |
| **Coverage %** | | **93.9189%** | **98.7773%** | **98.7452%** | **99.3565%** |

At +15 and +20 combined, AUDUSD is missing 75/518=14.48% of slots, EURUSD 12/518=2.32%, GBPUSD 15/518=2.90%, USDJPY 5/518=0.97%. The earlier all-days audit for these pairs contained AUDUSD=213, EURUSD=62, GBPUSD=63, USDJPY=44 missing slots; removing two 12-slot fully missing holidays per pair reconciles each sum.

**Interpretation:** the AUDUSD-specific 16:15 and 16:20 NY local clock concentration persists outside the two specified holiday dates, compared with other observed pairs. Causes remain unknown. Do not infer actual liquidity, broker execution quality, missing quotes, provider outages, historically valid holidays, actual OANDA market close, or strategy performance. These are overlapping window observations across time; aggregate percentages are descriptive, not independent trials. The particular 16:00 session clock is an illustrative, predeclared convention.

**Next decision before admission:** assess whether AUDUSD's large gap count is concentrated in a narrow part of 2019 (month/date) versus dispersed over the year, and whether the AUDUSD +15/+20 missing timestamps coincide with gaps in other pairs, using only timestamps in the original ledgers. Year boundary, holidays, DST, integrity and provenance remain explicit. Do not retroactively exclude bad-looking offsets from any future analysis without predeclared design, independent validation and human authority. Source status remains `QUARANTINED_UNRESOLVED_DISCREPANCIES`, seal_allowed=false, and no prices, orders, provider spend, protected years or outcomes opened.
