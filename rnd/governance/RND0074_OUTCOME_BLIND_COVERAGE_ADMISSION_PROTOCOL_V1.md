# RND-0074 — Version 1.0: Outcome-Blind Historical Data Coverage and Evidence-Admission Framework

**Document class:** Proposed research governance protocol (design only)  
**Status:** `DESIGN_RECORDED / COVERAGE_METADATA_ONLY / HISTORICAL_DATA_NOT_ADMITTED`  
**Project:** `dave75-cloud/Trading-app-`, research branch `agent/rnd-0074-session-handoff-mechanism-admission`  
**Scope:** RND-0033 OANDA PRACTICE M5 development-only archive, AUDUSD/EURUSD/GBPUSD/USDJPY, UTC years 2016–2019. Existing frozen session-clock *pilot* implementation remains 2019-only.  
**Authority:** This document grants **no new authority**. Do not merge, promote, re-seal, open prices or expand research windows without independently documented human approval at the relevant gate.

## 1. Research question and limits

**Question:** Does the original timestamp reference schedule provide adequately characterised, reproducible M5 *availability* around predeclared Tokyo, London and New York nominal session boundaries to support a separately approved future descriptive liquidity study?

**Not addressed here:** historical closures authoritatively established; candle source validity proven; spread accuracy; causal market liquidity; economic announcement effects; trading signals, strategy performance, live execution or capital. Missing M5 timestamp means missing within **this reference ledger**, not zero liquidity, no trade, OANDA outage or missing executed quotation.

The present source archive is `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False` for all sixteen pair-year shards. No action in this protocol changes this or the M005/M006e frozen stack. Trading Economics trial remains deferred. OANDA PRACTICE READ-ONLY, master execution switch NO, order writes and live authority forbidden.

## 2. Locked inputs and provenance

1. The development evidence root must have the exact basename `rnd0033-development-history-2016-2019`, containing one exact `PAIR/YEAR` shard for each authorized pair/year. No symbolic-link traversal; reject ambiguous paths and unexpected partitions.
2. Within each shard, original `quarantine_manifest.json`, `standard_schedule.json`, and `discrepancy_ledger.json` supply identity, immutable reference calendar and sorted timestamp lists. These must remain unchanged; never regenerate, reseal, or update a reference schedule merely to improve measured coverage.
3. Require bounded `rnd/tools/rnd0074_development_metadata_audit.py` file SHA-256 and manifest/ledger reconciliation **as a precondition**, including hash-only access to price-related files, with no parsing of canonical prices. Record exact tool commit, file hashes, execution timestamp/host environment, pair/year, and PASS/FAIL.
4. The existing RND-0074 SHA check is **not the independent, complete RND-0030 source/raw-page/canonical semantic verifier**. Before any proposal for economic/quote access, the original full verifier must be separately run, reviewed and recorded with immutable inputs. Disagreement, mismatch or tool error = FAIL CLOSED.
5. Protected 2021–2022 validation, reserved 2023–2024 final, sealed prospective outputs and performance/strategy outcomes are strictly outside scope. 2020/2015 development extensions are not covered by the current 16-shard receipt.

## 3. Frozen pilot session-time conventions

Use `rnd/orchestration/rnd0074_session_clock_rehearsal.py` on its frozen **2019** year:

| Session | IANA timezone | Nominal local OPEN | Nominal local CLOSE |
|---|---|---|---|
| TOKYO | Asia/Tokyo | 09:00 | 17:00 |
| LONDON | Europe/London | 08:00 | 16:00 |
| NEW_YORK | America/New_York | 08:00 | 16:00 |

These are **illustrative research wall-clock anchors**, not documentary evidence of OANDA hours, trading venue openings or dealer handoffs. Select local weekdays (Mon–Fri), convert via IANA time-zone rules, and reject ambiguous/nonexistent wall times rather than silently normalising. Do not override times, choose offsets post hoc, or extend beyond 2019 by evading the clock module. Extension to 2016–2018 requires a new versioned/reviewed clock capability with synthetic edge-case testing.

