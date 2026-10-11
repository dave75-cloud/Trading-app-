# RND-0065 — Trading Economics Outcome-Blind Provider Pilot

## Status
FROZEN PROVIDER PILOT DESIGN — NO FX OUTCOME ACCESS / NO STRATEGY TEST

## Purpose
Test whether Trading Economics can serve as an admissible historical macro-event source under RND-0064 without opening, joining, or computing any FX market outcome.

Provider selection for this pilot is based only on current documented access practicality and point-in-time/provenance capabilities. Econoday remains the independent fallback/cross-check candidate.

## Absolute outcome-blind rule
RND-0065 must not read, join, derive, request, or inspect:
- FX prices;
- FX returns;
- strategy signals;
- trade outcomes;
- P&L;
- equity;
- drawdown;
- pair rankings;
- Q003 outcomes;
- RND-0060Q/R economic outcomes;
- 2021–2022 consumed validation;
- 2023–2024 reserved final.

The pilot may inspect macro-event metadata and macro released values because these are candidate explanatory inputs, not FX outcomes.

## Provider
Pilot A provider: Trading Economics API.

Authoritative documented properties used by this protocol:
- point-in-time calendar access is available;
- release `Date` is documented as UTC;
- `CalendarId` provides event identity;
- `Actual`, `Previous`, `Forecast`, `TEForecast`, `LastUpdate`, `Revised`, `Source`, `SourceURL`, `Ticker`, `Symbol`, `Unit`, `Currency`, and `Importance` are available fields;
- `DateSpan=0` means exact release date/time is known; `DateSpan=1` means estimated timing and is not admissible for the pilot;
- point-in-time retrieval is intended to preserve values before later revisions.

## Fixed pilot sample
The pilot sample is frozen before acquisition and before any FX outcome access.

Date range:
- 2019-01-01T00:00:00Z inclusive
- 2019-04-01T00:00:00Z exclusive

Countries / economic areas:
- United States
- Australia
- United Kingdom
- Euro Area
- Japan

Acquisition rule:
- request calendar records for the complete fixed date range and covered countries/economic areas;
- do not filter based on observed macro surprise magnitude;
- do not filter based on later FX reaction;
- do not select records after seeing any market outcome.

The pilot is a data-quality exercise only. It does not define the eventual RND-0063 strategy event universe.

## Structural admissibility rules
A normalized macro-event record is pilot-admissible only if all are true:
1. provider identity is `TRADING_ECONOMICS`;
2. stable provider event identity is present;
3. release timestamp parses as timezone-aware UTC;
4. `DateSpan=0`;
5. country/economic area is inside the frozen pilot set;
6. release timestamp lies inside the frozen pilot window;
7. event/category identity is present;
8. source identity is present;
9. point-in-time acquisition request identity is recorded;
10. raw response hash is recorded;
11. no FX/market-outcome field is present in the normalized object.

Consensus is not required for every provider record because some releases are legitimately not surveyed. However, records without contemporaneous consensus are marked `NO_CONSENSUS` and are not eligible for a future surprise-direction rule unless a later frozen design explicitly allows a different directional input.

Actual-as-released is likewise structurally recorded when present. Missing actual values are marked and cannot be used for a future surprise calculation.

## Revision semantics
The pilot must preserve separately:
- actual released value for the current event;
- provider `Previous` field;
- provider `Revised` field;
- `LastUpdate` timestamp.

No code may overwrite original raw payloads with revised values.

## Raw evidence preservation
For each API response batch, preserve:
- provider;
- request URL with credential redacted;
- UTC acquisition timestamp;
- requested country/date scope;
- HTTP status;
- raw payload SHA-256;
- raw record count;
- parser/normalizer version;
- normalized structural report hash.

API credentials must never be committed to Git or evidence receipts.

## Provider pilot acceptance criteria
Trading Economics Pilot A is `PROVIDER_STRUCTURALLY_ACCEPTED_FOR_RND0063_DESIGN` only if all are true:
1. API access succeeds under an explicitly authorized user subscription/trial;
2. fixed pilot scope can be retrieved reproducibly;
3. no request exceeds provider limits or silently truncates records;
4. exact-timed (`DateSpan=0`) records are identifiable;
5. UTC timestamp semantics are confirmed in returned data;
6. stable event identities are present;
7. raw hashes and request metadata can be preserved;
8. duplicate identities can be detected;
9. point-in-time actual/consensus/revision fields can be preserved without mutation;
10. no FX outcome or protected evidence is accessed;
11. RND-0064 provenance guard accepts the structurally eligible normalized records;
12. repeated acquisition of the same frozen scope yields an explainable reproducibility result (identical raw data or documented provider-side update metadata).

## Pilot rejection / escalation
If any acceptance criterion fails:
- do not relax the provenance standard;
- do not inspect FX outcomes;
- classify `PROVIDER_PILOT_NOT_ACCEPTED` or `PROVIDER_PILOT_INCONCLUSIVE`;
- evaluate Econoday as Pilot B under the same structural principles.

## Commercial/access boundary
Trading Economics currently requires API authentication and offers self-service paid/trial access. RND-0065 does not authorize purchase, subscription, renewal, or charging a payment method.

A human must explicitly obtain/authorize API access before live acquisition.

## Authority firewall
Throughout RND-0065:
- strategy_outcome_open=FALSE
- validation_open=FALSE
- reserved_final_open=FALSE
- prospective_outcomes_open=FALSE
- promotion_authority=FALSE
- broker_write_authority=FALSE
- capital_authority=FALSE
- live_execution_authority=FALSE
- automatic_merge=FALSE

## Interpretation boundary
Passing RND-0065 would establish only that Trading Economics is structurally suitable as a macro-event input source for returning to the RND-0063 admission review. It would not establish a directional edge, profitable strategy, candidate, or trading authority.
