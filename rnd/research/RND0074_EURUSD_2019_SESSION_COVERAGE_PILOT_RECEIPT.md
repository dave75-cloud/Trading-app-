# RND-0074 — EURUSD 2019 session-boundary coverage pilot receipt

**Status: OPERATOR-REPORTED METADATA_ONLY_PASS; NO EVIDENCE ADMISSION.**

Using detached development commit `01088f9ac3eba6b11b9041549e3520bd065bc36f`, the operator ran `rnd/tools/rnd0074_session_coverage_audit.py --root ~/Trading-evidence/rnd0033-development-history-2016-2019 --pair EURUSD --year 2019`. The auditor performs the existing bounded five-file SHA-256/manifest/ledger checks, then reads original reference schedule and missing/unexpected timestamp ledgers (no market price parsing). Six aggregate research windows are fixed to ±30 minutes around the *illustrative*, not verified exchange/dealer, Tokyo (09:00/17:00 local), London (08:00/16:00 local) and New York (08:00/16:00 local) session conventions; weekday dates use IANA timezone rules including DST.

| Boundary | Weekday windows | Zero-eligible windows | Baseline expected M5 | Baseline present M5 | Baseline missing M5 | Coverage % | Unexpected timestamps in windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| TOKYO OPEN | 261 | 0 | 3126 | 3071 | 55 | 98.2406 | 0 |
| TOKYO CLOSE | 261 | 0 | 3132 | 3106 | 26 | 99.1699 | 0 |
| LONDON OPEN | 261 | 0 | 3132 | 3107 | 25 | 99.2018 | 0 |
| LONDON CLOSE | 261 | 0 | 3132 | 3108 | 24 | 99.2337 | 0 |
| NEW_YORK OPEN | 261 | 0 | 3132 | 3104 | 28 | 99.1060 | 0 |
| NEW_YORK CLOSE | 261 | 0 | 3132 | 3070 | 62 | 98.0204 | 0 |

Descriptive pooled window-count coverage: 18,566 present / 18,786 baseline expected = 98.828%; 220 missing pair-window occurrences. **This is not a sample-size estimate of independent observations:** window timestamps can overlap, and eligibility depends on the unchanged contested original schedule. In particular, Christmas/New Year apparent closures may contribute missing counts; and 17:00 New York excluded baseline rows are not automatically admitted. The six rows all reconcile expected = present + missing. Zero unexpected returned within these particular windows does not resolve the full-year 17:00 NY timestamp discrepancy.

Operator output explicitly: `RND0074_SESSION_COVERAGE: METADATA_ONLY_PASS`, `original_evidence_admitted=FALSE`, `original_quarantine_unchanged=TRUE`, `market_prices_opened=FALSE`, `broker_writes=FALSE`.

**Disposition:** proceed to the **remaining three pairs' metadata-only 2019 windows**, subject to review of their aggregate outputs. No threshold for formal evidence quality/admission has been validated or declared. This result is neither historical calendar verification nor proof of liquidity/tradability/strategy edge. Quarantine and human approvals remain in force; OANDA practice read-only and Trading Economics trial not activated.
