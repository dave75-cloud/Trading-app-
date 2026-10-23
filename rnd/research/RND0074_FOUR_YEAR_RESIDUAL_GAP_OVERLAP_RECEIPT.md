# RND-0074 — Four-year residual gap membership receipt

**Status:** OPERATOR-REPORTED DEVELOPMENT-ONLY TIMESTAMP-STRUCTURE ANALYSIS; NO ADMISSION.

Read-only analysis across 2016–2019 RND-0033 development discrepancy ledgers: for each pair and UTC-year shard, consecutive missing M5 timestamps were grouped into runs. **Residual** here means timestamps belonging to runs shorter than 12 M5 slots *for that pair*, consistent with the existing RND-0031 short/intermediate classifications. Four-pair membership was counted over distinct timestamp strings separately for each year.

| Year | Distinct residual timestamps | Exactly 1 pair | Exactly 2 | Exactly 3 | Exactly 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2016 | 732 | 658 | 51 | 8 | 15 |
| 2017 | 1029 | 960 | 40 | 1 | 28 |
| 2018 | 799 | 750 | 44 | 2 | 3 |
| 2019 | 2694 | 2349 | 283 | 37 | 25 |
| **Total** | **5254** | **4717** | **418** | **48** | **71** |

Weighted accounting: `4717 + 2*418 + 3*48 + 4*71 = 5981` missing pair-timestamp occurrences. Exactly one residual set contains 4717/5254 = 89.78% of distinct timestamps. This is **not** proof of exactly-one-pair missingness in the full ledger: per-pair long-run and residual-run classifications can differ at the same timestamp. No outcome data or market quotes inspected.

Prior structural audit reported 16/16 limited metadata and file-hash checks PASS, and 2,349 *distinct* closure-shaped missing intervals in 13 runs coincident across all four instruments over the four years. Long and residual gap categories are based on run length only; neither establishes verified closure or cause.

## Admission implications
- Define pair × local session/daypart expected M5 exposure from the *unchanged* baseline calendar, plus counts of available/absent timestamps, before analyzing spreads. Distinguish missing from the current calendar's excluded 17:00 NY entries.
- Predeclare omission/gap handling and report variation in availability across pairs and sessions. No fill-forward, synthetic candles, assumed zero liquidity, or selective dropping of inconvenient observations.
- Verify exact timestamp overlap and independent provider notice before any historic closure claim. Capture checksums, code version and all sources in a prospective audit receipt.
- A four-way intersection of pair-specific residual sets does not measure every pairwise/provider-wide missing timestamp; diagnostic counts do not establish causal mechanism.
- Original source status `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False` unchanged, and no strategy evaluation, evidence promotion, orders, protected-window access or vendor spend allowed.

## Next audit priority
Outcome-blind missingness exposure audit by New York local time and established session-handoff clock bands on the **2016–2019 development-only reference calendar**, keeping the 17:00 mismatch explicit. This is descriptive design/protocol work only; independent human authorization and full provenance verification are still required before empirical liquidity analysis.
