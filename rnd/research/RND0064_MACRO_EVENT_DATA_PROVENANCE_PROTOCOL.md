# RND-0064 — Historical Macro-Event Data Source & Provenance Protocol

## Status
FROZEN DATA-SOURCE GOVERNANCE DESIGN — NO MACRO STRATEGY OUTCOME OPENED

## Purpose
Establish a provider-agnostic protocol for admitting historical scheduled macroeconomic event data into the research system for later RND-0063 macro-shock testing.

This task governs source selection, point-in-time integrity, coverage, timestamps, consensus/actual semantics, revisions, duplicates, missing data, event identity, and immutable provenance. It does not calculate surprise-P&L, does not select an event family based on outcomes, and does not access protected validation/final/prospective outcomes.

## Governing constraints
- FX market development partition remains DEVELOPMENT_2015_2020.
- 2021–2022 consumed validation remains closed.
- 2023–2024 reserved final remains sealed.
- Q003 prospective outcomes remain sealed.
- RND-0060Q/R prospective economic outcomes remain sealed.
- Provider selection must be outcome-blind.

## Candidate source class
A candidate source must provide historical scheduled economic events with enough point-in-time detail to reconstruct what was knowable immediately before and at release.

Initial admissible acquisition candidates based on documentation review:
1. Trading Economics economic calendar point-in-time/history API.
2. Econoday historical economic event data/API.
3. LSEG/Reuters economic-indicator and poll data may be considered as an institutional alternative if access and field history are demonstrated.

No provider is scientifically preferred in advance. Provider choice is based only on structural data quality, coverage, reproducibility, licensing/access feasibility, and provenance.

## Minimum required raw fields
Every admitted raw event record must expose or allow deterministic derivation of:
- provider identity;
- provider event ID / stable event identity;
- event series/category identity;
- country/economy;
- affected currency mapping;
- scheduled release timestamp;
- actual release timestamp if distinct;
- timestamp timezone or UTC-normalized timestamp;
- timing-precision indicator if provider supplies one;
- actual-as-released value;
- contemporaneous pre-release consensus/expectation value;
- previous value;
- unrevised previous value or revision field where available;
- unit;
- reference period;
- provider source/official source identity where available;
- provider last-update/modify timestamp where available.

## Point-in-time integrity
The research dataset must preserve historical values as they appeared at the relevant point in time.

The following are prohibited:
- silently replacing historical consensus with a modern forecast;
- replacing actual-as-released with a subsequently revised value;
- using a provider-generated forecast in place of market consensus unless explicitly frozen as a different hypothesis family;
- using revised release timestamps without preserving the original scheduled/released timestamp lineage;
- retrospective normalization that depends on future events unless the transformation uses only the admitted development sample and is frozen before outcome testing.

A provider is not admissible merely because it has historical actuals. Historical consensus/expectation integrity is mandatory for directional surprise research.

## Release timestamp semantics
All timestamps must be normalized to UTC without losing the original provider representation.

For each event, retain:
- provider-original timestamp text;
- parsed timezone-aware timestamp;
- normalized UTC timestamp;
- whether time is exact, estimated, tentative, or non-timed where this distinction exists;
- reschedule/cancellation state where available.

Events with ambiguous or non-timed release boundaries are structurally ineligible for the first directional trial unless a future protocol explicitly governs them.

DST conversion must be deterministic and testable.

## Consensus semantics
Consensus must represent market/economist expectation available before the release.

For each event, preserve:
- consensus value as supplied;
- consensus range where available;
- forecast count where available;
- consensus observation/update timestamp where available;
- missing-consensus state explicitly.

No imputation of missing consensus is permitted in the first macro-shock family trial.

Events lacking valid contemporaneous consensus are excluded structurally, not assigned zero surprise.

## Actual and revision semantics
Preserve both actual-as-released and revised states when available.

For first-trial surprise construction:
- use actual-as-released;
- do not substitute later revision values;
- preserve revision metadata for audit and diagnostics only unless a later separately admitted hypothesis explicitly concerns revisions.

## Event identity and deduplication
Canonical event identity should be derived from provider event ID where stable, augmented by event-series identity and scheduled release timestamp.

Duplicates must be detected before research use.

If two records share the same economic release but differ because of provider update history, the canonical record must be selected by a frozen point-in-time rule, not by which record improves market alignment.

## Reschedules, cancellations, tentative times
- cancelled events: exclude and retain cancellation record;
- rescheduled events: preserve original schedule and final release lineage;
- tentative/non-timed events: exclude from first directional trial unless exact release time is later established under an auditable rule;
- duplicate scheduled instances caused by provider updates: resolve structurally before market alignment.

## Multiple values within one release
Many releases publish several sub-series simultaneously.

The first family trial may not choose the best-performing sub-series after seeing outcomes.

Before development testing, RND-0063 must freeze one of:
- a single predeclared headline field;
- a deterministic composite defined without market-outcome information;
- or a specific event-family mapping where one released field is economically canonical.

Provider availability of many fields is a disclosed degree of freedom.

## Currency/economy mapping
The initial project instrument universe remains:
- AUDUSD
- EURUSD
- GBPUSD
- USDJPY

Raw event records must map economically to AUD, EUR, GBP, JPY, or USD.

The event-to-pair mapping must be deterministic and frozen before outcome access. No pair may be dropped based on later performance.

