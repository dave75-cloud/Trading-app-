# RND-0047 — Prospective Fresh Validation Evidence Contract

Status: **PREDECLARED / ACQUISITION INFRASTRUCTURE ONLY / CANDIDATE OUTCOMES CLOSED**

## Purpose

RND-0047 creates a genuinely fresh validation evidence stream for the frozen Q003 candidate approved in RND-0046.

This task is deliberately separated from candidate evaluation. RND-0047 may define, acquire, verify, and seal fresh market evidence, but it has no authority to evaluate Q003 profitability, modify the candidate, open the reserved-final 2023–2024 set, or promote the strategy.

## Frozen candidate identity

Candidate: `Q003`

Canonical candidate fingerprint:

`25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`

Any mismatch to that fingerprint is fail-closed.

Frozen mechanics include:

- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY;
- timeframe: M5;
- fast MA 20;
- slow MA 50;
- volatility window 12, population standard deviation (`ddof=0`);
- ratio-only entry eligibility `signal_to_friction >= 8.0`;
- no absolute-volatility floor;
- one-observation signal delay;
- minimum hold three observed bars;
- frozen UTC sessions;
- bid/ask execution and mid-price signal semantics;
- frozen gap/reset semantics.

No rule, pair, threshold, session, delay, hold, weighting, or execution assumption may change inside RND-0047.

## Definition of fresh evidence

Fresh validation evidence must be prospectively generated after the human candidate freeze.

The first admissible candle timestamp is:

`2026-10-05T07:25:00Z` inclusive

This is the first complete M5 boundary after the human Q003 freeze decision at approximately 2026-10-05 17:23 Australia/Brisbane time.

The following are **not** admissible as fresh validation evidence for Q003:

- consumed 2021–2022 validation evidence;
- reserved-final 2023–2024 evidence;
- 2025 evidence;
- 2026 evidence before `2026-10-05T07:25:00Z`;
- any synthetic, interpolated, backfilled, or manually repaired market observations.

This strict boundary prevents retrospective selection of an already-existing historical interval after the candidate was frozen.

## Provider and evidence format

Provider: OANDA PRACTICE historical candle endpoint only.

Required candle representation:

- M5;
- complete candles only;
- bid, ask, and mid close prices preserved;
- source timestamps preserved in UTC;
- no synthetic candles;
- duplicate timestamps prohibited;
- out-of-order timestamps prohibited;
- missing intervals preserved as gaps rather than filled.

Acquisition is evidence collection only. It grants no broker order authority.

## Evidence accumulation protocol

RND-0047 does not use an outcome-dependent stopping rule.

The evidence stream remains open prospectively from `2026-10-05T07:25:00Z` onward and may be appended only with newly completed M5 candles.

A later, separate validation-evaluation task must predeclare its evaluation horizon or minimum evidence rule before candidate outcomes are opened.

RND-0047 itself does **not** decide when enough fresh evidence exists to judge Q003.

## Sealing requirements

Each acquisition tranche must produce an immutable manifest containing, at minimum:

- candidate fingerprint;
- provider and environment (`OANDA PRACTICE`);
- symbol;
- requested start/end boundaries;
- actual first/last candle timestamps;
- row count;
- complete-candle count;
- duplicate/out-of-order checks;
- gap count and gap intervals;
- file SHA-256;
- acquisition timestamp;
- explicit statements that strategy evaluation and reserved-final access were false.

Cumulative seals must be append-only in evidence identity: prior sealed bytes may not be rewritten to improve continuity or replace missing observations.

## Fail-closed conditions

Acquisition or sealing must fail if any of the following occurs:

1. candidate fingerprint mismatch;
2. requested start precedes `2026-10-05T07:25:00Z`;
3. 2023–2024 reserved-final evidence is referenced as validation input;
4. incomplete candles are accepted;
5. duplicate or out-of-order timestamps occur;
6. bid/mid/ask ordering is invalid;
7. synthetic/backfilled/interpolated candles are introduced;
8. a write/order broker endpoint is invoked;
9. strategy evaluation is attempted inside RND-0047;
10. sealed historical bytes are silently replaced.

## Governance

- candidate frozen: **TRUE**
- fresh-evidence acquisition design: **TRUE**
- acquisition implementation/testing: **TRUE**
- actual market-data acquisition: **FALSE pending separate human gate after implementation tests**
- candidate outcome evaluation: **FALSE**
- 2021–2022 validation reuse: **FALSE**
- reserved-final 2023–2024 access: **FALSE**
- 2025/pre-freeze-2026 validation use: **FALSE**
- candidate modification: **FALSE**
- pair dropping: **FALSE**
- pair weighting: **FALSE**
- broker writes/order endpoints: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
