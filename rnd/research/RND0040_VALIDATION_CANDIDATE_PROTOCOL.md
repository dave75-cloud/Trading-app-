# RND-0040 — Predeclared Validation Candidate Protocol

Status: **PREDECLARED / VALIDATION OUTCOMES CLOSED**

## Purpose

RND-0040 freezes the higher-volatility candidate emerging from RND-0039 and predeclares the protocol by which it may later be evaluated on the untouched RND-0029 validation partition. This task does not open validation outcomes and does not authorize acquisition or strategy evaluation by itself.

The scientific purpose is confirmation or falsification of a development-derived hypothesis, not further optimization.

## Candidate identity

The sole validation candidate is the otherwise-frozen M005 configuration with volatility eligibility threshold `0.0006`.

All other semantics remain fixed:

- fast MA 20;
- slow MA 50;
- volatility window 12;
- population standard deviation (`ddof=0`);
- signal delay 1 eligible observed bar;
- minimum hold 3 observed bars;
- frozen UTC sessions unchanged;
- bid/ask execution unchanged;
- gap semantics unchanged;
- four-symbol universe unchanged: AUDUSD, EURUSD, GBPUSD, USDJPY.

The candidate is **not** a promoted strategy. The development result at `0.0006` is hypothesis-generating/supporting evidence only.

No threshold other than `0.0006` may be evaluated as a candidate under this protocol. In particular:

- no threshold grid;
- no threshold above or below `0.0006`;
- no pair-specific threshold;
- no pair removal;
- no session change;
- no MA change;
- no delay/hold/latency change;
- no cost assumption tuning;
- no outcome-dependent exclusion or reweighting.

## Validation partition

Bound exactly to RND-0029:

- start inclusive: `2020-12-31T19:15:00Z`;
- end exclusive: `2023-01-01T09:40:00Z`;
- timeframe: M5;
- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY.

Reserved final test begins at `2023-01-01T09:40:00Z` and remains sealed.

## Warm-up rule

At most 50 genuine M5 observations immediately prior to the validation start may initialize indicator/state only.

Warm-up rows:

- may not generate trades;
- may not contribute returns;
- may not contribute P&L/equity/drawdown;
- may not influence parameter choice;
- must come only from the development partition;
- must be explicitly identified and excluded from validation outcomes.

## Primary validation question

Does the fixed `0.0006` candidate demonstrate positive, economically credible, non-concentrated net performance on the untouched validation partition without changing any strategy rule?

## Predeclared primary decision rule

The candidate may be classified **VALIDATION_SUPPORTED** only if all of the following are true on validation evidence:

1. observed four-pair equal-unit normalized terminal equity index is strictly greater than `1.000000`;
2. realized completed-trade net-return sum across the four pairs is strictly greater than `0`;
3. at least **3 of 4 pairs** have completed-trade net equity index `>= 1.000000`;
4. no single pair contributes more than **70%** of positive aggregate completed-trade net-return sum;
5. no single calendar year contributes more than **70%** of positive aggregate completed-trade net-return sum;
6. four-pair equal-unit normalized maximum drawdown is no worse than `-0.10`;
7. there are no evidence-identity, boundary, leakage, or warm-up violations.

If any of criteria 1, 2, 6, or 7 fail, classification is **VALIDATION_REJECTED**.

If criteria 1, 2, 6, and 7 pass but one or more of criteria 3–5 fail, classification is **VALIDATION_INCONCLUSIVE_CONCENTRATED** and no promotion is permitted.

No criterion may be relaxed after validation outcomes are visible.

## Secondary diagnostics

The following are descriptive/falsification diagnostics only and may not override the primary rule:

- per-pair trade count, hit rate, gross/net equity, max drawdown and execution-cost drag;
- per-year and pair×year concentration;
- additional round-trip cost break-even by pair;
- frozen stationary-bootstrap diagnostics using the already-declared RND-0035 configuration family;
- observed four-pair concurrent reference statistics;
- comparison with the development candidate record for directional consistency.

The frozen R000 `0.0005` development reference may be quoted as historical context, but **must not be rerun on validation as an alternate candidate or used to choose between strategies**.

## Validation data governance

Validation evidence must be acquired and sealed outcome-blind before any candidate evaluation.

Acquisition/sealing must:

- use OANDA PRACTICE historical GET only;
- request bid/ask/mid complete M5 candles;
- enforce the exact validation interval;
- prohibit rows at or after the reserved-final boundary;
- preserve raw immutable evidence and canonical SHA-256 identities;
- record explicit gap/calendar discrepancy ledgers;
- prohibit synthesis/interpolation/backfill;
- keep strategy outcome generation disabled during acquisition/sealing;
- require human review before the validation run is authorized.

## Interpretation constraints

A validation-supported result does not authorize live trading, capital allocation, broker writes, or final-test access. It would only justify a later human decision about whether to open the reserved final-test gate under a separately predeclared protocol.

A validation-rejected result closes this candidate absent a genuinely new, independently justified research hypothesis. Validation data may not be recycled for tuning.

An inconclusive/concentrated result may not be converted into a pass by dropping a pair, changing thresholds, changing sessions, or otherwise using validation outcomes for selection.

## Authority

- validation evidence acquisition: **FALSE pending separate authorization**;
- validation strategy outcomes: **FALSE**;
- validation candidate: fixed `0.0006` only;
- strategy selection: **FALSE**;
- parameter search: **FALSE**;
- reserved final test open: **FALSE**;
- broker writes: **FALSE**;
- portfolio sizing: **FALSE**;
- capital authority: **FALSE**;
- automatic promotion: **FALSE**;
- automatic merge: **FALSE**;
- human review required: **TRUE**.