For each of the six SESSION×BOUNDARY categories and each local weekday, observe **12 possible M5 candle-start labels** in half-open `[anchor-30 min, anchor+30 min)`, offsets `{-30,-25,-20,-15,-10,-5,0,+5,+10,+15,+20,+25}`. No inferred holiday removal from baseline in the primary result.

## 4. Coverage definitions and complete denominator accounting

For pair `p`, year `y`, session `s`, boundary `b`, offset `o`, and local study date `d`:

- `t(d,s,b,o)`: timezone-normalised UTC five-minute candle **start** timestamp; date/UTC-year clipped to original shard boundary.
- `E`: indicator `t` is in the **original** `standard_schedule.json`; never treat an out-of-year/unscheduled timestamp as automatically missing. Report unscheduled and out-of-shard counts separately where relevant.
- `M`: indicator `t` is in original `missing_timestamps`, only valid for `E=1`.
- `P = E - M`: baseline-present timestamp indicator. This is ledger-level availability only, not evidence of valid quote or tradability.
- `U`: timestamp in original `unexpected_timestamps`; report separately, **never** silently add `U` to `E` or `P`.

For every pair × session × boundary × offset, report `weekday_window_count`, `eligible_E`, `present_P`, `missing_M`, `unscheduled`, `out_of_year`, `unexpected_U`, `coverage_P/E`, `missing_rate_M/E` and number of `affected_local_dates`. Include per-month and weekday strata (with their respective denominators), as well as local DST zone/transition notes. If `E=0`, coverage is **NA**, not zero or 100%.

**Invariants:** `eligible_E = present_P + missing_M`; `missing_M <= eligible_E`; `eligible_E + unscheduled + out_of_year = count of generated boundary slots` (with mutually exclusive categories); `U` must not be counted twice as scheduled. Report per-cell reconciliation, whole-year summary reconciliation, and any overlapping timestamps across different session windows. Percentages should retain numerators/denominators and deterministic rounding.

The earlier 2019 pilot reports six coarse windows per pair. A finer offset/month/day-of-week audit must be independently implemented/tested before it is relied on as the formal denominator report. Prior operator-run exploratory scripts are **supporting receipts**, not yet an approved canonical implementation.

## 5. Required baseline, sensitivities and contamination flags

**Primary run:** the intact original reference calendar for all eligible 2019 local weekdays, including Christmas/New Year candidates. The excluded 17:00 NY daily rollover in that calendar must be labelled **contested**, not fixed, with all unexpected candles separately counted. Do not alter year-boundary treatment to match desired missingness.

**Predeclared sensitivity views** (always report primary unchanged result alongside each view):
- Remove only 1 January and 25 December local dates as a *holiday sensitivity*, **not** as a finding that their exact historical closure times were verified.
- Stratify every pair/session/offset by calendar month and local weekday, with denominators and affected-date counts; show results across DST transitions with IANA time-zone mapping.
- Separate long-run `>=12`, intermediate `4–11`, short `<=3` original missing-run classifications; note that a timestamp may be long-run in one pair but residual in another. Never assume a shared missing timestamp implies source closure.
- Show four-way and pairwise missing-timestamp overlap **using full original missing ledgers**, plus classifications per pair; do not equate failure of a four-way residual-set intersection with full instrument uniqueness.
- Identify provisional New Year/Christmas-associated candidate runs and unexplained 2019 Sunday reopening gaps as unresolved documentary questions. Across December/January UTC-year shards, diagnostic concatenation must not mutate original inputs, and 2019-only frozen pilot cannot silently analyze another year.

**Bias controls:** all pair/session/offset cells remain visible, including worst coverage. No filling with zeros, forward-filling, using a different pair as a substitute, retrospective deleting weak offsets or adopting a new expected calendar based on observed missingness. No selection of trading windows because they appear clean or profitable.

## 6. Observed evidence motivating this protocol (not thresholds)

