# RND-0060P — Activity-Policy Calibration Protocol

## Status

FROZEN DESIGN / PRE-CALIBRATION

## Purpose

Define exactly one mechanical calibration procedure for turning the already-frozen RND-0060H cross-sectional activity state into a one-dimensional veto-only admissibility policy under the RND-0060M/RND-0060N architecture.

RND-0060P is a calibration protocol, not a trading-strategy test and not confirmation evidence.

## Upstream basis

RND-0060H established that the frozen cross-sectional USD-dispersion state has reproducible association with subsequent market activity on DEVELOPMENT_2015_2020.

RND-0060L established that higher values of that same frozen activity state are associated with higher subsequent market-wide movement relative to contemporaneous spread friction on DEVELOPMENT_2015_2020.

RND-0060M restricted the activity state to an execution/admissibility context role. It cannot generate or reverse direction.

RND-0060N implemented and hostile-tested the generic ADMIT / VETO / DEFER contract, preserving strict separation between directional signal generation, activity admissibility, and risk/execution authority.

## Calibration objective

Produce at most one frozen scalar cut-point from DEVELOPMENT_2015_2020 for use in a later, separately governed prospective confirmation stream.

The calibration must not optimize any trading or economic outcome.

## Frozen state definition

The calibration variable is exactly the RND-0060H state:

- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY;
- timeframe: M5;
- observation time: 11:30 UTC;
- lookback: six completed M5 intervals, 11:00 through 11:30 UTC;
- orientation: AUDUSD=-1, EURUSD=-1, GBPUSD=-1, USDJPY=+1;
- per-symbol input: USD-oriented 30-minute return from 11:00 to 11:30;
- state: population standard deviation of the four oriented returns;
- eligible market day requires the exact four-symbol observation set and all upstream integrity rules inherited from RND-0060H/RND-0060L.

No alternate time, lookback, symbol set, orientation, dispersion statistic, or state transform is permitted in RND-0060P.

## Single permitted calibration rule

The sole permitted calibration rule is:

> `activity_cutpoint = empirical median of all eligible RND-0060H activity-state observations in DEVELOPMENT_2015_2020.`

The empirical median must be calculated deterministically from the complete eligible pooled development-state sample after all frozen integrity exclusions. No weighting by year, symbol, spread, return, strategy result, or economic outcome is permitted.

If the eligible observation count is odd, the median is the middle sorted value.

If the eligible observation count is even, the median is the arithmetic mean of the two central sorted values.

No quantile other than the median may be tested. No nearby threshold may be inspected. No threshold grid, optimizer, objective function, score, or sensitivity sweep is permitted.

## Frozen policy semantics

Once the cut-point is calibrated, the candidate policy form is:

- `ADMIT` when `activity_state >= activity_cutpoint`;
- `VETO` when `activity_state < activity_cutpoint`;
- `DEFER` only when the activity decision cannot be evaluated because required state/provenance/integrity inputs are unavailable or invalid under the RND-0060N contract.

The equality convention is frozen as `ADMIT`.

The activity layer remains veto-only. It may not:

- create a directional signal;
- change signal sign;
- choose instrument;
- set or increase position size;
- alter stop/target/holding-period logic;
- convert VETO into an opposite-side trade;
- use the calibrated state as a standalone entry signal;
- grant execution, broker-write, promotion, or capital authority.

## Why the median

The median is selected ex ante because it is:

1. one-dimensional and monotone;
2. deterministic and reproducible;
3. invariant to the scale units of the state;
4. robust to extreme dispersion observations;
5. independent of downstream trading or economic outcomes;
6. incapable of becoming a threshold-search family within this task;
7. suitable for a simple prospective high-activity versus lower-activity confirmation design.

This rationale is architectural. The median is not claimed to be economically optimal.

## Authorized evidence

Calibration may use only DEVELOPMENT_2015_2020, with the same historical evidence identities and development boundary already governed by RND-0037 and the RND-0060H/RND-0060L studies.

The development sample is calibration evidence only. It must never be described as fresh confirmation of the calibrated policy.

## Prohibited evidence

RND-0060P must not access or use:

- consumed 2021-2022 validation as untouched evidence;
- reserved-final 2023-2024 evidence;
- Q003 prospective outcomes;
- any post-freeze prospective activity-policy outcomes;
- broker or account performance data for policy calibration.

## Pre-calibration implementation gate

Before the development median is materialized, the implementation must pass hostile fixtures covering at least:

1. exact median for an odd-length state sample;
2. exact median for an even-length state sample;
3. deterministic ordering independence;
4. duplicate-value handling;
5. equality-at-cutpoint => ADMIT;
6. below-cutpoint => VETO;
7. above-cutpoint => ADMIT;
8. missing state => DEFER/fail closed;
9. non-finite state rejection;
10. non-finite cut-point rejection;
11. empty calibration sample rejection;
12. no alternate quantile parameter accepted;
13. no objective/outcome input accepted by calibration API;
14. no signal direction, size, P&L, validation, broker, or capital authority in output.

The hostile fixture suite must be green before the development-state sample is used to compute the cut-point.

## Calibration output

A successful RND-0060P calibration may output only:

- task/contract identity;
- eligible development observation count;
- integrity/exclusion counts required for reconciliation;
- the single empirical median activity cut-point;
- deterministic policy semantics (`>=` ADMIT, `<` VETO);
- evidence identities / provenance;
- governance flags confirming all prohibited authorities remain closed;
- report SHA-256 / receipt identity.

It must not output strategy trades, P&L, equity, drawdown, win rate, directional hit rate, pair ranking, or threshold comparisons.

## Calibration classifier

RND-0060P has no economic success classifier.

The only permitted completion states are:

- `CALIBRATION_COMPLETE_POLICY_FROZEN` — implementation gates pass, evidence reconciles, and exactly one finite median cut-point is produced; or
- `CALIBRATION_PROTOCOL_REJECTED` — integrity, provenance, deterministic-calibration, or contract requirements fail.

A completed calibration does not mean the policy is validated or useful.

## Required next stage after successful calibration

A successful RND-0060P result must be frozen before any fresh confirmation evidence is opened.

The preferred next stage is a separately governed prospective activity-policy evidence stream, independent of Q003, testing the frozen state and frozen median policy without threshold changes.

Any future strategy-facing use requires separate evidence and human approval.

## Governance invariants

Throughout RND-0060P:

- `parameter_search = FALSE`
- `threshold_search = FALSE`
- `trade_simulation = FALSE`
- `pnl = FALSE`
- `strategy_candidate = FALSE`
- `validation_open = FALSE`
- `final_test_open = FALSE`
- `reserved_final_access = FALSE`
- `prospective_candidate_outcomes_open = FALSE`
- `broker_writes = FALSE`
- `capital_authority = FALSE`
- `automatic_promotion = FALSE`
- `automatic_merge = FALSE`

Human approval remains required for every later evidence-opening, strategy-facing, promotion, broker-write, or capital-authority step.
