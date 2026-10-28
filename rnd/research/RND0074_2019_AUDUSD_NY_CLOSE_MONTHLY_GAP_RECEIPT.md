# RND-0074: AUDUSD 2019 New York close monthly missingness

Operator-reported, read-only analysis of quarantined development-only missing-timestamp metadata. Sensitivity calculation excludes January 1 and December 25, without modifying evidence.

At offsets +15 and +20 minutes from illustrative 16:00 New York boundary, missing M5 timestamp counts by month (January to December): **7, 5, 3, 4, 8, 10, 12, 3, 4, 7, 8, 4**. Total **75** missing out of 518 eligible slots across 259 weekdays, on **68 distinct dates**; seven dates have both offsets missing. The monthly pattern spans all twelve months. The missing rate is 14.48% of eligible pair-offset observations, but the cause is not established.

Earlier same-window comparison: EURUSD 12/518, GBPUSD 15/518, USDJPY 5/518. This is a descriptive coverage issue, not evidence of market liquidity, a broker outage, or trading returns. Holiday exclusions are sensitivity only. Original reference calendar and source quarantine remain unchanged.

**Disposition:** Continue timestamp-only research. No approval for historical data admission, price or strategy inspection, broker orders, protected-period access, calendar changes or new subscriptions. Next check month-specific denominators and pairwise overlap using original timestamp ledgers. Original source manifest status remains QUARANTINED_UNRESOLVED_DISCREPANCIES with seal_allowed=false.
