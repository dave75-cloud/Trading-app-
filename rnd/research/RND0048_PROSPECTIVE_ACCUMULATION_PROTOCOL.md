# RND-0048 — Prospective Validation Accumulation Protocol

Status: **PREDECLARED / OUTCOME BLIND**

## Purpose

RND-0048 governs accumulation of genuinely prospective evidence for the frozen Q003 candidate before any validation outcome is permitted to be computed.

This task is deliberately outcome-blind. It authorizes evidence accumulation and structural verification only. It does not authorize Q003 signal generation, trade simulation, returns, P&L, equity, drawdown, win rate, strategy comparison, validation classification, promotion, broker writes, or capital allocation.

## Frozen candidate

Candidate: `Q003`

Candidate fingerprint:

`25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`

The candidate must remain byte-for-byte semantically identical to the RND-0046 freeze manifest. Any rule, pair, threshold, session, delay, hold, price/execution, or gap-semantics change creates a new candidate and invalidates this accumulation protocol for that altered candidate.

## Prospective boundary

First admissible fresh candle:

`2026-10-05T07:25:00Z`

Evidence before that boundary is not part of RND-0048 prospective validation, including 2025 and pre-freeze 2026 history.

The consumed 2021–2022 validation interval remains unavailable for new validation claims.

The reserved-final 2023–2024 interval remains sealed and unavailable.

## Minimum accumulation horizon

No validation outcome may be opened before BOTH conditions below are satisfied:

1. at least **180 calendar days** have elapsed from the prospective boundary; and
2. sealed evidence spans continuously from the prospective boundary through at least the first M5 boundary at or after that horizon, subject only to explicitly preserved provider/market gaps.

Earliest permissible validation-readout boundary:

`2027-04-03T07:25:00Z`

This is a minimum, not a forced stop date. Structural defects may require further accumulation. Outcome information may not be used to shorten, extend, or otherwise choose the accumulation horizon because outcomes remain unavailable until the readout gate is separately opened by a human.

## Evidence accumulation rules

Every accepted tranche must:

- be OANDA fxTrade PRACTICE historical candle evidence acquired through authenticated GET only;
- contain AUDUSD, EURUSD, GBPUSD, and USDJPY;
- use M5 complete candles only;
- retain bid, ask, and mid OHLC;
- preserve exact provider timestamps;
- preserve raw response bytes and raw SHA-256 evidence;
- preserve canonical row SHA-256 evidence;
- preserve explicit gap ledgers;
- be immutable and non-overwriting;
- be bound to the frozen Q003 candidate fingerprint;
- contain no strategy metrics.

Tranches may be small and frequent. Tranche size is operational and may vary without changing the scientific protocol, provided chronology and identity remain auditable.

## Cumulative structural acceptance

Before any validation-readout gate can be considered, a cumulative structural audit must demonstrate:

- exact candidate fingerprint match;
- exact four-symbol universe throughout;
- no duplicate candle timestamps within a symbol;
- no overlapping duplicated evidence between accepted tranches;
- monotonic chronological ordering;
- all gaps explicitly represented rather than interpolated or filled;
- no synthetic candles;
- no incomplete candles;
- raw and canonical SHA-256 integrity for every accepted tranche;
- prospective start boundary preserved;
- cumulative end boundary at or beyond `2027-04-03T07:25:00Z`;
- no access to reserved-final evidence;
- no strategy evaluation during accumulation.

RND-0048 does not require a predeclared trade count because trade count would require running the frozen strategy and would therefore leak outcome-adjacent information during accumulation. The 180-day time horizon is intentionally fixed without reference to prospective trading results.

## No-peeking rule

Until a separate human-authorized validation-readout task exists, the following are prohibited on RND-0048 evidence:

- generate Q003 signals;
- simulate entries or exits;
- count candidate trades;
- calculate gross or net returns;
- calculate transaction-cost drag attributable to Q003;
- calculate equity or drawdown;
- calculate hit rate or win rate;
- compare Q003 with Q000 or any other rule;
- rank pairs by strategy performance;
- remove or reweight a pair;
- change the ratio threshold;
- inspect outcome summaries and then alter the accumulation horizon.

Structural candle counts, timestamps, hashes, provenance records, and gap ledgers are permitted.

## Stop / extend logic

At the 180-day minimum horizon:

- if cumulative structural integrity passes, the evidence package becomes **READOUT_ELIGIBLE_PENDING_HUMAN_GATE**;
- if structural integrity fails, accumulation continues until the defect is resolved or explicitly classified as an irrecoverable provider/market gap;
- no strategy outcome may determine whether to stop or extend accumulation.

## Authority

- prospective evidence accumulation: **TRUE**
- structural integrity verification: **TRUE**
- candidate modification: **FALSE**
- strategy evaluation: **FALSE**
- validation classification: **FALSE**
- pair dropping: **FALSE**
- pair-specific rules: **FALSE**
- pair weighting: **FALSE**
- new ratio thresholds: **FALSE**
- reserved-final access: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human readout gate required: **TRUE**
