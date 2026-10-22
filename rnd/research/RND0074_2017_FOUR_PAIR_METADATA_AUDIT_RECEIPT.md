# RND-0074 — Four-pair 2017 development metadata audit receipt

**Status: OPERATOR-REPORTED STRUCTURAL METADATA CHECK PASS (4/4); ADMISSION FALSE.**

The operator executed `rnd/tools/rnd0074_development_metadata_audit.py` on AUDUSD, EURUSD, GBPUSD and USDJPY 2017 shards under `~/Trading-evidence/rnd0033-development-history-2016-2019`. All four outputs report `STRUCTURAL_METADATA_CHECK_PASS`, `hashes_checked=True`, `admitted=False`, `source_quarantine_unchanged=TRUE`, `strategy_evaluation=FALSE` and `calendar_promotion=FALSE`.

| Pair | Rows | Missing | Unexpected | Unexpected at NY 17:00 | Unexpected elsewhere | Short bars/runs | Intermediate bars/runs | Closure-shaped bars/runs | Missing near NY rollover |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AUDUSD | 73517 | 1375 | 249 | 247 | 2 | 700/598 | 78/14 | 597/3 | 593 |
| EURUSD | 74192 | 707 | 256 | 254 | 2 | 84/77 | 26/3 | 597/3 | 157 |
| GBPUSD | 74111 | 787 | 255 | 253 | 2 | 164/149 | 26/3 | 597/3 | 153 |
| USDJPY | 74223 | 674 | 254 | 252 | 2 | 51/44 | 26/3 | 597/3 | 154 |
| **Aggregate pair-occurrences** | **296043** | **3543** | **1014** | **1006** | **8** | **999/868** | **156/23** | **2388/12** | **1057** |

The eight non-17:00 unexpected pair-timestamp occurrences match the earlier operator-inspected 2017 exceptions (2017-10-06T21:05Z and 2017-10-20T21:10Z, each present for four pairs). The three long-gap runs contain 597 M5 bars per pair. **Equal bar/run totals do not prove exact timestamp coincidence, verified closures or independent authority.**

This audit verified a limited set of recorded file SHA-256 hashes, manifest identity and timestamp-ledger invariants; it did not perform the complete original RND-0030 semantic/raw-page verifier or parse market prices. Gap-run classes are descriptive only. `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False`, and separate human admission requirements remain controlling. No original evidence altered, protected years opened, trading permissions increased or subscription activated.

Next: repeat unchanged development-only 2016 pair-year audit, then examine cross-pair exact timestamp overlap of long missing runs without opening candle prices.
