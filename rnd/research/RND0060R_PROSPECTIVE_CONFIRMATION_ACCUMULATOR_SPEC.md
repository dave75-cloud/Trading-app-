# RND-0060R — Prospective Confirmation Accumulator & Provenance Guard

## Purpose
Implement a non-trading prospective evidence accumulator for the frozen RND-0060P activity-admissibility policy.

This task does **not** evaluate direction, trades, P&L, equity, drawdown, sizing, broker execution, Q003 outcomes, validation 2021–2022, or reserved-final 2023–2024 evidence.

## Frozen upstream policy
- Source calibration task: RND-0060P.
- Activity state: exact RND-0060H cross-sectional dispersion state.
- Frozen cut-point: `0.0003990789273159821`.
- `activity_state >= cutpoint` => `ADMIT`.
- `activity_state < cutpoint` => `VETO`.
- missing/unavailable state => `DEFER`.
- The policy is veto-only and cannot generate, reverse, resize, or otherwise alter directional exposure.

## Prospective evidence contract
An eligible prospective observation is a complete record for one observation timestamp containing:
- exact UTC timestamp;
- provenance timestamp showing when the observation became available to the accumulator;
- four-symbol activity-state inputs needed by the frozen RND-0060H definition;
- frozen activity state;
- frozen ADMIT/VETO/DEFER classification;
- contemporaneous spread inputs;
- next-30-minute movement-to-friction outcome for each symbol and equal-weight market-wide response;
- explicit source/tranche identity.

## Provenance guard
The accumulator must reject or fail closed on:
- observations timestamped before the sealed prospective start;
- observations whose `available_at_utc` precedes the end of the required forward 30-minute window;
- duplicate observation timestamps;
- out-of-order observations;
- malformed/non-finite values;
- policy cut-point mismatch;
- policy-version mismatch;
- source marked as historical backfill, validation 2021–2022, reserved final 2023–2024, or Q003 prospective outcome evidence;
- any attempt to overwrite an already-recorded observation.

Historical data may be used only in fixtures. No backfilled market observation may count toward prospective evidence.

## Readout lock
Before BOTH conditions are satisfied, economic group comparisons remain locked:
1. at least 180 calendar days have elapsed from the sealed prospective start timestamp; and
2. at least 100 eligible non-DEFER observations have accumulated.

Before readout eligibility, status may expose only structural/provenance counts and dates, not ADMIT-vs-VETO economic outcome summaries.

## Future readout criteria inherited from RND-0060Q
A later governed readout may compare ADMIT versus VETO only after the lock opens. Positive confirmation requires the frozen RND-0060Q criteria, including:
- market-wide mean movement-to-friction: ADMIT > VETO;
- market-wide median movement-to-friction: ADMIT > VETO;
- at least 3 of 4 symbols show ADMIT > VETO on the frozen symbol-level comparison;
- integrity/provenance reconciliation passes.

No threshold rescue, pair dropping, alternate horizon, alternate observation time, alternate spread definition, or policy change is allowed after prospective accumulation begins.

## Governance
- `trade_simulation = false`
- `pnl = false`
- `strategy_interaction = false`
- `validation_open = false`
- `final_test_open = false`
- `reserved_final_access = false`
- `q003_prospective_outcomes_open = false`
- `broker_writes = false`
- `capital_authority = false`
- `automatic_promotion = false`

## Exit from RND-0060R
RND-0060R completes when:
1. the accumulator/provenance kernel is implemented;
2. hostile fixtures pass;
3. a pre-start verification receipt is sealed;
4. only then may a human-approved prospective start timestamp be recorded in the next governed step.
