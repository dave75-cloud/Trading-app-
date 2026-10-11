# RND-0060U — Strategy Integration Architecture

## Status
FROZEN ARCHITECTURE DESIGN — NO STRATEGY OUTCOME / NO EXECUTION AUTHORITY

## Purpose
Define the governed integration path an eventual independently validated directional signal must traverse before it could ever reach shadow execution, while preserving strict separation between signal generation, activity admissibility, risk authority, execution, reconciliation, audit, and kill controls.

This task is architecture-only. It does not create a directional signal, test a strategy, evaluate P&L, open validation/final evidence, or authorize broker writes/capital.

## Existing upstream contracts preserved
RND-0060U must extend rather than weaken the already-established project separation:
- research may propose signals but has no broker authority;
- RND-0060N activity admissibility is veto-only and may output only ADMIT / VETO / DEFER;
- activity state cannot create, reverse, enlarge, or directionally modify exposure;
- risk authority is separate from strategy logic;
- shadow execution must remain structurally incapable of becoming live execution by configuration error alone;
- control/API layers do not confer promotion or execution authority;
- human approval remains mandatory for strategy promotion, validation opening, final-test opening, capital allocation, broker writes, and live execution.

## Canonical integration pipeline
An eventual strategy-facing event must traverse exactly this ordered pipeline:

1. `SIGNAL_PROPOSAL`
2. `SIGNAL_PROVENANCE_CHECK`
3. `ACTIVITY_ADMISSIBILITY`
4. `RISK_AUTHORIZATION`
5. `SHADOW_EXECUTION_INTENT`
6. `SHADOW_EXECUTION_SIMULATION`
7. `RECONCILIATION`
8. `AUDIT_COMMIT`
9. `TERMINAL_STATE`

No stage may be skipped or reordered.

## Stage 1 — SIGNAL_PROPOSAL
Input is an independently governed directional signal object only.

Required fields:
- signal_id
- strategy_id
- strategy_version
- instrument
- direction
- requested_exposure
- signal_timestamp_utc
- source_evidence_identity
- strategy_promotion_receipt

Rules:
- signal must not originate from activity admissibility;
- requested_exposure must be explicit;
- no implicit default direction or size;
- missing or malformed provenance => FAIL_CLOSED.

## Stage 2 — SIGNAL_PROVENANCE_CHECK
Purpose: prove that the signal comes from a separately governed, human-promoted strategy artifact.

Required checks:
- immutable strategy identifier/version;
- valid promotion receipt;
- source evidence identity present;
- no prohibited validation/final contamination;
- signal timestamp monotonicity;
- no duplicate signal_id;
- no unapproved strategy substitution.

Failure result: `REJECT_PROVENANCE`.

## Stage 3 — ACTIVITY_ADMISSIBILITY
The frozen RND-0060N contract is authoritative.

Allowed outputs only:
- `ADMIT`
- `VETO`
- `DEFER`

Semantics:
- ADMIT preserves instrument, sign, direction, and requested exposure exactly;
- VETO suppresses the proposal;
- DEFER postpones evaluation and creates no exposure;
- activity state cannot generate a signal;
- activity state cannot invert direction;
- activity state cannot increase size;
- activity state cannot substitute instruments;
- malformed/unavailable activity state fails closed to DEFER.

## Stage 4 — RISK_AUTHORIZATION
Risk is downstream of both signal generation and admissibility.

Risk may only:
- `AUTHORIZE_UNCHANGED`
- `REDUCE`
- `REJECT`

Risk may never:
- increase requested exposure;
- reverse direction;
- create a position from zero;
- change instrument;
- bypass a VETO or DEFER;
- resurrect a rejected signal.

Required inputs include:
- portfolio state identity;
- exposure limits;
- concentration limits;
- drawdown/kill state;
- stale-data state;
- reconciliation health;
- execution mode.

Any uncertain or stale critical state => `REJECT` or global `KILL`, never permissive fallback.

## Stage 5 — SHADOW_EXECUTION_INTENT
A risk-authorized proposal may be transformed into a shadow intent object only.

Required fields:
- parent_signal_id
- admissibility_decision_id
- risk_decision_id
- instrument
- direction
- authorized_exposure
- intent_timestamp_utc
- mode=`SHADOW_ONLY`
- broker_write_authority=`FALSE`

No broker endpoint, credential, order ticket, or live write method is permitted in this object.

