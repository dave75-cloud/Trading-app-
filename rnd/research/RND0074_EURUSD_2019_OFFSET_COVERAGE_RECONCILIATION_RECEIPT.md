# RND-0074 — EURUSD 2019 offset-level coverage reconciliation

**Status: OPERATOR-REPORTED METADATA_ONLY_PASS; SIX OF SIX AGGREGATE WINDOWS MATCH PREVIOUS COVERAGE PILOT. NO EVIDENCE ADMISSION.**

Operator ran `rnd/tools/rnd0074_session_offset_coverage.py` at checked-out implementation commit `5ba19cc1e6a6d809008e7bd27d35974ccf1ec9ae` on the development-only EURUSD/2019 shard, with compact JSON-summary output and pipeline `set -o pipefail`. Report: `Status: METADATA_ONLY_PASS Pair: EURUSD`, `Admitted: False`.

| Session boundary | Eligible original baseline M5 | Missing M5 | Coverage % | Missing M5 excluding Jan 1 / Dec 25 local dates (sensitivity only) |
|---|---:|---:|---:|---:|
| LONDON_CLOSE | 3132 | 24 | 99.2337 | 0 |
| LONDON_OPEN | 3132 | 25 | 99.2018 | 1 |
| NEW_YORK_CLOSE | 3132 | 62 | 98.0204 | 38 |
| NEW_YORK_OPEN | 3132 | 28 | 99.106 | 4 |
| TOKYO_CLOSE | 3132 | 26 | 99.1699 | 2 |
| TOKYO_OPEN | 3126 | 55 | 98.2406 | 37 |

All six primary aggregate values match the earlier `RND0074_EURUSD_2019_SESSION_COVERAGE_PILOT_RECEIPT.md`. This is **agreement between two implementations against the same archival ledgers**, not independent source authenticity, historical provider hours, or economic validity. Each sensitivity is a separately reported view; it does not alter the baseline or verify exact holiday closures.

The auditor performs the existing limited RND-0074 manifest/file hash gate, not the full RND-0030 raw-page/semantic verifier. The original source status remains `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False`. No prices parsed, no strategies run, no broker writes, no protected periods opened, no source/calendar modification or vendor costs.

**Next:** run the same six-window aggregate check for AUDUSD, GBPUSD and USDJPY 2019 on this exact code commit, compare all 24 previously recorded coarse primary windows and review holiday-sensitivity differences. Do not infer admission from matches.
