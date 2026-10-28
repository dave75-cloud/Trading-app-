# RND-0074 — AUDUSD 2019 detailed NY-close offset reconciliation

**Status: OPERATOR-REPORTED METADATA_ONLY_PASS; DETAILED COUNTS RECONCILE; ADMITTED FALSE.**

The operator ran `rnd/tools/rnd0074_session_offset_coverage.py` from detached code commit `5ba19cc1e6a6d809008e7bd27d35974ccf1ec9ae` on the quarantined development-only AUDUSD/2019 archive. After a prior *display-only* Python command caused `KeyError: 'offset'` because it assumed a nested JSON key that does not exist, the corrected stdout summarizer accessed flat keys `offset:+15`, `offset:+20`, `month:01` etc. No underlying auditor or archive modification was required.

Observed: `Status: METADATA_ONLY_PASS`, `Admitted: False`.

| Local NY offset from 16:00 | Eligible M5 timestamps | Missing M5 timestamps | Coverage |
|---|---:|---:|---:|
| +15 (16:15) | 259 | 43 | 83.3977% |
| +20 (16:20) | 259 | 32 | 87.6448% |
| **Both offsets** | **518** | **75** | **85.5212%** |

The separate Jan 1/Dec 25 *sensitivity view* across the full ±30-minute NY closing window has **189 missing** out of **3,108** baseline-eligible timestamp occurrences (93.9189% coverage). Monthly sensitivity missing counts across this **full window**, January–December: **8, 10, 7, 19, 18, 18, 29, 10, 19, 13, 28, 10**, summing to 189. These monthly full-window totals must not be mistaken for the earlier two-offset monthly totals (7,5,3,4,8,10,12,3,4,7,8,4), which sum to 75.

This matches the prior exploratory 2019 AUDUSD +15/+20 missing counts (43 and 32) and the earlier whole-window sensitivity missing count (189), all against the **same immutable historical ledgers**, not independent provider price verification.

The 2019 reference calendar remains contested. The RND-0074 limited SHA/manifest checks do not supersede the full RND-0030 raw-page and semantic provenance verifier. Original shards remain `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False`; no candle price analysis, economic outcomes, strategy evaluation, calendar promotion, original-file write, broker order call, protected-period access, PR merge authorization or new subscription is implied.

**Next:** Add a formally tested affected-local-date count and cross-pair exact missing-timestamp overlap to the versioned report, then run the synthetic tests before local archival diagnostic use.
