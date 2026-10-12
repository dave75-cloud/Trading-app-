# RND-0070 — Historical Consensus Provenance Admission

## Status
GOVERNED ADMISSION STANDARD — OUTCOME-BLIND — NO PROVIDER PURCHASE — NO CONSENSUS ACQUISITION — NO FX OUTCOMES OPENED

## Purpose
Define the minimum evidentiary standard that any historical macro-consensus source must satisfy before a consensus value may enter the canonical RND-0064/RND-0066 macro-event record.

RND-0070 follows the verified RND-0069 BLS timing adapter. Exact timing for the frozen US CPI sample is therefore treated as independently solved. The only unresolved structural input for directional macro-surprise construction is defensible historical pre-release market consensus.

## Governing inheritance
RND-0070 inherits without modification:
- RND-0062 research-admission and multiplicity standard;
- RND-0063 finding that macro-shock research remains inadmissible until defensible point-in-time macro inputs exist;
- RND-0064 canonical event schema and provenance guard;
- RND-0066 split-source architecture and consensus firewall;
- RND-0067 verified FRED/ALFRED official-value backbone acquisition;
- RND-0068 provider feasibility findings;
- RND-0069 verified official BLS exact historical timing adapter.

No market outcome may be used to select, rescue, rank, or reject a consensus provider.

## Required consensus semantics
A candidate historical consensus field is admissible only if all of the following are proven:
1. it represents a market/economist survey consensus, not a vendor model forecast;
2. its value existed before the corresponding scheduled release time;
3. the provider exposes stable event identity or enough deterministic metadata to map into the frozen canonical link key;
4. the provider preserves historical point-in-time state rather than silently returning a present-day reconstructed field;
5. missing consensus remains missing;
6. raw response identity and immutable hash can be retained;
7. provider/source identity is retained at field level;
8. the source covers the required development period sufficiently for the intended hypothesis family;
9. no FX-return, P&L, ranking, or strategy outcome field enters acquisition or admission logic;
10. provider choice is outcome-blind.

## Candidate semantics: Trading Economics
Current Trading Economics documentation explicitly distinguishes:
- `Forecast`: consensus forecast from a representative group of economists;
- `TEForecast`: Trading Economics' own projection.

Only `Forecast` is eligible for the `MARKET_CONSENSUS` semantic. `TEForecast` is never an admissible substitute.

Trading Economics also documents point-in-time economic-calendar retrieval intended for backtesting without look-ahead bias. This makes it the strongest documented candidate presently identified for a bounded historical consensus pilot.

This is not a purchase authorization and not an acquisition authorization.

## Historical-point-in-time rule
A provider statement that an endpoint is "historical" is insufficient by itself. The source must support or document retrieval semantics that preserve what was available at the relevant historical time.

For any acquired record, RND-0070 requires:
- provider event identity;
- event/reference period identity;
- consensus value;
- semantic classification `MARKET_CONSENSUS`;
- historical-point-in-time assertion backed by provider semantics;
- capture/snapshot/update timestamp when available;
- proof that the consensus snapshot is strictly earlier than the BLS exact release timestamp, or a provider point-in-time mechanism that deterministically establishes the pre-release state;
- immutable raw hash;
- source identity.

## Chronology rule
A consensus value is ineligible if:
- captured at the exact release instant;
- captured after release;
- historical chronology is unknown;
- provider semantics do not establish pre-release availability.

The canonical join rule remains strict: consensus must be demonstrably pre-release.

## Semantic anti-substitution rule
The following may not fill a missing market-consensus field:
- proprietary/model forecast;
- previous release value;
- revised previous value;
- analyst estimate obtained after release;
- later reconstructed forecast;
- synthetic estimate from historical values;
- FRED/ALFRED observation or forecast surrogate.

## Coverage rule
The target development interval remains `DEVELOPMENT_2015_2020`.

A bounded pilot may use a smaller frozen sample for provenance verification, but source admission for full development work requires a documented coverage assessment across 2015–2020 for the intended event families.

A source beginning materially after 2015 cannot be silently promoted to full-development authority.

## Candidate-source states
RND-0070 classifies sources as:
- `REJECT_SEMANTIC_MISMATCH`
- `REJECT_NOT_POINT_IN_TIME`
- `REJECT_CHRONOLOGY_UNPROVEN`
- `REJECT_DEVELOPMENT_COVERAGE`
- `PILOT_ELIGIBLE_CONSENSUS_SOURCE`
- `FULL_DEVELOPMENT_CONSENSUS_SOURCE_ELIGIBLE`

`PILOT_ELIGIBLE_CONSENSUS_SOURCE` only authorizes a tiny outcome-blind provenance pilot. It does not authorize strategy testing.

## Frozen initial pilot target
If later authorized, the first consensus pilot should reuse the already-frozen RND-0067/RND-0069 US CPI structural sample:
- CPIAUCSL backbone;
- January, February, March 2019 reference months;
- BLS exact release timestamps already verified;
- no FX prices or outcomes;
- no expansion of event families during the pilot.

## Trading Economics acquisition posture
Trading Economics is presently the preferred pilot candidate because its documented economic-calendar schema distinguishes survey consensus from proprietary forecast and its point-in-time endpoint is explicitly intended to preserve historical state for backtesting.

However:
- no subscription or paid key is authorized by RND-0070;
- no credential may be pasted into chat or committed to source;
- a trial/free access route may be explored only if it does not weaken provenance requirements;
- if paid access is eventually required, human approval must precede purchase.

## Hostile requirements
Implementation must reject at minimum:
1. `TEForecast` or any model forecast presented as consensus;
2. missing consensus imputed from previous or actual values;
3. consensus with no historical-point-in-time proof;
4. consensus captured at release;
5. consensus captured after release;
6. mismatched link key;
7. mismatched economy;
8. mismatched currency;
9. mismatched reference period;
10. insufficient source identity;
11. missing raw hash;
12. development coverage beginning too late for full authority;
13. market-outcome contamination;
14. provider selection based on strategy performance;
15. authority escalation.

## Decision
Adopt a strict consensus-provenance admission layer before any consensus acquisition.

Treat Trading Economics as the current preferred bounded-pilot candidate, not as an architectural dependency and not as a purchased source.

Do not open FX outcomes until:
- FRED/ALFRED official-value provenance passes;
- BLS exact timing passes;
- consensus source passes RND-0070 and a bounded acquisition pilot;
- deterministic composition passes RND-0066/RND-0064;
- RND-0063 admission is formally revisited.

## Authority
No consensus acquisition authority.
No provider-purchase authority.
No market-outcome access.
No validation access.
No reserved-final access.
No prospective-outcome access.
No broker-write authority.
No capital authority.
No live-execution authority.
No automatic merge.
