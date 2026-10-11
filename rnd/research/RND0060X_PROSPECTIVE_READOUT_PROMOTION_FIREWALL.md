# RND-0060X — Prospective Evidence Readout Gate & Promotion Firewall

## Status
FROZEN GOVERNANCE DESIGN — NO OUTCOME OPENED / NO PROMOTION AUTHORITY

## Purpose
Define a machine-enforced firewall governing when prospective evidence may become eligible for human readout and preventing any prospective result from becoming automatic strategy promotion, capital authority, broker-write authority, or live execution authority.

RND-0060X does not inspect economic outcomes. It governs eligibility, separation, integrity, and human gates only.

## Prospective streams covered

### Stream A — Q003 prospective strategy validation
Authoritative candidate: frozen Q003 ratio-only candidate.

Prospective start: 2026-10-05T07:25:00Z.
Minimum time horizon: 180 calendar days.
Earliest time-based readout eligibility: 2027-04-03T07:25:00Z.

Until all Q003 structural and horizon conditions are met, status must remain:
`ACCUMULATING_PROSPECTIVE_VALIDATION_EVIDENCE`.

Economic outcome fields remain inaccessible before the readout gate opens.

### Stream B — RND-0060Q/R activity-policy independent confirmation
Frozen policy cutpoint: 0.0003990789273159821.
Prospective start: 2026-10-09T02:33:50Z.
Minimum readout conditions require BOTH:
1. at least 180 calendar days from prospective start; and
2. at least 100 eligible non-DEFER market-day observations.

Earliest time-based eligibility: 2027-04-07T02:33:50Z.

Until BOTH conditions are met, status must remain:
`ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE`.

Economic ADMIT/VETO comparison fields remain inaccessible before the readout gate opens.

## Absolute separation rule
Q003 and RND-0060Q/R are independent prospective programs.

They may share provider infrastructure only where raw market observations are independently identified, hashed, ledgered, and evaluated.

The following are prohibited:
- using Q003 strategy outcomes as inputs to RND-0060Q/R;
- using RND-0060Q/R economic outcomes to rescue, tune, reinterpret, or rank Q003;
- combining observations to satisfy either stream's minimum sample requirement;
- using one stream's success to waive the other stream's readout conditions;
- shared outcome-derived thresholds;
- joint optimization;
- post-hoc pair selection based on either stream.

## Generic machine readout gate
Each stream must expose a structural readiness object containing only non-economic fields before readout eligibility.

Required fields:
- `stream_id`;
- `prospective_start_utc`;
- `evaluation_time_utc`;
- `minimum_horizon_days`;
- `elapsed_calendar_days`;
- `minimum_observation_count` where applicable;
- `eligible_observation_count` where applicable;
- `provenance_integrity_pass`;
- `duplicate_check_pass`;
- `chronology_check_pass`;
- `pre_start_contamination_count`;
- `prohibited_partition_access_count`;
- `cross_stream_outcome_contamination`;
- `economic_fields_open`;
- `human_readout_gate`;
- `promotion_authority`;
- `broker_write_authority`;
- `capital_authority`.

Before eligibility:
- `economic_fields_open=FALSE`;
- `human_readout_gate=FALSE`;
- `promotion_authority=FALSE`;
- `broker_write_authority=FALSE`;
- `capital_authority=FALSE`.

## Q003 structural gate
Q003 may become `READOUT_ELIGIBLE_PENDING_HUMAN_GATE` only if all are true:
1. evaluation time is not earlier than 2027-04-03T07:25:00Z;
2. elapsed calendar days >= 180;
3. all expected tranches required by the Q003 accumulation protocol are either present or explicitly accounted for by governed gap/recovery records;
4. no pre-start observations counted;
5. no duplicate prospective evidence identities;
6. chronology passes;
7. provenance/hashes/ledger integrity pass;
8. no prohibited validation/final evidence opened;
9. no early Q003 economic outcome field was accessed;
10. no cross-stream economic contamination occurred.

Structural failure => `INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE`.

Opening the structural readout gate does NOT open economic fields. Economic fields require a separate explicit human readout authorization.

## RND-0060Q/R structural gate
RND-0060Q/R may become `READOUT_ELIGIBLE_PENDING_HUMAN_GATE` only if all are true:
1. evaluation time is not earlier than 2027-04-07T02:33:50Z;
2. elapsed calendar days >= 180;
3. eligible non-DEFER observation count >= 100;
4. ADMIT and VETO groups each satisfy their frozen minimum structural count requirements at eventual readout;
5. no pre-start observations counted;
6. no duplicate market-day observations;
7. chronology passes;
8. provenance/hashes/ledger integrity pass;
9. no 2021–2022 consumed validation evidence used;
10. no 2023–2024 reserved-final evidence used;
11. no Q003 outcome input or contamination;
12. no early activity-policy economic outcome field was accessed.