## Coverage acceptance gate
A provider must pass a coverage audit for 2015–2020 before being admitted.

The audit must report, without market outcomes:
- event count by year;
- event count by economy/currency;
- event count by candidate event family;
- percentage with valid exact/timed release boundary;
- percentage with contemporaneous consensus;
- percentage with actual-as-released;
- missing-field counts;
- duplicate counts;
- cancellation/reschedule counts;
- unit/schema stability issues;
- provider outages or unexplained temporal gaps.

No minimum event-family count will be chosen after looking at returns. A later RND-0063 admission completion must freeze sample adequacy before market-outcome calculation.

## Cross-provider comparison policy
If more than one provider is acquired for evaluation, compare only structural/provenance characteristics before selecting a canonical source.

Permitted comparisons:
- coverage completeness;
- timestamp precision;
- point-in-time consensus availability;
- actual-as-released preservation;
- revision lineage;
- event identity stability;
- missingness;
- API reproducibility;
- licensing/access feasibility.

Prohibited comparison:
- any FX return, P&L, directional hit rate, surprise-response coefficient, or other market outcome by provider.

Provider selection based on superior trading result is forbidden.

## Immutable raw evidence
Every acquired raw batch must be stored immutably with at minimum:
- provider;
- request/query specification;
- acquisition timestamp;
- raw response hash;
- row/event count;
- covered date range;
- schema/version note;
- parser/version identity;
- normalized-output hash.

Raw provider responses must not be overwritten by later updates.

## Normalization rules
Normalization may:
- parse timestamps;
- normalize numeric units;
- standardize country/currency labels;
- separate actual/consensus/previous/revised fields;
- attach canonical IDs;
- flag missing/ambiguous records.

Normalization may not:
- calculate FX outcomes;
- infer event importance from future price movement;
- choose thresholds from response strength;
- remove weak event families based on performance;
- repair missing consensus through outcome-informed substitution.

## Source acceptance classifications
Allowed classifications:
- `SOURCE_ADMISSIBLE_FOR_STRUCTURAL_NORMALIZATION`
- `SOURCE_ADMISSIBLE_WITH_DOCUMENTED_LIMITATIONS`
- `SOURCE_NOT_ADMISSIBLE_FOR_POINT_IN_TIME_RESEARCH`
- `SOURCE_EVALUATION_INCONCLUSIVE`

Source admission is not strategy admission.

## First acquisition pilot
The first provider pilot must be deliberately small and outcome-blind.

Preferred pilot scope:
- one economy/currency;
- one short historical interval within 2015–2020;
- retrieve event metadata, consensus, actual, revision/timing fields;
- validate raw/normalized hashes and timestamp semantics;
- do not join to FX returns during the pilot.

The pilot provider should be chosen by access practicality and documentation completeness, not expected trading usefulness.

## Candidate-provider notes from documentation review
### Trading Economics
Documentation indicates:
- historical economic calendar access;
- UTC release date/time fields;
- actual, previous, forecast/consensus, revised, currency, unit, source and last-update fields;
- timing-precision metadata;
- a point-in-time calendar method intended to preserve values as they appeared historically.

This makes it a strong first pilot candidate if API access permits the required historical point-in-time queries.

### Econoday
Documentation indicates:
- historical archives back to 2001;
- consensus data;
- actual-as-released data;
- revision data;
- release timestamps and stable event identifiers;
- international coverage.

This makes it a strong alternative or cross-check candidate subject to access/licensing.

### LSEG/Reuters
Documentation/community material indicates economic-indicator/poll fields including Reuters Poll and historical economic data fields. It remains a credible institutional alternative, but admission requires a concrete reproducible extraction path and access entitlement.

## Required hostile structural tests
Before any provider is admitted, tooling must prove at minimum:
1. missing consensus stays missing;
2. revised actual cannot overwrite actual-as-released silently;
3. timezone normalization is deterministic;
4. ambiguous/non-timed event is excluded from exact-time trial eligibility;
5. cancellation is preserved and excluded;
6. reschedule lineage is preserved;
7. duplicate event identity is detected;
8. schema unit changes are surfaced;
9. missing raw-source identity fails provenance;
10. normalized rows retain raw hash lineage;
11. future market outcomes are not accepted by the normalizer;
12. provider selection object contains no market-performance fields;
13. 2021–2022 validation data cannot enter the source-normalization task;
14. 2023–2024 reserved final cannot enter;
15. Q003 prospective outcomes cannot enter;
16. RND-0060Q/R prospective outcomes cannot enter;
17. deterministic replay produces identical normalized output;
18. no authority field can become TRUE.

## Authority state
- strategy_outcome_open: FALSE
- validation_open: FALSE
- reserved_final_open: FALSE
- prospective_outcomes_open: FALSE
- candidate_freeze: FALSE
- promotion_authority: FALSE
- broker_write_authority: FALSE
- capital_authority: FALSE
- live_execution_authority: FALSE
- automatic_merge: FALSE

## Exit condition
RND-0064 is complete only when at least one candidate provider has passed an outcome-blind pilot and structural provenance tests strongly enough to receive a source-admission classification.

Only then may RND-0063 be revisited to freeze the exact macro event universe, surprise mapping, timing, cost assumptions, minimum effect, and sample adequacy before a development trial is opened.