- 16/16 pair-year metadata/hash audits reported PASS, all admitted=false; exactly **2,349 distinct closure-shaped missing timestamps** shared across four pairs in 13 long runs over 2016–2019. Documentation verifying each exact historical closure remains absent.
- 2019 session-boundary coarse audit: four pairs × six nominal boundaries passed `METADATA_ONLY_PASS`. AUDUSD NY nominal CLOSE coverage **2919/3132 = 93.1992%**, versus EURUSD **3070/3132**, GBPUSD **3069/3132**, USDJPY **3088/3132**.
- AUDUSD +15/+20 New York close sensitivity excluding local Jan 1/Dec 25: **75 missing / 518 eligible**, across **68 dates and all twelve months**; of these, 70 have no counterpart in any other pair's missing ledger; five coincide with one other pair. Other pair missing counts at these two offsets: EURUSD 12, GBPUSD 15, USDJPY 5 out of 518.
- Above figures are **descriptive, operator-reported and limited to a quarantined reference calendar**. They do not establish a statistical acceptance threshold, economic materiality, market causality or validated historical data.

## 7. Gate states and explicit stop conditions

| Gate | Preconditions | Permitted outcome | Current disposition |
|---|---|---|---|
| A — Identity / hash / timestamp invariants | Exact 2016–2019 archive scope, trusted tool commit, complete limited SHA and ledger checks | Read-only metadata diagnostics | **PASS reported 16/16**, still quarantined |
| B — Calendar-clock transparency | Locked 2019 clock, full original E/P/M/U denominators, holiday/DST flags, offset and pair comparisons | Description of coverage and uncertainty | **PARTIAL**; coarse pilot + exploratory diagnostics, full formal offset ledger pending |
| C — Original-source provenance | Independently rerun full RND-0030 raw-page/canonical semantic verifier and review discrepancies | Evidence-provenance assessment only | **NOT COMPLETED** |
| D — Historical calendar resolution | Independent period-specific OANDA market hours/holiday notices, document timestamp mapping and discrepancies; no silent calendar editing | Proposal for specifically documented calendar interpretation | **UNRESOLVED** |
| E — Human scoped research admission | Written operator approval of an immutable, bounded study scope, code and risks after A–D; source status explicitly addressed | **Only the exactly approved scope**; separate process, never implicit quote access | **NO-GO / AWAITING HUMAN GATE** |
| F — Strategy/broker authority | Distinct governance and human approvals, frozen component constraints, independent OOS evidence | No authority from RND-0074 | **NO-GO** |

Any failed invariant, modified source hash, unreadable or ambiguous timezone, schema inconsistency, attempted protected-year access, unauthorized calendar promotion, proposal to inspect economic outcomes without approval, or attempt to use broker order endpoints => **FAIL CLOSED** and stop. A `METADATA_ONLY_PASS` is not a human admission decision.

Possible post-review decisions: `CONTINUE_METADATA_ONLY`, `RESTRICTED_DESCRIPTIVE_SCOPE_PROPOSED`, or `REJECT_AND_REENGINEER`. `RESTRICTED_DESCRIPTIVE_SCOPE_PROPOSED` is **not** automatic admission. A separate signed/recorded human GO is required.

## 8. Reproducibility and receipt schema

Each future canonical run must record: protocol version + Git commit + script SHA-256; exact authorized root/pair/year; original manifest and ledger digests; trusted timezone database/host Python version; predeclared sessions and offsets; denominator counts by pair/session/boundary/offset/month/weekday; overlap warning; missing-run type; holiday/dst/UTC-boundary sensitivity; failures and unresolved discrepancies; explicit `source_quarantine_unchanged=true`, `prices_parsed=false`, `strategy_evaluated=false`, `broker_writes=false`, `provider_spend_usd=0`, `admitted=false`. Publishing a *research receipt* must not replace or modify the original evidence.

## 9. Next engineering task (no data access granted here)

Create a bounded **2019-only, hash-verified, read-only session-offset coverage report generator** with synthetic negative tests for wrong year/root, symlinks, modified manifest/hash, duplicate/unsorted/non-M5 ledger timestamps, DST mapping errors, denominator/offset accounting, and unexpected timestamp segregation. Do not parse price data. Run tests locally on the exact commit; then, after review, produce four development pair-only metadata receipts. Document unresolved original holiday/calendar discrepancies and separately schedule the complete original-verifier review. Keep all gates intact.

**Current operator decision request: none.** No terminal action is needed to accept this design as a draft. Request a human GO/NO-GO only if moving to an independently defined scope requiring new authority.
