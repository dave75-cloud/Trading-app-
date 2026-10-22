# RND-0074 — Four-pair 2018 development metadata audit receipt

**Status: OPERATOR-REPORTED STRUCTURAL METADATA PASS (4/4); SOURCE REMAINS QUARANTINED.**

Operator ran `rnd/tools/rnd0074_development_metadata_audit.py` against four 2018 shards in `~/Trading-evidence/rnd0033-development-history-2016-2019`, using locally test-verified code from `df2c63816ea722d86ed9a8c4ed1d59b265228b8d`. All four executions reported `STRUCTURAL_METADATA_CHECK_PASS`, `hashes_checked=True`, `admitted=False`, `source_quarantine_unchanged=TRUE`, `strategy_evaluation=FALSE` and `calendar_promotion=FALSE`.

| Pair | Rows | Missing | Unexpected | Unexpected at 17:00 NY | Short bars/runs | Intermediate bars/runs | Closure-shaped bars/runs | Missing NY hours 16–18 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AUDUSD | 74045 | 1121 | 259 | 259 | 529 / 445 | 18 / 4 | 574 / 3 | 481 |
| EURUSD | 74499 | 667 | 259 | 259 | 93 / 85 | 0 / 0 | 574 / 3 | 141 |
| GBPUSD | 74499 | 667 | 259 | 259 | 93 / 86 | 0 / 0 | 574 / 3 | 113 |
| USDJPY | 74470 | 697 | 260 | 260 | 119 / 95 | 4 / 1 | 574 / 3 | 161 |
| **Aggregate occurrences** | **297513** | **3152** | **1037** | **1037** | **834 / 711** | **22 / 5** | **2296 / 12** | **896** |

All gap bar totals reconcile to each pair's missing count. The three closure-shaped runs total 574 M5 intervals for **each** pair; overlap of their exact timestamps has NOT been independently checked. In 2019, all four pairs likewise had equal closure-shaped totals (627 M5 bars each), with five runs per pair.

A limited read-only audit checked the five recorded file hashes, manifest identity, schedule/ledger timestamp consistency, count and set reconciliation; it did **not** execute the full original RND-0030 raw-page/canonical-content verifier. The auditor uses file hashes on canonical bytes but does not parse prices or strategy outcomes.

Any apparent calendar pattern is non-authoritative. Neither documentary market-closure confirmation nor performance-grade evidence admission is established. Original `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False` remain unchanged. Protected validation/final/prospective evidence unopened; no broker writes, no new subscriptions and no trial activation.

Next scope: apply the same unchanged read-only auditor to development-only 2017 pair-years. Stop on the first audit failure.
