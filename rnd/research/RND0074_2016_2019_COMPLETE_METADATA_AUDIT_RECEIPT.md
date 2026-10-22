# RND-0074 — 2016–2019 Development Archive Metadata Audit Completion

**Status: 16/16 OPERATOR-REPORTED LIMITED STRUCTURAL METADATA & FILE-HASH PASS. NO ADMISSION.**

Operator ran `rnd/tools/rnd0074_development_metadata_audit.py` at checked-out code commit `df2c63816ea722d86ed9a8c4ed1d59b265228b8d` against all four instruments and years 2016–2019 under the development-only `~/Trading-evidence/rnd0033-development-history-2016-2019` archive. All 16 returned `RND0074_METADATA_AUDIT: STRUCTURAL_METADATA_CHECK_PASS` and `hashes_checked=True`, `admitted=False`, `source_quarantine_unchanged=TRUE`, `strategy_evaluation=FALSE`, `calendar_promotion=FALSE`. This is transcribed human-supplied terminal evidence, not an independent GitHub runner execution.

| Year | Pass | Rows total | Missing pair-intervals | Unexpected pair-timestamps | Unexpected at 17:00 NY | Closure-shaped missing bars **per pair** | Runs **per pair** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 4/4 | 297496 | 3048 | 1008 | 1008 | 551 | 2 |
| 2017 | 4/4 | 296043 | 3543 | 1014 | 1006 | 597 | 3 |
| 2018 | 4/4 | 297513 | 3152 | 1037 | 1037 | 574 | 3 |
| 2019 | 4/4 | 295020 | 5634 | 1026 | 1026 | 627 | 5 |
| **Total** | **16/16** | **1186072** | **15377** | **4085** | **4077** | **2349 per pair** | **13 per pair** |

2016 detail:
- AUDUSD: 74,174 rows; missing 955; unexpected 245 all 17:00 NY; short 372 bars/316 runs; intermediate 32/5; closure-shaped 551/2; missing near NY rollover 344.
- EURUSD: 74,437 rows; missing 705; unexpected 258 all 17:00 NY; short 143/131; intermediate 11/1; closure-shaped 551/2; near rollover 159.
- GBPUSD: 74,354 rows; missing 779; unexpected 249 all 17:00 NY; short 201/172; intermediate 27/4; closure-shaped 551/2; near rollover 170.
- USDJPY: 74,531 rows; missing 609; unexpected 256 all 17:00 NY; short 40/36; intermediate 18/2; closure-shaped 551/2; near rollover 87.

**Careful interpretation**:
- 4077/4085 (99.804%) unexpected pair-timestamps map to 17:00 America/New_York. Eight others are the same two October 2017 post-Friday-close timestamp strings across four pairs.
- Each year has identical closure-shaped *counts and bar totals* across pairs. This does **not** verify identical constituent timestamps, valid closures, or documentary authority. Gap classifications are defined exclusively by duration (short <=3, intermediate 4–11, closure-shaped >=12 M5 intervals).
- All 16 source manifests remain `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False`. An equal number of long gap bars can arise from separate timestamps.

**Scope limitations**: The RND-0074 metadata auditor verifies manifest identity, file SHA-256 hashes (including canonical rows byte digest), schedule/discrepancy membership and count reconciliation. It does not parse the price observations, revalidate raw-page hashes, independently recompute canonical rows digests, or run the full RND-0030 verifier. Source files not altered; protected validation/reserved final/prospective data unopened; broker writes prohibited; incremental vendor spend = USD 0.

**Next gate**: Development-only read-only exact cross-pair overlap of the original *missing timestamp strings* for long contiguous runs, with integrity checks preserved and no reclassification or source mutation. Then prepare a distinct human-reviewed proposal for admissible, gap-aware, outcome-blind session-liquidity study; no strategy performance tests are authorised by this receipt.
