# RND-0060O — Activity-Admissibility Policy & Evidence Plan

## Status

FROZEN DESIGN / EVIDENCE PLAN — NO POLICY THRESHOLD SELECTED — NON-TRADING

## Purpose

RND-0060H established a strong development-only cross-sectional activity-state relationship. RND-0060L established that the same activity state predicts materially better subsequent movement relative to contemporaneous spread friction. RND-0060M defined the activity state as strategy-facing context rather than a directional signal, and RND-0060N implemented and verified a veto-only admissibility contract.

RND-0060O defines how any future activity-admissibility policy may be specified, calibrated, frozen, and independently confirmed without converting the RND-0060H/RND-0060L development discoveries directly into an overfit trading rule.

This task does not select a threshold, simulate trading, test P&L, open validation/final evidence, or access prospective Q003 outcomes.

## Core principle

Development evidence may establish the *form* of an admissibility policy and may support a predeclared calibration method, but development evidence alone cannot prove that the resulting policy deserves strategy-facing promotion.

Any policy parameter derived from development must be frozen before exposure to genuinely new confirmation evidence.

## Separation of functions

Three functions remain independent:

1. **Directional signal generation**
   - originates outside the activity layer;
   - supplies instrument, direction, and signal provenance;
   - cannot be created or reversed by the activity state.

2. **Activity admissibility**
   - receives the independent signal plus an activity-state measurement;
   - may return only `ADMIT`, `VETO`, or `DEFER`;
   - may not assign direction, position size, leverage, stop distance, target, portfolio weight, or capital.

3. **Risk / execution authority**
   - remains a separate downstream gate;
   - activity admissibility does not grant broker-write authority, capital authority, or promotion authority.

## Permitted future policy family

The first permissible policy family is **monotone, veto-only, one-dimensional activity admissibility**.

A future policy may use only the frozen RND-0060H cross-sectional dispersion state as its activity variable.

It may not combine additional market features, pair-specific conditions, alternate observation times, directional variables, or post-hoc transformations.

A future calibrated policy must be representable as one of:

- `ADMIT` when the frozen activity state satisfies one predeclared scalar condition; otherwise `VETO`; or
- `ADMIT`, `DEFER`, `VETO` under one predeclared ordered scalar partition of the same activity state.

RND-0060O does **not** choose which form will be used and does **not** choose any cut-point.

## Calibration rules

If a later task calibrates a policy from DEVELOPMENT_2015_2020, it must:

- declare the calibration objective before computing the cut-point;
- use exactly one calibration method;
- produce exactly one policy;
- prohibit threshold grids, candidate sweeps, pair-specific cut-points, year-specific cut-points, or repeated rescue attempts;
- record the derived cut-point and complete calibration provenance;
- freeze the resulting policy before opening confirmation evidence;
- treat that development-calibrated policy as a hypothesis, not as validated strategy logic.

Acceptable calibration methods must be rank/quantile or otherwise mechanically determined from the frozen activity state distribution and must be justified before outcomes are inspected.

Calibration must not optimize P&L, return, Sharpe ratio, drawdown, win rate, trade count, or any directional strategy outcome.

## Evidence hierarchy

### Layer A — Development discovery

Already consumed:

- DEVELOPMENT_2015_2020 informed RND-0060H and RND-0060L;
- it may support one later predeclared mechanical calibration;
- it must not be represented as fresh confirmation.

### Layer B — Historical validation 2021–2022

Unavailable for fresh confirmation.

The 2021–2022 validation interval was consumed by RND-0042. It must not be relabelled as untouched validation for the activity-admissibility policy.

### Layer C — Reserved final 2023–2024

Remains sealed.

RND-0060O does not authorize opening it. Any future request to use reserved-final evidence requires a separate explicit human gate and a justified project-level decision.

Reserved-final data must not be used merely because other evidence is inconvenient or slow to accumulate.

### Layer D — Fresh prospective activity evidence

This is the preferred confirmation path.

A future activity-policy confirmation stream should begin only after:

1. the policy form is fixed;
2. the calibration method is fixed;
3. any development-derived policy parameter is frozen;
4. the measurement implementation and evidence-acquisition protocol pass hostile verification;
5. a human explicitly authorizes prospective accumulation.

The prospective activity stream must have its own start timestamp, immutable tranche ledger, provenance receipts, minimum evidence horizon, and predeclared readout criteria.

## Separation from Q003 prospective validation

The Q003 prospective experiment remains independent and sealed.

The activity-policy stream must:

- use a separate task identifier, evidence ledger, report namespace, and readout decision;
- not inspect, condition on, or reference Q003 prospective signals, trades, returns, P&L, pair rankings, or equity;
- not alter Q003’s frozen candidate or accumulation protocol;
- not share a promotion decision with Q003.

The same raw market observations may be technically reusable only if their provenance is independently verified and the policy stream does not expose Q003 outcomes. Reuse of raw observations must never imply reuse of Q003 strategy results.

## Prospective confirmation question

The first prospective confirmation should remain non-trading.

It should ask whether the frozen activity policy distinguishes future market environments in the same direction as development evidence, using structural/economic measurements rather than strategy P&L.

Examples of permissible confirmation responses include:

- forward realized movement;
- movement-to-friction ratio;
- breadth/consistency across symbols;
- temporal consistency across prospective tranches.

The confirmation task must predeclare its exact primary response and pass/fail screen before opening outcomes.

## Promotion sequence

A positive prospective structural confirmation would still not authorize trading.

The minimum sequence is:

1. development discovery — complete;
2. admissibility architecture — complete;
3. contract verification — complete;
4. policy calibration/freeze — future task;
5. fresh prospective structural confirmation — future task;
6. human review of whether strategy-facing testing is justified;
7. only then, a separately frozen interaction test with an independent directional strategy;
8. shadow-only evaluation before any broker-write consideration;
9. separate risk/capital and execution gates.

## Failure semantics

If a frozen policy fails prospective structural confirmation:

- classify it as failed/inconclusive under the predeclared criteria;
- do not retune the cut-point on the same prospective evidence;
- do not invert the policy automatically;
- do not cherry-pick symbols or tranches;
- do not reuse the same confirmation period for a replacement policy and describe it as untouched.

A replacement hypothesis would require a new task and new evidence discipline.

## Governance

- task_id = RND-0060O
- policy_threshold_selected = FALSE
- strategy_candidate = FALSE
- trade_simulation = FALSE
- pnl = FALSE
- validation_open = FALSE
- final_test_open = FALSE
- reserved_final_access = FALSE
- q003_prospective_outcomes_open = FALSE
- broker_writes = FALSE
- capital_authority = FALSE
- automatic_promotion = FALSE
- automatic_merge = FALSE
- human_gate_required_for_prospective_start = TRUE
- human_gate_required_for_reserved_final = TRUE

## Recommended next task

The next implementation task should be **RND-0060P — Activity-Policy Calibration Protocol**.

RND-0060P should select exactly one mechanically defined calibration method, verify it with hostile fixtures, derive at most one development-based policy parameter, and freeze that policy without opening any fresh confirmation outcome.