## Stage 6 — SHADOW_EXECUTION_SIMULATION
The simulator may model:
- bid/ask spread;
- slippage assumptions;
- latency;
- partial fills;
- rejected fills;
- stale quotes;
- disconnected provider state;
- duplicate execution requests;
- cancel/replace semantics;
- market-session constraints.

It must not call broker write endpoints.

Output is simulated execution evidence only.

## Stage 7 — RECONCILIATION
Every shadow execution event must reconcile against:
- originating signal;
- admissibility decision;
- risk decision;
- simulated fill ledger;
- expected position state;
- observed provider/account read state where applicable.

Allowed reconciliation states:
- `RECONCILED`
- `RECONCILIATION_PENDING`
- `RECONCILIATION_FAILED`

`RECONCILIATION_FAILED` must block all downstream new intents until explicitly cleared under governance.

## Stage 8 — AUDIT_COMMIT
Each completed event chain must produce an immutable audit record containing identifiers and hashes for every upstream/downstream object.

Audit must be append-only and independently reconstructable.

Required integrity properties:
- one signal -> at most one active admissibility decision;
- one admitted signal -> at most one active risk decision;
- one authorized risk decision -> at most one active shadow intent;
- no orphan execution events;
- no silent mutation;
- no unlogged retry;
- no identifier reuse.

## Stage 9 — TERMINAL_STATE
Canonical terminal outcomes:
- `PROVENANCE_REJECTED`
- `ACTIVITY_VETOED`
- `ACTIVITY_DEFERRED`
- `RISK_REJECTED`
- `SHADOW_EXECUTION_REJECTED`
- `RECONCILIATION_PENDING`
- `RECONCILIATION_FAILED`
- `SHADOW_CYCLE_RECONCILED`
- `KILLED`

No terminal state in RND-0060U authorizes live execution.

## Kill hierarchy
Kill controls dominate all lower-level logic.

Precedence:
1. GLOBAL_KILL
2. RECONCILIATION_KILL
3. DATA_INTEGRITY_KILL
4. RISK_LIMIT_KILL
5. STRATEGY_SUSPEND
6. normal pipeline decisions

Once any applicable kill is active:
- no new shadow intent may be created;
- pending DEFER items may not auto-release;
- retries require explicit restart semantics;
- lower-priority states cannot override the kill.

## Fail-closed rules
The pipeline fails closed on:
- missing/malformed provenance;
- unknown strategy version;
- invalid promotion receipt;
- stale or missing market state;
- stale or missing portfolio state;
- malformed activity decision;
- malformed risk decision;
- duplicate identifiers;
- timestamp regression;
- reconciliation mismatch;
- audit persistence failure;
- unknown enum/state;
- any attempted mode other than SHADOW_ONLY.

## Separation-of-authority invariants
The following must be machine-testable:
1. strategy logic cannot call broker-write code;
2. activity admissibility cannot create direction or size;
3. risk cannot increase size or invert direction;
4. shadow execution cannot become live via configuration alone;
5. control/API cannot promote strategies or allocate capital;
6. reconciliation failure blocks further intents;
7. kill state overrides all ordinary decisions;
8. no stage may infer missing values permissively;
9. every transition must carry immutable parent identifiers;
10. human-only gates remain external to this pipeline.

## Human-only gates retained
RND-0060U explicitly does NOT authorize:
- strategy promotion;
- validation opening;
- reserved-final opening;
- Q003 or RND-0060R prospective readout;
- capital allocation;
- live broker credentials;
- broker writes;
- live execution;
- automatic merge.

## Test plan for implementation
The next implementation task must provide a pure, broker-disconnected state-machine kernel plus hostile fixtures proving at minimum:
- stage order cannot be bypassed;
- malformed provenance fails closed;
- VETO cannot become exposure;
- DEFER cannot auto-release;
- ADMIT cannot modify sign/size/instrument;
- risk cannot enlarge/invert/substitute;
- duplicate IDs are rejected;
- stale state is rejected;
- reconciliation failure blocks subsequent intents;
- kill precedence dominates;
- SHADOW_ONLY is mandatory;
- broker-write/live-authority fields remain false;
- audit lineage is complete and immutable.

## Interpretation boundary
RND-0060U is architectural scaffolding only. Passing its tests would establish that the system can safely compose future independently validated signals with admissibility, risk, shadow execution, and reconciliation. It would not establish trading edge, profitability, validation success, or permission to trade live.