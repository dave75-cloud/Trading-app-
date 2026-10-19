# RND-0074 — EURUSD 2019 Rollover Discrepancy Diagnostic

Status: USER-REPORTED READ-ONLY METADATA DIAGNOSTIC; NOT AN EVIDENCE RESEAL.

## Source
Local archive `~/Trading-evidence/rnd0033-development-history-2016-2019/EURUSD/2019/discrepancy_ledger.json`, originally `QUARANTINED_UNRESOLVED_DISCREPANCIES`. The human operator ran read-only analyses of timestamp strings and supplied outputs in conversation. The source bytes and SHA-256 have not been independently rechecked in this task.

## Observations
- EURUSD 2019 canonical row count 73,983; expected session slots 74,907; missing 1,182; unexpected 258. Identity: 74,907 - 1,182 + 258 = 73,983.
- Exactly 258 / 258 unexpected timestamp strings mapped to 17:00 `America/New_York`, including 170 at 21:00 UTC and 88 at 22:00 UTC.
- 0 missing timestamps mapped to exactly 17:00 New York.
- 467 / 1,182 missing timestamps mapped to New York local clock hours 16, 17 or 18; remaining 715 were outside those clock hours.
- Original manifest: `seal_allowed=False`; `seal_block_reason=UNRESOLVED_CALENDAR_DISCREPANCIES`; `complete_candles_only=True`; `empty_raw_page_count=0`; OANDA PRACTICE M5 bid/ask/mid.

## Inference and limit
The data are strongly **consistent with** a systematic daily rollover boundary convention mismatch. Do NOT infer that the actual candle is a valid trading interval, that the provider or reference calendar is incorrect, that the missing timestamps are explained, or that the archive passes sealing requirements. Candle label semantics (open/close), daily session timing, Sunday reopen, DST and provider documentation must be independently checked.

## Next outcome-blind diagnostic
Repeat the same aggregate NY-local-clock test on other *development-only* discrepancy ledgers (2016–2020), first checking that manifest status, package identity, and schema agree. Print counts only (not raw prices, strategy returns, validation, prospective, or protected data). Compare how many unexpected timestamps map to 17:00 NY and group the missing timestamps by clock hour. Preserve every original discrepancy and hash; do not change the schedule, quarantine or sealing status.

## Decision
NON-ECONOMIC METADATA PATTERN IDENTIFIED. DEVELOPMENT DATA ADMISSION STILL BLOCKED. NO PURCHASE OR TRIAL ACTIVATION AUTHORISED.
