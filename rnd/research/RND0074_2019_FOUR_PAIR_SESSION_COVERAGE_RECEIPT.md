# RND-0074 — 2019 Four-Pair Session-Boundary Coverage Receipt

**Status: OPERATOR-REPORTED METADATA_ONLY_PASS (4/4); NOT EVIDENCE ADMISSION.**

Existing code checked out by the operator at detached `01088f9ac3eba6b11b9041549e3520bd065bc36f`. After EURUSD passed, the operator ran `rnd0074_session_coverage_audit.py` sequentially on AUDUSD, GBPUSD and USDJPY, year 2019, development-only RND-0033 archive. Each reported `RND0074_SESSION_COVERAGE: METADATA_ONLY_PASS`, `original_evidence_admitted=FALSE`, `original_quarantine_unchanged=TRUE`, `market_prices_opened=FALSE`, `broker_writes=FALSE`. Earlier separate EURUSD receipt records identical status.

All boundaries use *illustrative, not documented venue/dealer* session local clock conventions from the frozen 2019 clock rehearsal, with ±30 minutes around each open and close. Each has 261 local weekday windows, zero zero-eligible windows, 0 unexpected provider timestamps counted within those windows. Baseline denominators: TOKYO OPEN 3126 M5 per pair; all other boundaries 3132 M5 per pair.

| Session | Boundary | AUDUSD present/missing/coverage% | EURUSD present/missing/coverage% | GBPUSD present/missing/coverage% | USDJPY present/missing/coverage% |
|---|---|---|---|---|---|
| TOKYO | OPEN | 3064/62/98.0166 | 3071/55/98.2406 | 3055/71/97.7287 | 3096/30/99.0403 |
| TOKYO | CLOSE | 3100/32/98.9783 | 3106/26/99.1699 | 3108/24/99.2337 | 3108/24/99.2337 |
| LONDON | OPEN | 3103/29/99.0741 | 3107/25/99.2018 | 3108/24/99.2337 | 3103/29/99.0741 |
| LONDON | CLOSE | 3101/31/99.0102 | 3108/24/99.2337 | 3108/24/99.2337 | 3107/25/99.2018 |
| NEW_YORK | OPEN | 3089/43/98.6271 | 3104/28/99.1060 | 3108/24/99.2337 | 3107/25/99.2018 |
| NEW_YORK | CLOSE | 2919/213/93.1992 | 3070/62/98.0204 | 3069/63/97.9885 | 3088/44/98.5951 |

**Notable diagnostic:** AUDUSD New York CLOSE has 213 missing baseline-eligible M5 timestamps (93.1992% coverage), substantially worse than EURUSD 62, GBPUSD 63 and USDJPY 44. GBPUSD Tokyo OPEN is the next-lowest boundary coverage (97.7287%). None of these figures measures actual liquidity, zero trades, candle quality or execution feasibility. No quality threshold or formal admission decision is implied by `METADATA_ONLY_PASS`.

**Next narrowly bounded research:** investigate the AUDUSD 2019 New York CLOSE missing timestamps at date/day-of-week/minute-offset aggregation, using only already-hashed `standard_schedule.json` and `discrepancy_ledger.json` ledgers, optionally separating dates shared across four pairs. Avoid individual candle prices and strategies, retrospective change of selection windows or calendar promotion. Identify holidays/year-end contamination explicitly. To maintain the original year/calendar authority, no inferred gap closing, source resealing, or source edits. RND-0030 full original verifier still not rerun; all source manifests quarantined with `seal_allowed=False`.

Incremental provider spend: USD 0. OANDA PRACTICE read-only, no broker order writes, protected validation/reserved final/prospective outcomes remain unopened.
