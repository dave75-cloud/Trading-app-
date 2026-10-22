# RND-0074 — 2019 four-pair metadata/file-hash audit receipt

**Status: OPERATOR-REPORTED STRUCTURAL METADATA CHECK PASS (4/4); EVIDENCE ADMISSION = FALSE.**

Operator ran `rnd/tools/rnd0074_development_metadata_audit.py` on the 2016–2019 development archive, with `--year 2019`, first EURUSD and then AUDUSD, GBPUSD, USDJPY, using the locally tested commit `df2c63816ea722d86ed9a8c4ed1d59b265228b8d`. All reported `RND0074_METADATA_AUDIT: STRUCTURAL_METADATA_CHECK_PASS`, `hashes_checked=True`, `admitted=False`, `source_quarantine_unchanged=TRUE`, `strategy_evaluation=FALSE` and `calendar_promotion=FALSE`.

| Pair | Rows | Missing | Unexpected | Unexpected at 17:00 NY | Short bars/runs | Intermediate bars/runs | Closure-shaped bars/runs | Missing NY hours 16–18 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AUDUSD | 72912 | 2232 | 237 | 237 | 1411 / 1165 | 194 / 38 | 627 / 5 | 1007 |
| EURUSD | 73983 | 1182 | 258 | 258 | 508 / 442 | 47 / 9 | 627 / 5 | 467 |
| GBPUSD | 73852 | 1317 | 262 | 262 | 662 / 572 | 28 / 5 | 627 / 5 | 448 |
| USDJPY | 74273 | 903 | 269 | 269 | 252 / 221 | 24 / 4 | 627 / 5 | 289 |
| **Aggregate** | **295020** | **5634** | **1026** | **1026** | **2833 / 2400** | **293 / 56** | **2508 / 20** | **2211** |

The aggregate counts are **pair-timestamp occurrences**, not distinct timestamps; common occurrences across pairs must not be double-counted as independent events. The five long missing runs of 627 M5 bars are **equal in total length for each pair**; coincidence of their exact start and end times has *not* yet been confirmed. Short/intermediate gap intensity differs across pairs.

This tool checked manifest identity/status, file SHA-256 digests, schedule/discrepancy timestamp integrity and membership/count reconciliation. It does not independently reparse prices, raw-page response semantics, or perform the complete RND-0030 shard verifier. Existing `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False` remain controlling. No candles interpolated, no missing runs promoted to verified closure, no economic outcomes consulted, no protected evidence opened, no broker writes or cost commitments.

## Next bounded decision
1. Continue identical read-only audit for 2018 and then earlier 2016–2017 development shards. Stop on any failure.
2. With integrity confirmed, compare structural timestamp overlap across instruments for the five closure-shaped runs; only independently dated official source can authenticate market closures.
3. Prepare human-reviewed intended-use decision separately from structural PASS.
