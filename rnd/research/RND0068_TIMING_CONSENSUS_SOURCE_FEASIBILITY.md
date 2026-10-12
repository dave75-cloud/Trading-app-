# RND-0068 — Timing & Consensus Source Feasibility

## Status
GOVERNED SOURCE FEASIBILITY — OUTCOME-BLIND — NO PROVIDER PURCHASE — NO FX OUTCOMES OPENED

## Purpose
Determine the cheapest defensible architecture for the two macro-event fields still missing after RND-0067:
1. exact historical release timing suitable for M5 event alignment; and
2. contemporaneous pre-release market consensus suitable for surprise construction.

RND-0068 does not acquire FX prices, calculate returns, inspect P&L, tune a strategy, purchase a provider, or open validation/reserved/prospective outcomes.

## Inheritance
RND-0068 inherits without modification:
- RND-0062 research-admission and multiplicity controls;
- RND-0063 macro-shock admission requirement;
- RND-0064 canonical schema/provenance guard;
- RND-0065/0065A low-cost provider discipline;
- RND-0065B FRED/ALFRED backbone architecture;
- RND-0066 split-source timing/consensus firewall;
- RND-0067 live structural proof of the FRED/ALFRED official-value/revision backbone.

## Timing conclusion
For US Bureau of Labor Statistics releases, official historical BLS release schedules and archived releases are suitable as the preferred free timing source when they establish:
- exact scheduled public release date;
- exact release clock time;
- explicit Eastern Time context;
- release identity;
- historical source provenance.

The 2019 BLS release schedule, for example, lists CPI and Employment Situation releases at 08:30 AM Eastern Time and states that schedule times are Eastern Time.

This evidence can support `timestamp_precision=EXACT` only after deterministic timezone conversion using the historical US Eastern daylight-saving regime for the event date. A hard-coded UTC offset is prohibited.

Official-source timing is preferred over a commercial calendar where feasible because it is cheaper and closer to the primary release authority.

## Consensus conclusion
Consensus remains a separate evidentiary problem.

A consensus provider is admissible only if it can demonstrate all of the following:
- historical coverage spanning the governed development interval as needed;
- a genuine survey/market/economist consensus, not a vendor model forecast;
- point-in-time reconstruction or retained snapshots proving what was known before release;
- event identity and reference-period metadata sufficient for deterministic linkage;
- timestamps or update metadata sufficient to prove consensus existed before the release;
- immutable request/response provenance;
- no outcome-informed provider selection.

## Provider findings frozen at RND-0068

### Trading Economics
Classification: `CONSENSUS_PILOT_CANDIDATE_DOCUMENTED_POINT_IN_TIME`

Positive evidence:
- documents point-in-time economic-calendar retrieval;
- calendar schema distinguishes `Forecast` (consensus) from `TEForecast` (vendor model forecast);
- provides event Date in UTC, unique CalendarID, Reference/ReferenceDate, Source, Actual, Previous, Forecast, Revised, DateSpan, LastUpdate;
- describes survey consensus as the average forecast among a representative group of economists.

Caveats:
- API access is paid beyond limited trial/demo arrangements;
- purchase is NOT authorized by RND-0068;
- actual historical coverage for the exact pilot event family must be demonstrated before selection;
- any trial must prove point-in-time consensus integrity using the same event window without opening FX outcomes.

### EODHD
Classification: `NOT_PRIMARY_DEVELOPMENT_CONSENSUS_SOURCE_COVERAGE_INSUFFICIENT`

Reason:
- its documented Economic Events API history is available from 2020;
- this cannot by itself support the full governed 2015–2020 development interval.

It may later be useful for prospective or post-2020 cross-checking, but cannot be chosen as the primary historical consensus source for this research family on current evidence.

### Financial Modeling Prep
Classification: `UNRESOLVED_POINT_IN_TIME_CONSENSUS_INTEGRITY`

Positive evidence:
- economic calendar exposes date, country, event, currency, previous, estimate, actual, impact, unit.

Unresolved issue:
- current documentation reviewed in RND-0068 does not establish that historical `estimate` values are immutable point-in-time consensus snapshots available before each release.

No admission until this is proven independently.

### Finnhub
Classification: `UNRESOLVED_POINT_IN_TIME_AND_COVERAGE_FIT`

Positive evidence:
- advertises global economic-calendar history.

Unresolved issues:
- point-in-time consensus semantics were not established by the reviewed documentation;
- advertised calendar-history horizon must be shown to cover the full required 2015–2020 development interval for the exact event set.

No purchase or selection is authorized.

## Cost conclusion
Do not buy Trading Economics yet.

Preferred order:
1. use free official-source timing wherever defensible (BLS first for US CPI/employment releases);
2. build and hostile-test the official timing adapter independently;
3. run a very small outcome-blind consensus feasibility probe using a provider only if point-in-time historical consensus can be demonstrated;
4. pay only for the smallest missing evidentiary component after free sources have been exhausted.

## Deterministic join rule
No timing or consensus source may be joined to the FRED/ALFRED backbone by fuzzy name similarity or nearest timestamp.

The join contract must predeclare:
- event family / link key;
- economy;
- currency;
- reference period;
- official release identity;
- scheduled timestamp;
- consensus provider event identity.

Consensus must have a proof timestamp strictly before the scheduled release timestamp.

## Timezone rule
For official US schedules expressed in Eastern Time:
- timezone identity must be `America/New_York` or an equivalently governed historical timezone implementation;
- daylight-saving conversion must be date-aware;
- naive `ET = UTC-5` or `ET = UTC-4` assumptions are prohibited;
- ambiguous/nonexistent local times must fail closed.

## Provider-selection firewall
A provider may not be selected, retained, replaced, or rejected because its consensus happens to improve FX backtest performance.

Selection criteria are limited to provenance, historical point-in-time integrity, timing precision, coverage, deterministic identity, reliability, reproducibility, and cost.

## Authority
No FX outcomes opened.
No validation access.
No reserved-final access.
No prospective economic outcomes opened.
No broker-write authority.
No capital authority.
No live-execution authority.
No provider-purchase authority.
No automatic merge.

## Decision
RND-0068 adopts a split-source plan:
- **official primary-source schedules first for exact timing**, beginning with BLS for US CPI/employment families;
- **commercial consensus only where necessary**, with Trading Economics currently the strongest documented pilot candidate but not yet purchased or selected as production dependency.

## Next governed step
Implement and hostile-test an outcome-blind BLS historical timing adapter for a frozen CPI sample, including historical Eastern-to-UTC conversion and deterministic linkage to the RND-0067 FRED backbone. This timing adapter must not contain consensus or FX outcome data.
