# RND-0074 — Historical development evidence admission review

**PROPOSAL ONLY. NOT AN APPROVAL OR PROMOTION.** Prepared 2026-10-22.

## Scope and separation
Covers existing OANDA PRACTICE M5 bid/ask/mid historical development shards, primarily 2015–2020. Does not open 2021–2022 protected validation, reserved 2023–2024 final, prospective evidence, or trading outcomes. Separate calendar interpretation from file integrity, completeness, strategy design and economic results. Respect predeclared RND-0062 multiple-testing/validation admission controls.

## Gate A — repository and source provenance
- Verify source pair/year identity, acquisition declaration, environment, timeframe, price components, complete flag, start/end boundaries, number of raw pages, provenance hashes, raw bundle/canonical bundle/ledger/schedule file digests. Independently recompute SHA-256 of *development-only* acquisition records before any use.
- Confirm existing source manifest `QUARANTINED_UNRESOLVED_DISCREPANCIES`; record sealed/blocked status unchanged. Fail closed on missing/inconsistent digests, unreconciled identity, unknown source or altered bytes.
- No file writes to evidence folder; any derived candidate outputs versioned separately outside canonical paths and labeled `NON_AUTHORITATIVE`.

## Gate B — documented trading calendar
- RND-0030 baseline: current OANDA NY ordinary hours excluding 17:00 M5 start; valid as the baseline reference but *not automatically period-specific*.
- RND-0031 candidate: add 17:00 NY Sunday–Thursday; explanatory hypothesis only, authority `NONE`.
- Explicitly examine provider M5 start-time labeling, `complete` flag, DST, Sunday reopening, Friday close and the two shared post-Friday October 2017 times. Historical documentary evidence must independently cover the dates/rules claimed.
- Keep both baseline and candidate schedules/ledgers side-by-side; never discard an unexpected row merely because the candidate explains it.
- If period-specific authority is missing, **calendar authority = UNRESOLVED**. A human may separately approve bounded descriptive timestamp-structure analysis that clearly retains this caveat; cannot approve performance-grade historical sealing by default.

## Gate C — missing timestamp taxonomy
For each development-only pair-year, derive runs from *existing discrepancy timestamp strings* using the RND-0031 `contiguous_runs` and `classify_missing_runs` pattern:
1. short residual <=3 M5 bars;
2. intermediate unclassified 4–11 bars;
3. closure-shaped >=12 bars (candidate only, not a documentary closure).
Record number of runs, number of bars, earliest/latest time ranges, clock-hour/day-of-week bands, and cross-pair overlap. Do not expose prices/returns. Protect against changes to source ledger and reject unsorted/duplicate/non-M5 timestamps.
Any retained gap must be represented as unavailable in downstream features and execution logic; no filled or synthetic bars, no implicit continuity, no forward/backward time leakage. Long closure-shaped patterns require date-specific source confirmation to be called verified closures. Remaining gaps are explicitly unresolved, not silently deleted.

## Gate D — intended-use decision
Proposed *distinct* dispositions:
- **Structural-only descriptive analysis**: may be approved by human on a narrowly defined development-only slice once A integrity passes and uncertainty is documented. No profitability, strategy selection, signal or trade simulation.
- **Gap-aware empirical hypothesis study**: requires separately predeclared objectives, timing, sample partitions, controls, costs and exclusion/gap rules; specific human admission review and RND-0062 compliance. No implicit approval from this document.
- **Performance-grade historical sealing**: not allowed on current evidence. Requires complete independent calendar/exception support as necessary for chosen use, verified hashes, no unexplained integrity failures, explicit gap semantics, audit reproducibility and human approval.
- **Quarantine continued / reject**: default whenever prerequisites fail or cannot be established.

## Proposed review fields
- `dataset_scope`, `source_file_sha256_checks`, `original_status`, `original_seal_allowed`, `baseline_calendar_rule`, `candidate_calendar_rule`, `historical_documentary_authority`, `gap_summary`, `unresolved_exceptions`, `proposed_intended_use`, `independent_reviewer`, `human_approval`, `decision_timestamp`, `derived_artifact_sha256`.
- Require `human_approval = null` and `decision = PENDING` until an explicit later user instruction. No self-issued promotion authority.

## Unresolved specific questions
- What exact historical OANDA break rule was operative in 2015–2020, by entity/feed, and do the current trading-hours pages apply retrospectively? Not established.
- Why exactly two Friday 2017 late entries occurred across all pairs? Not established.
- Which missing intervals represent scheduled holidays, low-activity non-creation of candles, provider gaps or integrity failures? Not established.
- Does historical development data offer reliable spread observations at intended session handoffs? Not evaluated.
- Can any directional edge withstand OOS tests, transaction costs and multiple testing? Not evaluated.

## Decision for this RND-0074 documentation phase
**DOCUMENTARY SYNTHESIS COMPLETE; ADMISSION PENDING.** Original quarantine/seal blocked; strategy authority = FALSE; broker writes = FALSE; capital authority = FALSE; protected windows unopened; no incremental subscriptions or cost authorized.

See `rnd/research/RND0074_HISTORICAL_OANDA_CALENDAR_EVIDENCE_SYNTHESIS.md` and original RND-0030/31/36 records.
