# RND-0074 — 2019 residual missing-timestamp overlap receipt

**Status: HUMAN-REPORTED READ-ONLY DEVELOPMENT-ONLY TIMESTAMP COMPARISON; NOT EVIDENCE ADMISSION.**

The operator read the four 2019 RND-0033 `discrepancy_ledger.json` files from the development-only archive, partitioned each pair's missing timestamps into consecutive 5-minute runs, and extracted timestamps belonging to runs of fewer than 12 missing intervals (RND-0031 short + intermediate categories). These *pair-specific* residual timestamp sets were compared through a four-way intersection.

| Pair | Residual missing timestamps | Present in all four residual sets | Not present in all four residual sets |
|---|---:|---:|---:|
| AUDUSD | 1605 | 25 | 1580 |
| EURUSD | 555 | 25 | 530 |
| GBPUSD | 690 | 25 | 665 |
| USDJPY | 276 | 25 | 251 |

The four-way shared residual set consists of 25 distinct missing M5 timestamp identifiers. In contrast, earlier verified operator checks identified the same 627 long-gap missing timestamp identifiers across all four pairs in 2019. **Caution:** the residual definition selects runs *per pair*, so a timestamp's membership in a different pair's long run would not count as residual there. `Not shared by all four` does **not** mean `pair-unique`: overlap of two or three is unknown until separately computed. It is equally not evidence of low liquidity, a valid calendar closure, or a data acquisition defect.

Next: print aggregate membership counts (missing residual timestamp occurrence in exactly 1, 2, 3 or 4 pairs), pairwise residual intersections and totals in 2019, preserving the per-pair run-length definition. Do not print market prices, signals or any protected period. No modifications to evidence or original `QUARANTINED_UNRESOLVED_DISCREPANCIES` statuses, no strategy authorization, orders or provider spend.
