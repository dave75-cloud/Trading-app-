# RND-0060L — Economic Utility of Cross-Sectional Activity State

## Status

FROZEN DESIGN REVIEW — DEVELOPMENT ONLY — NON-TRADING

## Purpose

RND-0060H established a robust development-only relationship between cross-sectional USD dispersion at 11:30 UTC and subsequent 30-minute market activity/magnitude. RND-0060J and RND-0060K failed to establish reproducible directional information from two separately predeclared directional mechanisms.

RND-0060L therefore closes the immediate directional-search sequence and asks a different question:

> Does the RND-0060H cross-sectional activity state identify periods in which subsequent market movement is economically large relative to contemporaneous transaction friction?

This is an economic-utility / market-state question, not a trading-strategy test.

## Research hypothesis

At 11:30 UTC, higher cross-sectional dispersion among the four USD-oriented 30-minute returns is associated with a higher subsequent 30-minute movement-to-friction ratio across the same four-symbol market set.

## Fixed market-state variable

Use the exact RND-0060H state definition without modification:

- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY
- timeframe: M5
- observation time: 11:30 UTC
- lookback: 6 M5 intervals / 30 minutes, 11:00–11:30
- USD orientation:
  - AUDUSD = -1
  - EURUSD = -1
  - GBPUSD = -1
  - USDJPY = +1
- state: population standard deviation of the four USD-oriented 30-minute returns

No alternate time, lookback, symbol subset, weighting, or transformed dispersion state may be substituted after outcomes are seen.

## Economic-adequacy response

For each eligible symbol-day at 11:30 UTC:

1. contemporaneous relative spread = (ask_close - bid_close) / mid_close at 11:30 UTC;
2. forward 30-minute realised movement = (maximum mid high - minimum mid low) over the next 6 completed M5 bars, divided by the 11:30 mid close;
3. movement-to-friction ratio = forward relative realised movement / contemporaneous relative spread.

The market-wide primary response for each eligible day is the equal-weight mean of the four symbol movement-to-friction ratios.

The per-symbol movement-to-friction ratios are retained for breadth diagnostics.

This ratio is descriptive of economic opportunity relative to friction. It is not a trade-entry rule, profit estimate, expected return, or sizing rule.

## Structural question

Primary question:

> Is higher 11:30 cross-sectional dispersion monotonically associated with a higher market-wide forward movement-to-friction ratio?

Secondary diagnostics:

- annual consistency across 2015–2020;
- per-symbol consistency across all four currency pairs;
- top-versus-bottom dispersion quartile difference in mean movement-to-friction ratio;
- integrity reconciliation.

## Predeclared classifier

All criteria must pass for `ACTIVITY_STATE_ECONOMIC_UTILITY_DETECTED`:

1. aggregate Spearman correlation between dispersion state and market-wide movement-to-friction ratio >= 0.05;
2. at least 4 of 6 annual Spearman correlations are positive;
3. at least 3 of 4 symbol-level Spearman correlations are positive;
4. mean primary response in the top dispersion quartile is greater than in the bottom dispersion quartile;
5. integrity reconciliation passes.

Otherwise classify `NO_REPRODUCIBLE_ACTIVITY_STATE_ECONOMIC_UTILITY`.

The quartile comparison is diagnostic only. It does not create a threshold or admissibility rule.

## Dataset and scope

- DEVELOPMENT_2015_2020 only.
- 24 pair-years structurally verified through the existing RND-0037 development assembly.
- validation 2021–2022 remains closed and consumed.
- reserved final 2023–2024 remains closed.
- no prospective Q003 evidence may be inspected or referenced.

## Explicit prohibitions

RND-0060L must not:

- introduce a trading direction;
- create a long/short signal;
- create a threshold such as ratio >= N;
- reuse, tune, or compare any previously frozen strategy threshold;
- select currency pairs post hoc;
- alter the 11:30 observation time;
- alter the 30-minute lookback or forward horizon;
- optimise spread definitions, weights, or friction multipliers;
- simulate trades, P&L, equity, drawdown, win rate, or position sizing;
- open validation or reserved-final evidence;
- access prospective candidate outcomes;
- grant broker-write, capital, promotion, or merge authority.

## Relationship to prior research

RND-0060L does not attempt to rescue RND-0060J or RND-0060K and does not invert either result.

It also does not construct a strategy from RND-0060H. It tests whether the established activity state has economically meaningful information about the scale of future movement relative to contemporaneous friction.

Any later use of this state as a filter, sizing input, execution-control input, or strategy-admissibility condition would require a separate predeclared task and human review.

## Governance

- independent research firewall remains active;
- development_only = TRUE;
- declared_trial_count = 1;
- parameter_search = FALSE;
- threshold_search = FALSE;
- trade_simulation = FALSE;
- pnl = FALSE;
- strategy_candidate = FALSE;
- validation_open = FALSE;
- final_test_open = FALSE;
- reserved_final_access = FALSE;
- prospective_candidate_outcomes_open = FALSE;
- broker_writes = FALSE;
- capital_authority = FALSE;
- automatic_promotion = FALSE;
- automatic_merge = FALSE.

## Advancement rule

A positive result may justify a later, separately governed design review into activity-aware execution or risk controls.

A negative result closes this specific economic-adequacy hypothesis without nearby threshold, timing, symbol, horizon, spread-multiplier, or weighting rescue.
