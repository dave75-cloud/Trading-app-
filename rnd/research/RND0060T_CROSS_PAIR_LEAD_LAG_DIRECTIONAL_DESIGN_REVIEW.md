# RND-0060T — Cross-Pair Lead–Lag Directional Design Review

## Status
FROZEN DESIGN REVIEW — NO OUTCOME OPENED

## Purpose
Test one independent directional mechanism that is structurally distinct from RND-0060A–K and from the RND-0060H activity-state family.

## Research question
At the fixed 11:30 UTC observation time, does a predeclared cross-pair USD lead signal contain reproducible information about another pair's subsequent 30-minute USD-oriented return?

## Independence constraints
- DEVELOPMENT_2015_2020 only.
- Independent of Q003.
- No 2021–2022 validation.
- No 2023–2024 reserved final.
- No RND-0060H/L activity state as a directional input.
- No revival, inversion, threshold rescue, pair dropping, or time/lookback/horizon search from RND-0060A–K.
- Exactly one declared trial.

## Frozen market representation
Symbols: AUDUSD, EURUSD, GBPUSD, USDJPY.
USD orientation:
- AUDUSD = -1
- EURUSD = -1
- GBPUSD = -1
- USDJPY = +1

Observation time: 11:30 UTC.
Timeframe: M5.
Lead lookback: 6 completed M5 bars (11:00 to 11:30 UTC).
Forward horizon: 6 completed M5 bars (11:35 to 12:00 UTC).

## Frozen lead–lag structure
Use two predeclared leader baskets and two predeclared targets:

1. European-leader basket = equal-weight mean of current USD-oriented 30-minute returns of EURUSD and GBPUSD.
   - Target A = AUDUSD next-30-minute USD-oriented close return.
   - Target B = USDJPY next-30-minute USD-oriented close return.

2. Pacific-leader basket = equal-weight mean of current USD-oriented 30-minute returns of AUDUSD and USDJPY.
   - Target C = EURUSD next-30-minute USD-oriented close return.
   - Target D = GBPUSD next-30-minute USD-oriented close return.

No pair-specific parameterization or post-hoc leader/target selection is permitted.

## Primary statistic
For each of the four frozen leader→target relationships, compute Spearman correlation between the leader basket and the target's next-30-minute USD-oriented close return.

Aggregate primary statistic = equal-weight mean of the four relationship-level Spearman correlations.

## Breadth diagnostics
- annual aggregate relationship statistic by year, 2015–2020;
- four relationship-level correlations;
- sign consistency across years and relationships.

## Predeclared classifier
Classification = `CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE_DETECTED` only if all are true:
1. aggregate primary statistic >= 0.05;
2. at least 4 of 6 annual aggregate statistics are positive;
3. at least 3 of 4 relationship-level correlations are positive;
4. integrity reconciliation passes.

Otherwise classification = `NO_REPRODUCIBLE_CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE`.

## Prohibitions
- no strategy simulation;
- no trades, P&L, equity, drawdown, win rate, sizing, or capital allocation;
- no threshold search;
- no alternate pair grouping;
- no alternate observation time;
- no alternate lookback or horizon;
- no sign inversion after outcome;
- no dropping a weak relationship after outcome;
- no Q003 references or prospective outcomes;
- no validation/final access;
- no broker writes or execution authority.

## Interpretation boundaries
A positive result establishes only a reproducible directional relationship worthy of a separate candidate-design review. It is not a strategy and does not authorize trading.

A negative result closes this exact lead–lag hypothesis without nearby rescue.
