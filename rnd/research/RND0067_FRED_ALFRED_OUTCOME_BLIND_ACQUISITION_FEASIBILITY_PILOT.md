# RND-0067 — FRED/ALFRED Outcome-Blind Acquisition Feasibility Pilot

## Status
GOVERNED STRUCTURAL PILOT — NO FX OUTCOMES — NO CONSENSUS JOIN — NO EXACT-TIME CLAIM

## Purpose
Test whether the frozen RND-0066 FRED/ALFRED backbone can be acquired reproducibly and transformed into governed structural evidence for a tiny predeclared US macro sample, without opening any FX outcome or weakening the RND-0064/RND-0066 provenance firewall.

RND-0067 is not a strategy backtest. It does not calculate surprise, returns, P&L, direction, hit rate, drawdown, pair ranking, or promotion evidence.

## Inheritance
RND-0067 inherits without modification:
- RND-0062 research-admission and multiple-hypothesis discipline;
- RND-0063 requirement for a defensible point-in-time macro dataset before directional research;
- RND-0064 canonical event/provenance rules;
- RND-0065A cost discipline and provider replaceability;
- RND-0065B FRED/ALFRED backbone architecture;
- RND-0066 field-level provenance firewall and independent timing/consensus requirements.

## Frozen pilot scope
The pilot is deliberately narrow and is selected for acquisition/provenance mechanics only.

Frozen series:
- FRED series ID: `CPIAUCSL`
- link key: `US_CPI_HEADLINE`
- economy: United States
- currency: USD
- observation window: `2019-01-01` through `2019-03-01`
- vintage/realtime audit window: `2019-01-01` through `2019-12-31`
- pilot scope ID: `RND0067_US_CPI_2019Q1_STRUCTURE_ONLY`

No alternative series may be substituted after inspecting any market response.

## API endpoints
The pilot uses only official St. Louis Fed web-service endpoints:
1. `fred/series` for series identity/title/frequency/units metadata;
2. `fred/series/observations` with `output_type=4` for initial-release-only observations;
3. `fred/series/vintagedates` for dates when values were revised or new values were released.

All requests use `file_type=json`.

The official API documentation requires an API key for web-service requests. The key is accepted only through an argument or the `FRED_API_KEY` environment variable and must never be committed, printed in receipts, or pasted into chat.

## Security and request identity
The raw request URL contains the API key because that is how the FRED API authenticates requests. Therefore:
- the key must be redacted before persistence;
- request identity is the SHA-256 of the redacted deterministic request URL;
- changing only the API key must not change request identity;
- raw payload hashes are independent of the credential;
- receipts may contain only the redacted URL.

## Immutable evidence receipts
Each endpoint response receives a receipt containing:
- endpoint role;
- FRED series ID;
- frozen pilot scope ID;
- redacted request URL;
- deterministic request identity;
- acquisition timestamp in UTC;
- SHA-256 of canonical JSON serialization of the raw response;
- raw record count;
- parser version.

The pilot bundle is structurally complete only when all three endpoint receipts exist and have distinct endpoint request identities.

## Initial-release rule
The observation request is frozen to `output_type=4`, which the St. Louis Fed documentation defines as initial-release-only observations.

For each returned observation, the pilot records:
- FRED series ID;
- observation date;
- returned `realtime_start` as the date-level initial vintage evidence;
- initial-release value;
- unit from separately validated FRED series metadata;
- reference period derived deterministically from the monthly observation date;
- US/USD mapping;
- raw response hash;
- source identity `FRED:<series_id>:output_type=4`;
- `initial_release=True`.

A missing initial-release value is rejected rather than imputed.

## Vintage-lineage rule
`fred/series/vintagedates` is used to prove that historical dates exist on which the series received new or revised observations.

The pilot requires the returned vintage dates to be:
- present;
- valid `YYYY-MM-DD` dates;
- ascending;
- duplicate-free.

