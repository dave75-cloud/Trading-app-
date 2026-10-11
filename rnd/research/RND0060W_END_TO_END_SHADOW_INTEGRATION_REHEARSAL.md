# RND-0060W — End-to-End Shadow Integration Rehearsal

## Status
FROZEN INTEGRATION REHEARSAL DESIGN — SHADOW ONLY / NO STRATEGY SCIENCE / NO LIVE AUTHORITY

## Purpose
Verify that the already-frozen RND-0060U strategy-integration state machine and RND-0060V shadow execution/risk realism layer compose correctly as one deterministic broker-disconnected pipeline.

RND-0060W is an integration rehearsal only. It does not create a strategy, inspect prospective outcomes, evaluate profitability, open validation/final evidence, allocate capital, or authorize broker writes.

## Authoritative upstream contracts
RND-0060W may orchestrate but must not weaken, reinterpret, or bypass:
- RND-0060U strategy-integration architecture and state-machine invariants;
- RND-0060V shadow execution/risk realism invariants;
- activity admissibility semantics: ADMIT / VETO / DEFER only;
- risk semantics: AUTHORIZE_UNCHANGED / REDUCE / REJECT only;
- SHADOW_ONLY execution mode;
- broker_write_authority=FALSE;
- reconciliation blocking;
- kill-state precedence;
- immutable audit lineage;
- human-only promotion/live/capital gates.

## Canonical integrated pipeline
A rehearsal event must traverse exactly:

1. SIGNAL_PROPOSAL
2. SIGNAL_PROVENANCE_CHECK
3. ACTIVITY_ADMISSIBILITY
4. RISK_AUTHORIZATION
5. SHADOW_EXECUTION_INTENT
6. EXECUTION_REALISM_PRECHECK
7. SHADOW_EXECUTION_SIMULATION
8. RECONCILIATION
9. AUDIT_COMMIT
10. TERMINAL_STATE

No stage may be skipped, reordered, or silently retried.

## Rehearsal inputs
The rehearsal uses synthetic fixed fixtures only. No Q003 prospective outcomes, RND-0060R outcomes, validation 2021–2022, reserved final 2023–2024, broker account state, or live market writes are permitted.

Each rehearsal scenario must explicitly supply:
- signal object and promotion/provenance metadata;
- activity admissibility decision;
- risk state and risk decision;
- quote snapshot;
- execution realism assumptions;
- reconciliation result;
- kill state;
- deterministic audit identifiers.

Missing values are never inferred permissively.

## Happy-path contract
A valid scenario may terminate as SHADOW_CYCLE_RECONCILED only when all are true:
- signal provenance passes;
- activity result is ADMIT;
- risk result is AUTHORIZE_UNCHANGED or REDUCE;
- authorized exposure <= requested exposure;
- quote/session/provider/risk state is valid and fresh;
- execution request is SHADOW_ONLY;
- broker_write_authority is FALSE;
- simulated fill exposure <= authorized exposure;
- instrument and direction remain unchanged end-to-end;
- reconciliation is RECONCILED;
- audit lineage is complete.

## Negative-path terminal mapping
Integration must map failures deterministically:
- malformed/invalid provenance -> PROVENANCE_REJECTED;
- VETO -> ACTIVITY_VETOED;
- DEFER -> ACTIVITY_DEFERRED;
- risk reject/stale state -> RISK_REJECTED;
- quote/provider/session/latency/liquidity failure -> SHADOW_EXECUTION_REJECTED;
- reconciliation pending -> RECONCILIATION_PENDING;
- reconciliation failed -> RECONCILIATION_FAILED and block subsequent intents;
- active kill -> KILLED.

No failed stage may create downstream exposure.

## Cross-layer invariants
The integrated rehearsal must machine-check:
1. requested exposure may only stay unchanged or decrease downstream;
2. instrument cannot change across any stage;
3. direction cannot change across any stage;
4. zero exposure cannot become non-zero downstream;
5. VETO and DEFER cannot reach risk/execution as exposure-producing events;
6. risk reduction must propagate exactly into shadow intent authorization;
7. execution partial fill cannot exceed risk authorization;
8. execution rejection produces zero exposure and cannot reconcile as a fill;
9. duplicate execution request cannot alter state twice;
10. reconciliation failure blocks later intents/replacements;
11. kill state dominates activity, risk, and execution decisions;
12. SHADOW_ONLY and broker_write_authority=FALSE remain immutable end-to-end;
13. every child object carries immutable parent identifiers;
14. audit lineage can reconstruct the complete event chain;
15. identical complete input yields identical complete output.

## State contamination guards
RND-0060W must explicitly reject or avoid:
- Q003 outcome fields;
- RND-0060R economic outcome fields;
- validation/final partition access;
- broker credentials;
- broker-write methods/endpoints;
- live order identifiers;
- capital-allocation authority;
- automatic strategy promotion;
- automatic merge.

## Reconciliation semantics
Reconciliation is the final operational truth gate.

Rules:
- RECONCILED permits SHADOW_CYCLE_RECONCILED only when simulated execution and expected state agree;
- RECONCILIATION_PENDING creates no new exposure and blocks subsequent new exposure until resolved;
- RECONCILIATION_FAILED triggers reconciliation block semantics and must dominate later normal requests;
- mismatch between simulated fill ledger and expected position state fails closed.

## Audit contract
Every rehearsal output must include immutable identifiers for:
- signal;
- provenance decision;
- activity decision;
- risk decision;
- shadow intent;
- execution request/result;
- quote identity;
- risk-state identity;
- reconciliation event;
- terminal state.

The audit representation must be deterministic and append-only in semantics. No silent mutation, identifier reuse, or unlogged retry is permitted.

## Required hostile integration tests
The implementation must prove at minimum:
1. valid happy path reaches SHADOW_CYCLE_RECONCILED;
2. provenance rejection halts before activity/risk execution exposure;
3. VETO halts before risk/execution exposure;
4. DEFER cannot auto-release into execution;
5. risk REDUCE propagates exact reduced exposure;
6. risk REJECT creates no execution intent;
7. stale risk state blocks execution;
8. stale quote blocks execution;
9. disconnected provider blocks execution;
10. closed session blocks execution;
11. partial fill respects authorized exposure;
12. rejected fill creates zero exposure;
13. duplicate execution request cannot double-apply;
14. direction cannot invert across layers;
15. instrument cannot substitute across layers;
16. kill state dominates all ordinary decisions;
17. reconciliation pending blocks subsequent new exposure;
18. reconciliation failure blocks subsequent new exposure;
19. malformed audit lineage fails closed;
20. SHADOW_ONLY is immutable;
21. broker_write_authority remains FALSE;
22. no prohibited prospective/validation/final fields are accepted;
23. exposure monotonicity holds end-to-end;
24. deterministic replay yields byte-equivalent normalized output.

## Interpretation boundary
Passing RND-0060W establishes only that the governed shadow components compose safely and deterministically as one end-to-end pipeline. It does not establish trading edge, profitability, prospective validation success, capital readiness, broker-write readiness, or live-trading permission.
