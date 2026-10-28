# RND-0074 — Affected-date and cross-pair offset implementation gate

**Status: CODE COMMITTED; OPERATOR SYNTHETIC TEST RUN PENDING; NO REAL ARCHIVE OUTPUT CLAIMED.**

New extension: `rnd/tools/rnd0074_cross_pair_offset_dates.py`. Synthetic test module: `rnd/tools/test_rnd0074_cross_pair_offset_dates.py`. This supplements, and does not modify, the previously locally verified `rnd0074_session_offset_coverage.py`.

## Definition

- **Authorized input:** exact RND-0033 development evidence root; year 2019 only; all four fixed pairs; six illustrative session boundary conventions from the frozen 2019 clock module; all twelve predeclared five-minute offsets.
- **Integrity gate:** each of four original 2019 shards goes through the existing limited SHA-256/manifest/ledger audit BEFORE any cross-pair comparison. It does not independently rerun the full original RND-0030 provenance verifier.
- **Affected local dates:** count distinct local weekdays on which a given pair/offset/window has a missing baseline-eligible M5 timestamp.
- **Cross-pair membership:** for each session, boundary, offset and local weekday, count how many of the four instruments have that exact UTC timestamp in the original full missing ledger *and* in that instrument's original baseline schedule. Report the number of distinct timestamp occurrences missing in exactly one, two, three or four pairs.
- **Cross-check:** for every pair, offset and selected view, missing count from new cross-pair routine MUST match the corresponding count from the existing single-pair offset auditor; any mismatch is an error.
- **Views:** original untouched calendar on all local weekdays; separate descriptive sensitivity excluding only local 1 January and 25 December, without declaring historical closures.
- **Output:** structured JSON to standard output, not written to the source archive. No parsing of canonical prices, returns, trades or economic outcomes.

## Current known targets (not assumed outcomes of this new code)

For AUDUSD 2019 at NY CLOSE offsets +15 and +20, with the two-date sensitivity, prior operator analysis found **75 missing pair-offset timestamps on 68 distinct affected dates**. Across those 75, **70** missing from AUDUSD alone, **5** also missing in exactly one other pair, and none missing in two or three other pairs. These figures are reconciliation targets, not hardcoded acceptance values.

## Strict limitations and next gate

- Original source status remains `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=False`; clock conventions illustrative rather than authenticated trading hours.
- This implementation contains supporting negative tests, but no passing test outcome may be asserted until operator executes the actual test suite on the exact commit.
- Operator test first; review any failures, then one bounded AUDUSD-targeted development-only comparison. Full all-pair JSON is potentially verbose; a summarizer may display only relevant window/offset values.
- Cross-pair comparison is **not a provider-authenticity or liquidity measurement**. No price access, strategy evaluation, protected data, OANDA broker writes, promotions, merge approval or paid data trial follows.

**Disposition: CONTINUE_METADATA_ONLY / NO-GO HISTORICAL EVIDENCE ADMISSION.**