If time horizon is met but observation count is <100, status remains:
`ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE`.

If structure is corrupt or insufficient, status becomes:
`INCONCLUSIVE_EXTEND_CONFIRMATION`.

## Economic readout authorization
Economic readout is a separate HUMAN_ONLY gate.

A machine may determine `READOUT_ELIGIBLE_PENDING_HUMAN_GATE`.
A machine may NOT set `economic_fields_open=TRUE`.

Human approval must identify:
- stream being opened;
- exact evidence ledger/version;
- exact readout protocol/version;
- timestamp of authorization;
- confirmation that no tuning or threshold changes are authorized;
- confirmation that reserved final remains closed;
- confirmation that promotion is not automatic.

Without that receipt, economic fields remain sealed.

## Outcome classification separation
Once human readout is authorized, each stream is classified only under its own frozen protocol.

### Q003
Uses its predeclared Q003 prospective validation decision protocol only.

Possible high-level outcomes remain governed by that protocol, including structural extension/inconclusive states and validation acceptance/rejection states.

No outcome automatically opens reserved final, shadow deployment, capital, or broker writes.

### RND-0060Q/R
Uses the frozen RND-0060Q criteria only.

Possible outcomes:
- `ACTIVITY_POLICY_INDEPENDENTLY_CONFIRMED`;
- `ACTIVITY_POLICY_NOT_INDEPENDENTLY_CONFIRMED`;
- `INCONCLUSIVE_EXTEND_CONFIRMATION`.

A positive activity-policy result establishes only independent confirmation of the veto-context mechanism. It is not a directional strategy and cannot be promoted as one.

## Promotion firewall
No prospective outcome may directly transition to strategy promotion.

Any future promotion requires a separately governed HUMAN_ONLY promotion review that verifies at minimum:
- exact frozen strategy/policy identity;
- prospective readout receipt;
- applicable success criteria satisfied;
- all integrity checks passed;
- no prohibited evidence reuse;
- no post-hoc tuning;
- shadow architecture readiness;
- risk architecture readiness;
- explicit human decision.

`promotion_authority` must remain `FALSE` inside RND-0060X.

## Reserved-final firewall
RND-0060X does not open 2023–2024 reserved final evidence.

Reserved final remains independently sealed and can only be opened under a future explicit human gate and separately defined protocol.

No positive prospective result automatically consumes or opens reserved final.

## Live-authority firewall
RND-0060X explicitly retains:
- `broker_write_authority=FALSE`;
- `capital_authority=FALSE`;
- `live_execution_authority=FALSE`;
- `automatic_promotion=FALSE`;
- `automatic_merge=FALSE`.

No readout outcome can modify these fields.

## Fail-closed conditions
The readout gate must remain closed on:
- evaluation before minimum date;
- insufficient required observation count;
- missing evidence ledger;
- missing hash/provenance identity;
- duplicate observation identity;
- pre-start contamination;
- chronology regression;
- prohibited 2021–2022 validation reuse;
- prohibited 2023–2024 reserved-final access;
- Q003/RND-0060Q/R cross-stream outcome contamination;
- evidence mutation;
- unknown protocol version;
- missing human readout receipt;
- any attempted automatic promotion;
- any attempted broker/capital/live authority.

## Required implementation tests
The implementation must prove at minimum:
1. Q003 early date cannot open readout;
2. Q003 exactly at/after minimum time may pass time gate;
3. Q003 pre-start contamination fails closed;
4. Q003 duplicate evidence fails closed;
5. Q003 economic fields cannot open without human receipt;
6. RND-0060Q/R early date cannot open readout;
7. RND-0060Q/R 180 days but <100 observations remains accumulating;
8. RND-0060Q/R >=180 days and >=100 observations can become human-gate eligible if structure is clean;
9. RND-0060Q/R pre-start contamination fails closed;
10. duplicate market days fail closed;
11. 2021–2022 evidence reuse fails closed;
12. 2023–2024 reserved-final access fails closed;
13. cross-stream economic contamination fails closed;
14. chronology regression fails closed;
15. missing provenance/hash identity fails closed;
16. human readout receipt is stream-specific;
17. human readout receipt cannot authorize tuning;
18. positive outcome cannot set promotion authority;
19. any attempt to set broker/capital/live authority fails closed;
20. reserved final remains closed;
21. deterministic readiness evaluation yields identical output;
22. Q003 and RND-0060Q/R readiness counters remain independent;
23. structural eligibility does not imply economic success;
24. no machine path can transition directly from readout eligibility to promotion.

## Interpretation boundary
Passing RND-0060X establishes that prospective evidence cannot be peeked at early, mixed across programs, or promoted automatically. It does not reveal either stream's economic result and does not authorize trading.