# RND-0066 — FRED/ALFRED Macro Provenance Backbone Architecture

## Status
GOVERNED ARCHITECTURE — OUTCOME-BLIND — NO MACRO ACQUISITION — NO FX OUTCOMES OPENED

## Purpose
Define how FRED/ALFRED can serve as the preferred free historical official-value and revision-provenance backbone for the RND-0063 scheduled macro-information shock research family, without weakening the frozen RND-0064 canonical macro-event schema or creating look-ahead bias.

RND-0066 is an architecture/provenance phase. It does not acquire provider data, join macro events to FX prices, calculate surprise signals, inspect returns, tune a hypothesis, purchase a provider, or alter any prospective track.

## Governing inheritance
RND-0066 inherits without modification:
- RND-0062 research-admission and multiple-hypothesis standard;
- RND-0063 finding that macro-shock directional research remains inadmissible until a defensible point-in-time macro dataset exists;
- RND-0064 canonical event schema and provenance guard;
- RND-0065 provider-pilot safety posture;
- RND-0065A provider-substitution and low-cost architecture principles.

The canonical RND-0064 event schema remains authoritative. FRED/ALFRED is a source component, not a replacement schema.

## Verified FRED/ALFRED capabilities
Current Federal Reserve documentation establishes that the FRED API can:
- return series observations with `realtime_start` / `realtime_end` real-time periods;
- return observations by specified historical `vintage_dates`;
- return observations by vintage date;
- return new/revised observations by vintage date;
- return `output_type=4`, observations at initial release only;
- return series vintage dates, defined as dates when values were revised or new values were released;
- return release and release-date metadata.

These capabilities make FRED/ALFRED suitable as a historical official-value/revision-provenance backbone, particularly for US macro series.

## Critical limitation: date is not M5 release time
The FRED release-date documentation explicitly states that release dates are published by data sources and do not necessarily represent when data are available on FRED or ALFRED.

Accordingly:
- a FRED/ALFRED vintage date is date-level provenance, not proof of an exact intraday release timestamp;
- a FRED release date is not automatically an exact tradable availability timestamp;
- RND-0066 MUST NOT promote any date-only FRED/ALFRED evidence to `timestamp_precision=EXACT`;
- M5 event alignment requires separately proven timezone-aware release-time evidence.

This is a hard anti-look-ahead rule.

## Critical limitation: consensus
FRED/ALFRED is not treated as a historical market-consensus provider for this research family.

Therefore:
- missing consensus MUST remain missing;
- no FRED forecast, model forecast, survey surrogate, previous value, or later estimate may be substituted for contemporaneous market consensus;
- no synthetic consensus may be manufactured from historical values;
- an event cannot become directional-surprise eligible until a separately governed source establishes a contemporaneous pre-release market consensus.

## Split-source architecture
The governed architecture is:

1. **FRED/ALFRED backbone**
   - official series identity;
   - historical observations;
   - initial-release value where `output_type=4` or an equivalently demonstrated initial-vintage rule establishes it;
   - historical vintages and revision lineage;
   - source metadata;
   - immutable raw-response hash and acquisition provenance when acquisition later occurs.

2. **Independent timing evidence**
   - exact scheduled/release timestamp;
   - timezone/UTC normalization;
   - stable event identity;
   - cancellation/reschedule state where relevant;
   - source provenance.

   Date-only FRED/ALFRED release metadata cannot fill this role for an M5 trial.

3. **Independent consensus evidence**
   - contemporaneous market/economist consensus;
   - evidence that the value was available before release;
   - provider/source identity;
   - historical point-in-time integrity;
   - immutable raw-response hash.

4. **RND-0064 canonical composition layer**
   - deterministic predeclared cross-source linkage;
   - field-level provenance;
   - duplicate detection;
   - chronology guard;
   - canonical normalized record;
   - no FX outcome fields.

## Field ownership
The composite record MUST preserve field-level provenance. A composite event may not imply that one provider supplied fields actually obtained from another.

Minimum ownership:
- `actual_as_released`: FRED/ALFRED initial-release evidence, when proven;
- revision lineage: FRED/ALFRED;
- `scheduled_timestamp_utc`: independent exact timing source;
- `consensus`: independent historical point-in-time consensus source;
- event link identity: predeclared deterministic mapping;
- raw hashes/source identities: preserved for every component.

