# RND-0065A — Low-Cost Macro Data Provider Comparison

## Status
FROZEN PROVIDER-COMPARISON REVIEW — NO FX OUTCOMES OPENED — NO PROVIDER PURCHASED

## Purpose
Determine whether a lower-cost macro-event data architecture can satisfy the RND-0064 point-in-time provenance requirements sufficiently to unblock RND-0063, without committing the project to Trading Economics.

This review is provider-selection research only. No strategy outcome, FX response, P&L, candidate promotion, broker authority, capital authority, or reserved-final evidence is opened.

## Core architectural principle
The project must remain provider-substitutable.

The canonical macro-event schema and RND-0064 provenance guard are authoritative. Any external vendor is only an acquisition adapter. A provider may be replaced later if a replacement can be normalized to the same canonical schema and independently satisfy the frozen provenance requirements.

Changing provider must never be conditioned on which source produces a more attractive strategy result.

## Required fields / properties
A source suitable for RND-0063 must support or permit defensible reconstruction of:
- event identity / indicator identity;
- economy / currency relevance;
- release timestamp with adequate precision;
- actual value as released at the time;
- contemporaneous consensus / estimate where the strategy requires surprise direction;
- previous value and revision lineage where relevant;
- unit / reference period;
- source / acquisition provenance;
- deterministic raw-response hashing;
- repeatable acquisition for the frozen historical development interval.

A cheap source that supplies present-day revised values but cannot establish what was known at the time is not sufficient for point-in-time strategy research.

## Candidate assessment

### 1. FRED / ALFRED — preferred free provenance backbone
Cost: free API access with account/API key.

Strengths:
- ALFRED explicitly preserves historical real-time periods / vintages and revisions.
- FRED API supports initial-release-only and vintage-date retrieval.
- Release-date endpoints and source/release metadata are available.
- Excellent for verifying official US macro values and revision histories.

Limitations:
- not a general survey-consensus database;
- release dates do not necessarily prove exact intraday availability time for every series;
- narrower geographic usefulness than a global calendar vendor.

Assessment:
`ADMISSIBLE_AS_REVISION_AND_OFFICIAL_VALUE_BACKBONE`, but insufficient alone for a consensus-surprise strategy.

### 2. EODHD Economic Events API — first low-cost calendar pilot candidate
Published economic-event coverage: from 2020.
Documented fields include date/time, country, actual, previous, estimate, type, period and comparison.
Public personal plans start well below Trading Economics; provider also offers a free/sandbox entry path.

Strengths:
- low acquisition cost;
- simple historical economic-event endpoint;
- actual/estimate/previous fields directly map to much of the canonical schema;
- API documentation is machine-readable and suitable for a small structural pilot.

Limitations:
- available event history beginning in 2020 does not cover the full current DEVELOPMENT_2015_2020 interval;
- documentation reviewed does not establish point-in-time snapshots preserving the contemporaneous estimate through later corrections;
- revision lineage semantics are not documented strongly enough for automatic admission.

Assessment:
`HIGH_PRIORITY_LOW_COST_STRUCTURAL_PILOT`, but cannot by itself support the full 2015–2020 development design unless the research partition is separately and prospectively redesigned before outcome access. It must also prove historical-estimate integrity in a pilot.

### 3. Financial Modeling Prep (FMP) Economic Calendar — second low-cost pilot candidate
Documented fields include date/time, country, event, currency, previous, estimate, actual, change, impact and unit.
A free Basic plan exists; paid personal plans begin below Trading Economics.

Strengths:
- free exploratory access advertised;
- useful calendar schema with actual/estimate/previous and currency;
- low-cost paid tiers relative to Trading Economics.

Limitations:
- reviewed documentation describes an economic calendar but does not prove historical point-in-time consensus preservation or revision lineage;
- historical depth/access varies by subscription tier;
- exact release-time provenance and stable historical identity need to be demonstrated empirically.

Assessment:
`HIGH_PRIORITY_LOW_COST_STRUCTURAL_PILOT` after or alongside EODHD, subject to RND-0064 guard.

### 4. Finnhub Economic Data API — mid-cost candidate
Published price: USD 50/month, billed quarterly, personal-use licence.
Published coverage: global economic data up to 50 years and global economic calendar 10 years.

Strengths:
- materially cheaper than Trading Economics Standard pricing;
- broader documented historical calendar depth than EODHD;
- global scope potentially compatible with AUD/EUR/GBP/JPY/USD research.

Limitations:
- current pricing structure implies a larger upfront commitment than a one-month USD 50 test because billing is quarterly;
- reviewed public material does not establish point-in-time consensus snapshot semantics or revision lineage to the RND-0064 standard.

Assessment:
`SECONDARY_PILOT_CANDIDATE`; attractive historical depth, but cost commitment and point-in-time semantics should be verified before purchase.

### 5. Trading Economics — benchmark / fallback provider
Strengths:
- explicitly documents point-in-time economic-calendar retrieval preserving original values before subsequent revisions;
- documents actual, previous, revised, consensus/forecast and release timestamps;
- strongest documentation match to the RND-0064 requirement among candidates reviewed.

Limitations:
- substantially higher cost than free/low-cost alternatives;
- unnecessary if a cheaper architecture can demonstrate equivalent point-in-time integrity.

Assessment:
`REFERENCE_BENCHMARK_AND_FALLBACK`, not mandatory.

## Provider-substitution rule
Yes, Trading Economics can be substituted later.

A provider change is admissible only if:
1. the replacement adapter maps to the frozen canonical RND-0064 schema;
2. the replacement passes the same provenance/duplicate/timestamp/revision guards;
3. the selection rationale is documented without consulting FX strategy outcomes;
4. event-universe differences are measured and documented;
5. any change in historical coverage is treated as a data-protocol change requiring a separate human-reviewed gate;
6. the project never cherry-picks between providers after comparing trading performance.

If two sources coexist, one may be used as an independent provenance cross-check, but not as an outcome-driven selector.

## Recommended lowest-cost acquisition sequence
1. Use FRED/ALFRED as the no-cost official-value/revision backbone for US releases where applicable.
2. Run an outcome-blind structural pilot against EODHD using only provider event records and the RND-0064 guard.
3. Run the same structural pilot against FMP if its free access exposes sufficient historical rows.
4. If neither can establish contemporaneous-consensus integrity and sufficient coverage, evaluate Finnhub before paying Trading Economics.
5. Use Trading Economics only if the lower-cost stack fails the frozen provenance standard or cannot provide a defensible historical research sample.

## Important development-partition constraint
EODHD states that economic-event history is available from 2020. The existing project development partition is 2015–2020.

Therefore EODHD cannot silently replace a source capable of covering 2015–2020. Permissible outcomes of its pilot are:
- useful cross-check / schema proof only;
- later supplementary source;
- or basis for a separately frozen future study using a new admissible data interval.

It may not justify changing the current RND-0063 development interval after outcome inspection.

## Decision
Do not purchase Trading Economics at this stage.

Proceed first with zero/low-cost structural pilots, beginning with EODHD and FMP, while using FRED/ALFRED for official-vintage validation where possible.

Trading Economics remains available as a later fallback and may be substituted into or out of the architecture because provider-specific logic is isolated behind the canonical normalization/provenance layer.

## Authority
No provider purchase authority.
No market-outcome access.
No Q003 or RND-0060Q/R outcome access.
No 2021–2022 validation access.
No 2023–2024 reserved-final access.
No broker-write authority.
No capital authority.
No live-execution authority.
No automatic merge.
