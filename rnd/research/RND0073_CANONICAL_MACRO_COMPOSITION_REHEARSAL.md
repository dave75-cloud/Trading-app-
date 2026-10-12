# RND-0073 — Canonical Macro Composition Rehearsal

## Purpose

Prove the full structural macro-event composition path without paying for a consensus provider and without opening FX outcomes.

The rehearsal composes:

1. FRED/ALFRED initial-release actual / revision provenance;
2. official BLS exact historical release timing;
3. synthetic point-in-time market-consensus fixtures shaped exactly like the admitted RND-0066 consensus interface;
4. the canonical RND-0064 normalized event record.

## Frozen scope

- Economy: United States
- Event family: headline CPI
- Link key: `US_CPI_HEADLINE`
- Reference periods: `2019-01`, `2019-02`, `2019-03`
- Development partition only
- Exactly three records
- Consensus provider in this phase: `SYNTHETIC_CONSENSUS_FIXTURE` only
- No live Trading Economics access
- No provider purchase
- No FX prices, returns, P&L, equity, drawdown, hit rate, win rate, ranking, signal or strategy outcome data

## Success criterion

All three frozen records must compose through the existing RND-0066 join into valid RND-0064 normalized events with:

- exact BLS timing;
- initial-release FRED/ALFRED actual provenance;
- strictly pre-release point-in-time consensus semantics;
- deterministic cross-source identity alignment;
- deterministic canonical event IDs and bundle hash;
- `SURPRISE_INPUT_ELIGIBLE` structural state;
- every spending, trading, promotion and live authority remaining false.

This classification is structural only. It does **not** authorize surprise calculation against market outcomes, strategy evaluation, provider purchase, promotion, or execution.

## Falsification / rejection conditions

The rehearsal must reject, at minimum:

- missing or extra frozen records;
- reference-period misalignment or reordering;
- non-synthetic consensus in this offline phase;
- consensus captured at or after the release timestamp;
- cross-source link-key, economy, currency or reference-period mismatch;
- non-initial FRED actuals;
- duplicate canonical identities;
- contaminated market-outcome fields;
- non-exact / inconsistent timing inherited from the BLS adapter.

## Cost posture

Incremental spend for RND-0073: **US$0**.

The Trading Economics trial remains unapproved and unincurred. The purpose of this rehearsal is to maximize what can be proven before any paid access is activated.

## Next gate

If the hostile test suite passes locally, the project will have proven the complete canonical join using synthetic consensus. The remaining unresolved empirical question will then be provider-side: whether a bounded live Trading Economics point-in-time snapshot supplies historical `Forecast` values with the provenance semantics expected by the frozen adapter.
