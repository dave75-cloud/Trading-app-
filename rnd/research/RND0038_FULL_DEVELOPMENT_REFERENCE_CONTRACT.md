# RND-0038 — Full Development R000 Reference Completion

Status: **PREDECLARED / OUTCOMES NOT YET AUTHORIZED**

## Purpose

RND-0038 extends the already-fixed R000 M005 reference from governed 2015–2019 development evidence to the now-complete governed 2015–2020 development partition. It is a reference-completion and falsification task only. It is not a strategy-selection task and does not authorize the quarantined higher-volatility follow-up hypothesis.

## Development scope

- start inclusive: `2015-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- timeframe: M5
- evidence basis: RND-0037 complete 24/24 pair-year structural assembly

Validation begins exactly at `2020-12-31T19:15:00Z` and remains closed. Reserved-final evidence remains closed.

## Fixed reference

R000 is unchanged from RND-0035:

- fast MA 20
- slow MA 50
- volatility window 12
- population standard deviation (`ddof=0`)
- volatility threshold `0.0005`
- signal delay 1 eligible observed bar
- minimum hold 3 observed bars
- sessions unchanged from frozen M005
- bid/ask execution and gap semantics unchanged from RND-0034/RND-0035

No parameter search, threshold extension, session tuning, Champion reconstruction, or pair-specific modification is permitted.

## Required outputs

RND-0038, if separately authorized, must report:

1. per-pair R000 outcomes over the full 2015–2020 development interval;
2. per-year and pair×year concentration diagnostics including 2020;
3. cost bridge and additional round-trip break-even diagnostics;
4. per-pair stationary bootstrap using the same frozen G configuration family;
5. observed four-pair equal-unit concurrent reference aggregation;
6. explicit 2020-only contribution diagnostics;
7. evidence identity proof for all 24 pair-years;
8. confirmation that validation/final remain closed.

## Interpretation constraints

- R000 may be rejected as a reference edge if the full-development evidence remains adverse.
- No RND-0035 variant may be promoted because of this task.
- A016 / `.0006` remains an outcome-derived quarantined observation, not the new reference.
- No higher-volatility follow-up may run under RND-0038.
- Results may motivate a separately predeclared RND-0039 hypothesis-falsification design only after human review.

## Authority

- R000 development outcomes: **FALSE pending separate authorization**
- higher-volatility outcomes: **FALSE**
- strategy selection: **FALSE**
- validation open: **FALSE**
- final test open: **FALSE**
- broker writes: **FALSE**
- portfolio sizing: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
