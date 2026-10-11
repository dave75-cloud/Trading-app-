# RND-0065B — FRED/ALFRED Macro Backbone Architecture

## Status
FROZEN ARCHITECTURE — NO FX OUTCOME OPENED

## Purpose
Adopt FRED/ALFRED as the low-cost authoritative backbone for official macroeconomic release values, historical vintages, revision lineage, and release identity, while preserving a replaceable adapter for contemporaneous consensus expectations and, where necessary, exact event-time timestamps.

This architecture is provider-agnostic above the canonical macro-event schema and does not bind the research program permanently to Trading Economics or any other commercial provider.

## Core architecture

### Layer A — FRED/ALFRED authoritative backbone
Responsibilities:
- official series identity;
- official source/release identity;
- observation values;
- initial-release values where available;
- vintage dates;
- revision lineage;
- historical 'what was known when' retrieval using ALFRED real-time periods;
- reproducible API retrieval with immutable request metadata and raw hashes.

Preferred API semantics:
- `fred/series/observations` with `output_type=4` for initial release where appropriate;
- `vintage_dates` for historical snapshots;
- `realtime_start` / `realtime_end` for ALFRED point-in-time reconstruction;
- `fred/series/vintagedates` for revision/new-release dates;
- `fred/release/dates` / `fred/releases/dates` for release identity/date metadata.

### Layer B — Consensus adapter
Responsibilities:
- contemporaneous consensus/median expectation as available immediately before release;
- survey/provider identity;
- timestamp or snapshot time proving when the expectation was known;
- stable event mapping into the FRED/ALFRED release/series identity;
- raw request/response hashes and provenance.

The consensus provider is replaceable. Candidate sources may include EODHD, FMP, Finnhub, Trading Economics, Econoday, or another source that later passes the RND-0064 provenance protocol.

No provider may be selected or replaced based on which produces a superior FX backtest.

### Layer C — Event-time adapter
Responsibilities:
- exact scheduled release timestamp in UTC;
- timing precision classification;
- reschedule/cancellation semantics;
- proof that the timestamp corresponds to the economically relevant public release time.

FRED/ALFRED release dates are not automatically treated as executable event timestamps. The St. Louis Fed documentation explicitly notes that published release dates do not necessarily represent when data became available on FRED/ALFRED. Accordingly, exact intraday timing must be independently validated.

This layer may be supplied by the same provider as Layer B or by a separate low-cost source.

### Layer D — Canonical RND-0064 event schema
The strategy/research layer consumes only canonical normalized records. It must not depend directly on vendor-specific field names or endpoints.

Canonical record should preserve at minimum:
- canonical event identity;
- official series/release identity;
- economy/currency relevance;
- exact or classified release timestamp;
- official actual-as-released value;
- prior value and revision lineage where relevant;
- contemporaneous consensus;
- unit/reference period;
- provider identities for each component;
- raw and normalized hashes;
- partition identity;
- authority fields fixed FALSE.

## Join semantics
A research-eligible surprise event requires a deterministic join among:
1. official FRED/ALFRED series/release identity;
2. exact event timestamp source;
3. contemporaneous consensus source.

The join key must be frozen before any FX outcome is opened. Matching may use approved combinations of official release ID, series ID, reference period, economy, event family, and scheduled timestamp.

Fuzzy post-outcome joining is prohibited.

## Point-in-time rule
For official values, ALFRED real-time/vintage semantics are authoritative where available. Current revised FRED values must never be substituted for what was known at the historical release time.

For consensus, the adapter must prove that the stored estimate existed before the release. A current vendor field labelled `estimate` is not sufficient by itself unless provider documentation or retained historical snapshots establish its contemporaneous nature.

## Revision rule
The backbone preserves:
- initial actual-as-released value;
- later revisions separately;
- vintage/revision dates;
- immutable lineage between them.

Later revisions must never overwrite the original event surprise input.

## Timestamp rule
Date-only release metadata is insufficient for an intraday macro-shock strategy.

An event is `EXACT_TIME_ELIGIBLE` only when an independently validated source provides an exact scheduled/public release timestamp with acceptable precision.

Otherwise classify as one of:
- `DATE_ONLY_NOT_TRADABLE`;
- `TIME_ESTIMATED_NOT_PRIMARY_ELIGIBLE`;
- `TIME_TENTATIVE_NOT_PRIMARY_ELIGIBLE`;
- `TIMESTAMP_SOURCE_CONFLICT_REQUIRES_REVIEW`.

## Cost discipline
FRED/ALFRED is the default backbone because it offers authoritative vintage/revision functionality without requiring a premium macro-calendar subscription.

Commercial spend is limited to the smallest missing component necessary to satisfy:
- contemporaneous consensus integrity;
- exact event-time integrity;
- adequate historical coverage.

The architecture allows the commercial component to be substituted later without changing the strategy specification, provided the replacement maps to the same canonical schema and passes the same provenance tests.

## Pilot order
1. Obtain a free FRED API key.
2. Run an outcome-blind FRED/ALFRED structural pilot on a small frozen set of US macro series/releases.
3. Verify initial-release retrieval, vintage lineage, deterministic hashes, and release identity.
4. Separately pilot one low-cost consensus/timestamp provider.
5. Test deterministic joins without loading FX outcomes.
6. Only after all provenance gates pass, return to RND-0063 admission review.

## Initial pilot scope
The first FRED/ALFRED pilot is structural only and must use a small predeclared set of high-profile US releases with clear official series lineage. The pilot must not compute FX returns, price responses, signals, P&L, rankings, or strategy metrics.

Suggested pilot families for source/provenance testing only:
- CPI;
- nonfarm payroll / employment situation components;
- retail sales;
- GDP advance/revisions;
- PCE inflation.

Exact series IDs and release IDs must be frozen before retrieval.

## Governance
Unchanged:
- DEVELOPMENT_2015_2020 only for future strategy development unless separately governed;
- validation 2021–2022 remains consumed;
- reserved final 2023–2024 remains sealed;
- Q003 prospective outcomes remain sealed;
- RND-0060Q/R prospective economic outcomes remain sealed;
- promotion authority FALSE;
- broker-write authority FALSE;
- capital authority FALSE;
- live-execution authority FALSE;
- automatic merge FALSE.

## Exit criteria
RND-0065B architecture is considered ready for implementation when:
- FRED/ALFRED role is frozen as official-value/vintage backbone;
- consensus role is explicitly external and replaceable;
- exact timestamp role is explicitly external or independently validated;
- canonical join semantics are frozen;
- no market outcome has been opened.
