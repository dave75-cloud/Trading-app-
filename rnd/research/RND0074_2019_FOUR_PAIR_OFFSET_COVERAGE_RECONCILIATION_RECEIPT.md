# RND-0074 — Four-pair 2019 session-offset coverage reconciliation

**Status: 24/24 OPERATOR-REPORTED AGGREGATE RECONCILIATION MATCH; SOURCE QUARANTINED; DATA NOT ADMITTED.**

The operator executed `rnd/tools/rnd0074_session_offset_coverage.py` from detached code commit `5ba19cc1e6a6d809008e7bd27d35974ccf1ec9ae` on the development-only 2019 archive. New JSON offset auditor outputs from AUDUSD, GBPUSD and USDJPY were compared to the earlier recorded six-boundary coarse auditor receipts; EURUSD's matching run was recorded separately. All reported `METADATA_ONLY_PASS` and `Admitted: False`.

For each currency: Tokyo OPEN baseline expected M5 = 3126; Tokyo CLOSE, London OPEN/CLOSE, New York OPEN/CLOSE baseline expected M5 = 3132 apiece. All six values match the prior implementation for each currency; **24/24 aggregate comparisons match**.

| Pair | Tokyo OPEN missing (sensitivity) | Tokyo CLOSE missing (sensitivity) | London OPEN missing (sensitivity) | London CLOSE missing (sensitivity) | NY OPEN missing (sensitivity) | NY CLOSE missing (sensitivity) | All-six missing |
|---|---|---|---|---|---|---|---|
| AUDUSD | 62 (44) | 32 (8) | 29 (5) | 31 (7) | 43 (19) | 213 (189) | 410 |
| EURUSD | 55 (37) | 26 (2) | 25 (1) | 24 (0) | 28 (4) | 62 (38) | 220 |
| GBPUSD | 71 (53) | 24 (0) | 24 (0) | 24 (0) | 24 (0) | 63 (39) | 230 |
| USDJPY | 30 (12) | 24 (0) | 29 (5) | 25 (1) | 25 (1) | 44 (20) | 177 |
| **Total** | **218** | **106** | **107** | **104** | **120** | **382** | **1037** |

Sensitivity-only missing totals: AUDUSD 272; EURUSD 82; GBPUSD 92; USDJPY 39; summed **485**. Every boundary uses local weekdays in 2019, and the sensitivity separately omits local January 1 and December 25 only, **without changing the source reference calendar or establishing historical trading closures**.

Across all 24 windows the denominators sum to 75,144 eligible **pair-window occurrences**, with 1,037 missing and 74,107 ledger-present occurrences. These are not necessarily independent timestamps; windows may overlap. Reconciliation occurs against the **same original reference ledgers**, not independently sourced canonical price files.

Notable AUDUSD NY CLOSE: 213/3132 baseline missing (93.1992% coverage); 189/3108 missing in the two-date sensitivity. This is an instrument-specific timestamp-availability research issue, not proof of liquidity, provider failure, market closure, order execution or economic edge.

**Outstanding protocol requirements:** full per-offset/month/weekday canonical report review, denominator and UTC-year boundary edge-case tests, affected-date counts, exact cross-pair offset coincidence in canonical implementation, underlying original RND-0030 complete raw-page/semantic provenance verification, and period-specific OANDA calendar documentary resolution. Retain original `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False`; no strategy, quote access, broker writes, protected periods, calendar promotion, PR merge, or paid data provider usage authorized.
