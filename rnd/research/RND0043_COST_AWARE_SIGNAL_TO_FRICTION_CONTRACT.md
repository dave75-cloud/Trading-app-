# RND-0043 — Cost-Aware Signal-to-Friction Development Study

Status: **PREDECLARED / DEVELOPMENT OUTCOMES CLOSED**

## Purpose

RND-0043 begins a fresh development-stage research line after the RND-0042 validation rejection. It does not attempt to rescue the rejected `0.0006` candidate and does not reuse validation outcomes for tuning.

The research question is whether the fixed M005 family fails primarily when available short-horizon movement is too small relative to executable bid/ask friction, and whether a dimensionless volatility-to-spread eligibility rule is a more transferable mechanism than an absolute volatility threshold.

This is a new hypothesis grounded in a pre-validation observation already established in RND-0035/RND-0038: the M005 family was materially sensitive to execution-cost drag, and positive gross behavior often deteriorated substantially after bid/ask costs.

RND-0043 is development-only hypothesis research. It cannot promote a strategy, open validation, or access reserved-final evidence.

## Data scope

Authorized research evidence is limited to the governed RND-0037 development assembly:

- start inclusive: `2015-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- timeframe: M5
- provider/environment: OANDA PRACTICE historical bid/ask/mid complete candles
- gap semantics: frozen gap-aware semantics

The following evidence is explicitly prohibited:

- the already-observed RND-0029 validation partition (`2020-12-31T19:15:00Z` to `2023-01-01T09:40:00Z`);
- the reserved-final partition beginning `2023-01-01T09:40:00Z`;
- any post-development outcome used to choose RND-0043 thresholds or rules.

The RND-0042 validation rejection may be cited only as the reason the prior candidate is closed. Its pair/year outcomes may not be used to design, select, or tune RND-0043 parameters.

## Fresh hypothesis

### Economic premise

A moving-average crossover signal is unlikely to survive executable bid/ask friction when the contemporaneous short-horizon price variation is small relative to the contemporaneous spread.

Absolute volatility cutoffs are pair- and regime-dependent. A dimensionless ratio should be more portable:

`signal_to_friction = sigma12_mid_return / relative_spread`

where:

- `sigma12_mid_return` is the frozen 12-observation population standard deviation (`ddof=0`) of genuine contiguous M5 mid returns available at the decision observation;
- `relative_spread = (ask_close - bid_close) / mid_close` at that same observation;
- both numerator and denominator use only contemporaneously available information;
- no future candle or future spread is permitted;
- a gap resets the rolling volatility state exactly as under frozen gap-aware semantics.

The primary hypothesis is:

> Restricting otherwise-fixed M005 entries to observations where short-horizon realized volatility is sufficiently large relative to current executable spread will improve net economics more coherently across pairs and years than the rejected absolute-volatility candidate family.

## Strategy base

RND-0043 returns to the frozen R000 M005 reference as the research base rather than continuing the rejected RND-0039/RND-0042 candidate.

Fixed base semantics:

- fast MA: 20
- slow MA: 50
- volatility window: 12
- volatility std: population (`ddof=0`)
- absolute volatility threshold: frozen R000 `0.0005`
- signal delay: 1 eligible observed bar
- minimum hold: 3 observed bars
- sessions: frozen M005 sessions
- bid/ask execution: frozen
- gap handling: frozen
- universe: all four symbols

The only additional experimental condition is the contemporaneous `signal_to_friction` eligibility gate.

## Predeclared development arms

RND-0043 uses a deliberately small coarse falsification ladder rather than an optimization grid.

- `F000`: no additional signal-to-friction gate (R000 reference)
- `F001`: require `signal_to_friction >= 3.0`
- `F002`: require `signal_to_friction >= 5.0`
- `F003`: require `signal_to_friction >= 8.0`

These values are fixed before outcomes are opened. They represent progressively stronger requirements that realized short-horizon movement materially exceed contemporaneous spread friction. No intermediate or additional ratio may be introduced after outcomes are visible under RND-0043.

No pair-specific ratio is permitted.

## Research status of the arms

The four arms are **development falsification arms**, not candidate strategies.

RND-0043 may determine whether the mechanism appears coherent, but may not promote one arm or open validation.

No arm may be described as an edge solely because it has the highest terminal equity.

## Primary falsification questions

RND-0043 must answer all of the following:

1. Does increasing the signal-to-friction requirement reduce execution-cost drag in a mechanically expected way?
2. Does any improvement appear in gross economics as well as net economics, or is it merely fewer trades paying fewer spreads?
3. Is the effect directionally coherent across the four symbols?
4. Is the effect distributed across development years rather than dependent on one year?
5. Does the effect survive leave-one-year-out and leave-one-pair-out diagnostics?
6. Does the effect improve stationary-bootstrap positive-total probability without creating extreme trade scarcity?
7. Does the four-pair concurrent reference improve without materially worsening drawdown?
8. Is any apparent benefit monotonic/coherent across `3.0`, `5.0`, `8.0`, or does it appear as an isolated best point consistent with overfitting noise?

## Predeclared interpretation rule

RND-0043 may classify the mechanism only as one of:

- `MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH`
- `MECHANISM_MIXED_OR_NON_MONOTONIC`
- `MECHANISM_FALSIFIED`

`MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH` requires all of:

1. at least two consecutive stricter arms improve four-pair realized completed-trade net-return sum relative to `F000`;
2. at least two consecutive stricter arms improve or preserve four-pair concurrent maximum drawdown relative to `F000`;
3. at least three of four pairs show non-worsening net-equity direction at the same stricter arm that provides the best coherent portfolio-level result;
4. the best coherent arm is not dependent on a single development year for more than 70% of positive aggregate net contribution;
5. leave-one-year-out and leave-one-pair-out diagnostics do not reverse the sign of the claimed aggregate improvement in a majority of exclusions;
6. no evidence, chronology, leakage, or gap-semantics violation occurs.

If the strongest apparent result is an isolated arm, pair-specific, single-year-dependent, or contradicted by leave-one-out diagnostics, classification must be `MECHANISM_MIXED_OR_NON_MONOTONIC`.

If stricter gates fail to improve aggregate net economics or materially worsen them, classification must be `MECHANISM_FALSIFIED`.

This classification is about the mechanism only. It does not select a deployable strategy.

## Required diagnostics

For each arm and symbol:

- row count and episode/gap counts;
- trade count;
- hit rate;
- gross equity index;
- net equity index;
- completed-trade net-return sum;
- max drawdown;
- execution-cost drag;
- median and distribution summary of the signal-to-friction ratio at eligible entries;
- rejected-entry count caused by the new gate.

Portfolio/dependence diagnostics:

- per-year and pair×year net contribution;
- leave-one-year-out;
- leave-one-pair-out;
- top 1% and top 5% absolute contribution shares;
- break-even additional round-trip cost by pair;
- frozen stationary bootstrap using the existing RND-0035 configuration family;
- observed four-pair equal-unit concurrent reference statistics.

## Guard against validation leakage

The previously observed 2021–2022 validation outcomes are scientifically consumed and may never be reused as a validation surface for RND-0043 or descendants.

If RND-0043 later supports a candidate mechanism, any new candidate must receive a **fresh untouched validation segment** under a separate contract. The preferred source is post-2025 historical evidence acquired and sealed after candidate identity is frozen.

The original reserved-final 2023–2024 partition remains sealed and cannot be used merely because the old validation partition has been consumed.

## Prohibited actions

RND-0043 may not:

- access or evaluate 2021–2022 validation outcomes for parameter choice;
- access reserved-final evidence;
- add ratios other than `3.0`, `5.0`, `8.0` after outcomes are visible;
- use pair-specific ratios;
- combine the ratio gate with new MA/session/delay/hold/latency rules;
- continue the absolute-volatility threshold search above or below the prior predeclared set;
- remove or reweight pairs based on prior validation performance;
- perform strategy selection for production;
- allocate capital;
- perform broker writes;
- open live authority;
- promote or merge automatically.

## Authority

- development outcomes: **FALSE pending separate human authorization**
- candidate strategy selection: **FALSE**
- validation access: **FALSE**
- reserved final test open: **FALSE**
- parameter expansion beyond predeclared arms: **FALSE**
- broker writes: **FALSE**
- portfolio sizing: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
