# RND-0074 — Session-boundary M5 coverage pilot: predeclared protocol

**Status:** DEVELOPMENT-ONLY METADATA AUDIT DESIGN. No strategy/outcome authority. The source evidence remains quarantined.

## Purpose and existing conventions
Reuse the *frozen 2019 illustrative* clock conventions in `rnd/orchestration/rnd0074_session_clock_rehearsal.py`, which define Tokyo local 09:00/17:00, London 08:00/16:00, and New York 08:00/16:00. These are **research time conventions**, not confirmed individual FX venue openings, dealer handoffs or inventory transfers. They correctly map local weekdays to UTC with IANA DST.

The pilot uses **2019 only** because the existing clock module intentionally rejects dates outside 2019. Extending to 2016–2018 would require separately reviewed and tested generalization rather than bypassing the frozen fixture. Pairs: AUDUSD, EURUSD, GBPUSD and USDJPY; archive only `rnd0033-development-history-2016-2019`.

## Immutable coverage definitions
- For each *local weekday* session boundary, consider half-open UTC window `[boundary - 30 minutes, boundary + 30 minutes)`, exactly twelve potential 5-minute start timestamps.
- Compute eligible denominator as the intersection of that window and the **original reference** `standard_schedule.json` in the same UTC-year shard. The baseline is retained as-is; no calendar promotion. A local-day boundary may fall outside the UTC-year archive; those slots are out of scope and must not be inferred missing.
- Count `expected_baseline_m5`, `missing_baseline_m5` from `discrepancy_ledger.json`, `present_baseline_m5 = expected - missing`, and `coverage_pct = 100 * present / expected` for each pair × session × boundary class. Count zero-eligible local-weekday windows explicitly.
- Count *unexpected* provider timestamps in these windows **separately**; they must not silently enter denominator/numerator. Notably the pre-existing baseline excludes NY 17:00 rollover; such provider candles are reported separately if they fall within any study window.
- All intervals are timestamp-label availability only, not quote continuity, spread availability, representative trading hours, liquidity, or plausible executable tradeability. Window comparisons may overlap between sessions; **do not sum coverage across sessions as independent M5 observations**.
- Holidays are not inferred or excluded in this pilot; calendar holiday uncertainty remains. This can bias coverage and requires separate documentary review.

## Admission gates and technical constraints
Audit calls the bounded RND-0074 `summarize(..., verify_hashes=True)` before any coverage calculation, checking five listed file digests and manifest/ledger invariants. The auditor reads `canonical_rows.json` solely as opaque bytes for hash computation; it does **not** parse price observations, signals or strategy outcomes. It does not rewrite source evidence or generate a report file. Original RND-0030 raw-page semantic verifier is **not** re-executed; neither this audit nor its test suite authorizes sealing.

Output: six aggregate session/boundary records per pair (three convention sessions × opening/closing window). No individual quote, raw market return, cross-year protected validation, reserved final, prospective observation, OANDA call, credential, broker write or subscription use.

## Review after first pilot
1. Human reports local synthetic tests on the exact GitHub commit.
2. Run one read-only `EURUSD/2019` coverage pilot. Confirm 6 records, sensible denominators, counts and explicit admitted=false status.
3. Expand to other three 2019 pairs only after operator output review; compare availability, report how missingness varies by nominal handoff. Do not select strategies based on these figures.
4. Decide whether the present baseline's holiday and 17:00 exclusions make a proposed descriptive study inadmissibly biased. Any future 2016–2018 coverage audit requires an explicit versioned clock-year expansion and its own validation.
5. Separate independent human decision is mandatory for economic/spread analysis, strategy simulation, evidence promotion, or calendar changes.

Current disposition: `COVERAGE_PROBE_ONLY; SOURCE_QUARANTINED; EVIDENCE_NOT_ADMITTED`. Incremental provider expense USD 0; Trading Economics trial not activated.