RND-0067 does not infer which later value superseded which earlier value solely from a date list. Full value-level revision lineage, if required, belongs in a later separately frozen extension using vintage-specific observation retrieval.

## Critical timing limitation
RND-0067 does not make any intraday timing claim.

FRED/ALFRED release dates and vintage dates remain date-level provenance. The St. Louis Fed release-date documentation states that release dates are published by the underlying data sources and do not necessarily represent when data became available on FRED or ALFRED.

Therefore:
- `fred_exact_intraday_timing_authority = FALSE`;
- no date returned by this pilot may become `timestamp_precision=EXACT`;
- no M5 event alignment may be performed from FRED/ALFRED dates alone.

## Critical consensus limitation
RND-0067 acquires no market consensus.

Therefore:
- `fred_market_consensus_authority = FALSE`;
- no surprise value is computed;
- no prior value, model forecast, FRED forecast, or later vendor field may be substituted for contemporaneous pre-release consensus;
- no event becomes `SURPRISE_INPUT_ELIGIBLE` in RND-0067.

## Outcome firewall
Raw or normalized pilot structures reject prohibited fields including:
- FX return;
- P&L;
- equity;
- drawdown;
- hit/win rate;
- pair rank;
- directional response;
- strategy signal/outcome.

No join to OANDA or any other FX price history occurs in this phase.

## Classification
Allowed pilot classifications are structural only:
- `PILOT_STRUCTURAL_FEASIBILITY_CONFIRMED`
- `PILOT_INCONCLUSIVE_NO_INITIAL_RELEASE_ROWS`
- `PILOT_INCONCLUSIVE_NO_VINTAGE_LINEAGE`
- `PILOT_FAIL_SERIES_IDENTITY`
- `PILOT_FAIL_INITIAL_RELEASE_SEMANTICS`

`PILOT_STRUCTURAL_FEASIBILITY_CONFIRMED` means only that FRED/ALFRED acquisition mechanics can supply the frozen official-value/vintage backbone structure. It is not strategy admission and not source sufficiency for macro-surprise research.

## Hostile tests
The implementation must prove at minimum:
1. explicit valid API key required;
2. frozen series/window cannot silently drift;
3. `output_type=4` is fixed for initial-release retrieval;
4. API key never survives in receipts;
5. request identity is credential-independent;
6. endpoint request identities are distinct;
7. metadata series mismatch is rejected;
8. missing metadata is rejected;
9. market-outcome contamination is rejected recursively;
10. initial records are explicitly marked initial release;
11. observation/vintage/reference-period identity is deterministic;
12. missing initial value is rejected;
13. out-of-scope observation is rejected;
14. vintage dates must be ascending and duplicate-free;
15. raw hashes are deterministic;
16. incomplete receipt bundles are rejected;
17. all strategy/execution/promotion authorities remain false.

## Live acquisition gate
A live request is permissible only when the user has independently configured a valid FRED API key as `FRED_API_KEY` in the local environment or passes it locally to the pilot tool.

The API key must not be pasted into ChatGPT, committed to Git, embedded in shell history unnecessarily, or included in test fixtures beyond dummy non-secret keys.

Running the live acquisition is optional for implementation verification. The hostile unit tests use synthetic FRED-shaped fixtures and make no external network call.

## Exit criteria
RND-0067 implementation is ready for human verification when:
- the frozen pilot code exists on its own governed branch;
- hostile tests pass locally;
- no protected outcome partition is opened;
- no API key is exposed;
- no provider purchase is made;
- no consensus or exact-time claim is made.

After implementation verification, the next decision is whether to perform one real outcome-blind FRED API acquisition locally. A successful live structural bundle can then justify a separate value-level revision-lineage pilot or a low-cost timing/consensus-source pilot. Neither step may inspect FX outcomes.

## Authority
No market-outcome access.
No validation access.
No reserved-final access.
No prospective-outcome access.
No exact-time authority.
No consensus authority.
No provider-purchase authority.
No promotion authority.
No broker-write authority.
No capital authority.
No live-execution authority.
No automatic merge.
