# RND-0060N — Activity-Admissibility Contract

## Status

FROZEN CONTRACT — DEVELOPMENT/ARCHITECTURE ONLY — NON-TRADING

## Purpose

RND-0060H detected a reproducible cross-sectional activity state. RND-0060L further showed that higher activity state is associated with a stronger forward movement-to-friction environment. RND-0060M therefore selected a veto-only architecture for any future strategy-facing use of the activity state.

RND-0060N turns that architecture into a machine-checkable generic contract without selecting an activity threshold, directional strategy, position size, or execution rule.

## Separation of roles

Three layers remain separate:

1. **Directional signal source**
   - external to the activity layer;
   - supplies symbol and direction;
   - may supply metadata identifying its own provenance;
   - the activity layer may not create or reverse it.

2. **Activity admissibility layer**
   - consumes an already-existing directional signal plus an externally supplied activity-policy decision;
   - may return only `ADMIT`, `VETO`, or `DEFER`;
   - may not change symbol, direction, side, quantity, leverage, stop, target, or holding period;
   - may not turn a flat/no-signal state into exposure.

3. **Risk/execution authority**
   - remains downstream and separate;
   - even an `ADMIT` decision grants no broker-write, capital, promotion, or execution authority.

## Generic contract inputs

The activity-admissibility kernel accepts:

- `symbol`: one of AUDUSD, EURUSD, GBPUSD, USDJPY;
- `direction`: exactly `-1`, `0`, or `+1`;
- `activity_state`: positive finite descriptive value;
- `activity_policy_decision`: exactly one of `ADMIT`, `VETO`, `DEFER`;
- `direction_source_id`: non-empty provenance identifier independent of RND-0060H/L;
- optional opaque signal metadata that must be passed through unchanged.

RND-0060N does **not** decide how `activity_policy_decision` is generated. In particular it does not select, tune, infer, or encode an activity threshold.

## Veto-only semantics

- If `direction == 0`, output exposure intent remains zero regardless of policy decision.
- `ADMIT` may preserve an existing non-zero direction unchanged.
- `VETO` suppresses the existing non-zero direction to zero exposure intent.
- `DEFER` suppresses immediate exposure intent to zero and records that the directional intent is deferred, not reversed.
- No activity decision may invert `+1` to `-1` or vice versa.
- No activity decision may increase exposure, assign quantity, select a pair, or synthesize a trade.

## Required output

The kernel returns a pure decision record containing:

- original symbol;
- original direction;
- original direction source ID;
- activity state;
- activity policy decision;
- `effective_direction_now`;
- `deferred_direction` only for `DEFER` with a non-zero input direction;
- unchanged signal metadata;
- fixed governance flags showing no trading or authority expansion.

## Explicit prohibitions

RND-0060N must not:

- choose an activity threshold;
- derive direction from activity state;
- reuse Q003 rules or prospective outcomes;
- reference consumed 2021–2022 validation outcomes;
- open reserved final 2023–2024;
- simulate trades, P&L, equity, drawdown, win rate, or sizing;
- assign quantity, leverage, stop, target, or holding period;
- route orders;
- enable broker writes;
- enable capital authority;
- create a strategy candidate;
- automatically promote or merge.

## Advancement rule

RND-0060N is complete only when the pure contract kernel and hostile fixtures demonstrate that:

- no-signal cannot become exposure;
- activity cannot create or reverse direction;
- `ADMIT` preserves an independent direction exactly;
- `VETO` can only suppress;
- `DEFER` can only postpone;
- unsupported symbols, malformed directions, malformed policy decisions, invalid activity values, and missing provenance are rejected;
- all governance flags remain closed.

Only after this contract is verified may a separate human-approved task define how an activity policy is obtained. Any such policy must be predeclared and independently governed.