The canonical provider label for a joined record is a composite architecture identity, not a claim that FRED supplied timing or consensus.

## Deterministic join rule
Cross-source joins must be frozen before FX outcome access.

Every component must carry the same predeclared `link_key`. A join is rejected if any of the following differ:
- link key;
- economy;
- affected currency;
- reference period.

The consensus capture/update time must be strictly before the exact scheduled release time.

A fuzzy event-name match, nearest timestamp, or outcome-informed manual correction is not admissible.

## Initial-release semantics
For directional surprise construction, `actual_as_released` may be populated from FRED/ALFRED only when the acquisition record is explicitly established as the initial release.

A later vintage may be retained for revision lineage, but it may never overwrite the initial value used as `actual_as_released`.

## Structural eligibility states
RND-0066 distinguishes:
- `BACKBONE_ONLY`: official/vintage evidence exists but exact timing and/or consensus is absent;
- `STRUCTURAL_JOIN_READY`: independent components exist and deterministic identity/chronology checks can run;
- `SURPRISE_INPUT_ELIGIBLE`: initial actual, exact independently proven timing, contemporaneous point-in-time consensus, identity, chronology, and provenance all pass.

`SURPRISE_INPUT_ELIGIBLE` means only that macro inputs are structurally eligible. It does not admit a trading strategy, authorize market-outcome inspection, or imply economic efficacy.

## Geographic scope
FRED/ALFRED is strongest as a US official-value/revision backbone. RND-0066 does not assume equivalent coverage for Australia, Euro Area, United Kingdom, or Japan.

The four-pair research universe remains AUDUSD, EURUSD, GBPUSD, USDJPY. Non-US official-value provenance may later require other authoritative statistical-source adapters. That extension must preserve the same canonical field/provenance contract.

No pair or economy may be removed because of eventual trading performance.

## Development partition
The existing macro-research development interval remains `DEVELOPMENT_2015_2020` unless a separately governed, human-reviewed protocol changes it before outcome inspection.

RND-0066 does not open:
- consumed validation 2021–2022;
- reserved-final 2023–2024;
- Q003 prospective outcomes;
- RND-0060Q/R prospective economic outcomes.

## Acquisition policy
RND-0066 itself performs no acquisition.

A later acquisition pilot may use FRED/ALFRED only after:
- a small series/economy scope is frozen;
- API credentials are supplied through environment/configuration rather than chat or committed source;
- request identity and raw hashing are defined;
- raw evidence is immutable;
- exact timing and consensus sources are separately governed.

No provider subscription or purchase authority is created here.

## Hostile requirements
The implementation firewall must prove at minimum:
1. FRED/ALFRED alone cannot become surprise eligible;
2. date-only/vintage evidence cannot masquerade as exact intraday timing;
3. missing consensus cannot be synthesized;
4. FRED/ALFRED cannot masquerade as a market-consensus source;
5. consensus must be demonstrably point-in-time and pre-release;
6. cross-source link-key mismatch is rejected;
7. economy/currency/reference-period mismatch is rejected;
8. later revisions cannot overwrite initial actual;
9. field-level provenance survives composition;
10. duplicate canonical event identity is rejected;
11. no market-outcome fields enter the architecture;
12. all execution/promotion/capital authorities remain false.

## Decision
Adopt FRED/ALFRED as the preferred free official-value/revision-provenance backbone where its series coverage is suitable.

Do **not** treat FRED/ALFRED as a standalone macro-surprise dataset. Exact intraday timing and contemporaneous market consensus remain independent evidentiary requirements.

The next scientific step after this architecture is verified should be a small, outcome-blind **FRED/ALFRED backbone acquisition feasibility pilot**, followed separately by evaluation of the cheapest defensible timing/consensus source. No FX response should be opened until the complete joined dataset passes RND-0064 and the RND-0063 admission review is formally completed.

## Authority
No market-outcome access.
No validation access.
No reserved-final access.
No prospective-outcome access.
No broker-write authority.
No capital authority.
No live-execution authority.
No provider-purchase authority.
No automatic merge.
