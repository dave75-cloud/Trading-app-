# RND-0060Q — Independent Confirmation Protocol

## Status
FROZEN DESIGN / NO OUTCOME OPENED

## Purpose
Independently confirm whether the frozen RND-0060P activity-admissibility policy continues to identify future market states with superior movement-to-friction conditions, without reusing development evidence as confirmation and without interacting with Q003 strategy outcomes.

## Frozen upstream inputs
- RND-0060H activity state: cross-sectional population standard deviation of the four USD-oriented 30-minute returns observed at 11:30 UTC.
- Symbols: AUDUSD, EURUSD, GBPUSD, USDJPY.
- Timeframe: M5.
- Observation time: 11:30 UTC.
- Lookback: 6 completed M5 intervals / 30 minutes.
- USD orientation: AUDUSD=-1, EURUSD=-1, GBPUSD=-1, USDJPY=+1.
- RND-0060P frozen activity cut-point: `0.0003990789273159821`.
- Policy mapping:
  - activity state >= cut-point -> ADMIT
  - activity state < cut-point -> VETO
  - unavailable/incomplete required state -> DEFER

The cut-point is immutable for RND-0060Q. No threshold search, percentile substitution, pair-specific threshold, time change, lookback change, or horizon change is permitted.

## Confirmation evidence source
RND-0060Q uses a new prospective evidence stream only.

Rules:
1. Prospective eligibility begins only after this protocol is committed and the prospective-start receipt is sealed.
2. No observation with timestamp earlier than that prospective start may count.
3. 2015-2020 is development/calibration evidence only and cannot count as confirmation.
4. 2021-2022 remains consumed prior validation evidence and is prohibited.
5. 2023-2024 reserved final evidence remains sealed and prohibited.
6. Q003 prospective outcomes, signals, trades, returns, P&L, equity, drawdown, or pair rankings are prohibited inputs.
7. Raw market observations may be acquired from the same broker/data provider infrastructure only if RND-0060Q evidence is separately identified, hashed, ledgered, and evaluated under this protocol.

## Frozen measurement
For each eligible prospective market day:

### Activity state
Compute the exact frozen RND-0060H cross-sectional activity state at 11:30 UTC.

### Contemporaneous friction
For each symbol at 11:30 UTC:
`relative_spread = (ask_close - bid_close) / mid_close`

### Forward movement
For each symbol over the next 6 completed M5 bars (11:35 through 12:00 UTC):
`forward_relative_movement = (max(mid_high) - min(mid_low)) / 11:30 mid_close`

### Movement-to-friction ratio
For each symbol:
`movement_to_friction = forward_relative_movement / relative_spread`

Market-wide response:
`equal-weight mean of the four symbol movement-to-friction ratios`

No direction, trade simulation, P&L, sizing, or execution is part of this measurement.

## Frozen policy comparison
Each eligible day is classified using the already-frozen cut-point only:
- ADMIT if activity_state >= 0.0003990789273159821
- VETO if activity_state < 0.0003990789273159821
- DEFER if required state cannot be validly computed

DEFER observations are structural exclusions and cannot be reassigned after observing outcomes.

## Minimum evidence horizon
A confirmation readout is not eligible until BOTH are satisfied:
1. at least 180 calendar days have elapsed from the sealed prospective start; and
2. at least 100 eligible non-DEFER market-day observations have accumulated.

Until both conditions are met, status is `ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE` and economic readout is prohibited.

## Predeclared confirmation criteria
At the first eligible readout, classify as `ACTIVITY_POLICY_INDEPENDENTLY_CONFIRMED` only if ALL are true:

1. `mean_market_wide_movement_to_friction_ADMIT > mean_market_wide_movement_to_friction_VETO`
2. `median_market_wide_movement_to_friction_ADMIT > median_market_wide_movement_to_friction_VETO`
3. at least 3 of 4 symbols have higher mean movement-to-friction under ADMIT than under VETO
4. both ADMIT and VETO contain at least 20 eligible observations
5. integrity/provenance reconciliation passes with no pre-start observations, no prohibited historical partitions, no Q003 outcome inputs, and no duplicate market days

If structural evidence is insufficient or corrupted, classification is `INCONCLUSIVE_EXTEND_CONFIRMATION`.
If structurally valid but any economic criterion 1-4 fails, classification is `ACTIVITY_POLICY_NOT_INDEPENDENTLY_CONFIRMED`.

No nearby rescue threshold, sign inversion, alternative quantile, pair dropping, horizon change, or post-hoc subgroup is permitted after readout.

## Separation from strategy validation
A positive RND-0060Q result does NOT establish trading profitability and does NOT authorize the activity policy to filter any live or shadow strategy automatically.

A positive result may justify a later, separately governed strategy-interaction design review in which an independently specified directional strategy is compared with and without the veto-only activity layer.

A negative result closes the frozen policy as an independently unconfirmed activity-admissibility rule unless a future task begins from a genuinely new hypothesis rather than a rescue search.

## Governance state
- threshold_search: FALSE
- parameter_search: FALSE
- strategy_interaction: FALSE
- trade_simulation: FALSE
- pnl: FALSE
- validation_2021_2022_open: FALSE
- reserved_final_2023_2024_open: FALSE
- q003_prospective_outcomes_open: FALSE
- broker_writes: FALSE
- capital_authority: FALSE
- automatic_promotion: FALSE
- automatic_merge: FALSE

## Next permitted step
Implement and hostile-test the prospective confirmation accumulator and provenance guard before sealing the prospective start timestamp. No economic outcome may be opened during that implementation stage.
