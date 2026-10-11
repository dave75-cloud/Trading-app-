# RND-0060V — Shadow Execution & Risk Realism

## Status
FROZEN ARCHITECTURE DESIGN — SHADOW ONLY / NO LIVE AUTHORITY

## Purpose
Strengthen the realism and failure semantics of the broker-disconnected shadow execution and risk pipeline defined upstream by RND-0060U.

RND-0060V must improve modelling fidelity without conferring broker-write authority, capital authority, strategy promotion authority, or any path from configuration to live execution.

## Upstream invariants preserved
- RND-0060U pipeline order is authoritative.
- Activity admissibility remains ADMIT / VETO / DEFER only.
- Risk may AUTHORIZE_UNCHANGED / REDUCE / REJECT only.
- Risk may never enlarge exposure, reverse direction, substitute instrument, bypass VETO/DEFER, or resurrect rejection.
- Execution mode remains `SHADOW_ONLY`.
- Broker write authority remains `FALSE`.
- Reconciliation failure blocks further intents.
- Kill hierarchy dominates all ordinary decisions.
- Every event retains immutable parent identifiers and audit lineage.

## Frozen scope
RND-0060V covers only shadow realism and fail-closed risk/execution state handling:

1. bid/ask execution semantics;
2. slippage modelling;
3. execution latency;
4. partial fills;
5. rejected fills;
6. stale quotes;
7. disconnected provider state;
8. duplicate execution requests;
9. cancel/replace semantics;
10. market-session eligibility;
11. execution-state reconciliation;
12. portfolio/risk-state freshness;
13. execution fault propagation;
14. kill-state escalation.

## Explicit exclusions
RND-0060V does NOT:
- create or test a trading strategy;
- inspect Q003 prospective outcomes;
- inspect RND-0060R prospective economic outcomes;
- open 2021–2022 validation;
- open 2023–2024 reserved final;
- evaluate strategy profitability;
- authorize capital;
- authorize broker credentials;
- call broker write endpoints;
- create live order tickets;
- enable automatic promotion or merge.

## Execution realism contract

### Reference quote
Each simulated execution request must carry an immutable quote snapshot with:
- instrument;
- bid;
- ask;
- quote_timestamp_utc;
- quote_source_identity;
- quote_sequence or equivalent monotonic identity where available;
- session_state;
- provider_state.

Invalid bid/ask, crossed market, missing timestamp, unknown source identity, stale quote, closed session, or disconnected provider => no fill.

### Side-aware entry price
For an accepted shadow market execution:
- LONG consumes ask-side liquidity;
- SHORT consumes bid-side liquidity.

The simulator must never use mid as an executable price.

### Slippage
Slippage is an explicit non-negative adverse execution adjustment.

- LONG fill >= reference ask.
- SHORT fill <= reference bid.
- favourable slippage is prohibited in this first realism contract.
- slippage must never reverse sign.
- malformed or negative slippage => reject/fail closed.

No calibration or optimization of slippage assumptions is performed in RND-0060V.

### Latency
Latency must be explicit and non-negative.

Execution may only use a quote/fill state whose timestamp is not earlier than the intent timestamp and is consistent with the configured shadow latency model.

Timestamp regression, impossible chronology, or latency violation => reject/fail closed.

### Partial fills
Partial fills are permitted only when:
- filled exposure > 0;
- filled exposure <= authorized exposure;
- direction/instrument remain unchanged;
- residual exposure is explicit.

A partial fill may never create a follow-up request automatically. Any retry/cancel-replace requires a distinct governed event with lineage to the original intent.

### Rejected fills
A simulated rejection creates zero exposure.

The rejection must include a reason code, e.g.:
- STALE_QUOTE
- PROVIDER_DISCONNECTED
- SESSION_CLOSED
- INVALID_QUOTE
- LATENCY_VIOLATION
- DUPLICATE_REQUEST
- RISK_STATE_STALE
- RECONCILIATION_BLOCK
- KILL_ACTIVE
- SIMULATED_LIQUIDITY_REJECT

Unknown rejection reason => fail closed.

### Duplicate execution requests
An execution request identifier is single-use.

Duplicate request IDs must be rejected idempotently and may not produce a second fill or second position change.

### Cancel/replace
Cancel/replace is modelled as explicit state transitions only.

Rules:
- an already terminal request cannot be replaced;
- replacement cannot increase authorized exposure;
- replacement cannot change instrument or direction;
- replacement must preserve parent signal/admissibility/risk lineage;
- replacement receives a new unique request ID;
- replacement is SHADOW_ONLY;
- replacement may be blocked by risk/reconciliation/kill state.

## Risk realism contract

### Required fresh state
Risk authorization requires fresh, internally consistent identities for:
- portfolio state;
- current exposures;
- concentration state;
- drawdown/kill state;
- quote/market state;
- reconciliation health;
- provider state;
- execution mode.

Missing, stale, contradictory, or unknown critical state => REJECT or KILL, never permissive fallback.

### Exposure monotonicity
Across the complete pipeline:
`filled_exposure <= authorized_exposure <= requested_exposure`.

No downstream stage may increase exposure.

### Direction/instrument invariance
Across signal -> admissibility -> risk -> shadow intent -> simulated fill:
- instrument must remain unchanged;
- direction must remain unchanged;
- zero exposure may never become non-zero downstream.

### Reconciliation block
If reconciliation state is `RECONCILIATION_FAILED`, no new shadow intent or replacement may be created.

If reconciliation is `RECONCILIATION_PENDING`, policy is fail closed for new exposure creation.

Only `RECONCILED` permits normal progression.

### Provider and data state
Provider states:
- CONNECTED
- DEGRADED
- DISCONNECTED

DISCONNECTED => reject execution.
DEGRADED => no new exposure unless all required data freshness/integrity checks explicitly pass; otherwise reject.

Unknown state => reject.

### Session state
Session states:
- OPEN
- CLOSED
- UNKNOWN

Only OPEN is eligible for simulated fills.

## Fault propagation
Execution realism faults must propagate upstream into governance state where appropriate.

At minimum:
- reconciliation mismatch => RECONCILIATION_KILL;
- malformed quote identity => DATA_INTEGRITY_KILL;
- impossible chronology => DATA_INTEGRITY_KILL;
- stale portfolio/risk state => RISK reject or RISK_LIMIT_KILL according to severity;
- duplicate execution request => reject and audit event;
- audit persistence failure => GLOBAL_KILL/fail closed.

No lower-priority state may override a kill.

## Determinism and auditability
Given identical input objects and fixed simulation assumptions, the shadow result must be deterministic.

Every output must include:
- request ID;
- parent intent/risk/admissibility/signal IDs;
- quote identity;
- risk-state identity;
- simulated status;
- requested exposure;
- authorized exposure;
- filled exposure;
- residual exposure;
- reference executable side;
- simulated fill price when filled;
- slippage assumption;
- latency assumption;
- rejection/fault code where applicable;
- broker_write_authority=`FALSE`;
- mode=`SHADOW_ONLY`.

## Separation from science
RND-0060V evaluates system behaviour, not trading edge.

No comparison of strategy returns with/without realism parameters is permitted here. No slippage/latency parameter search is permitted. No optimization against P&L is permitted.

## Required hostile implementation tests
The implementation must prove at minimum:
1. LONG fills from ask, never mid/bid;
2. SHORT fills from bid, never mid/ask;
3. adverse slippage sign is enforced;
4. negative/favourable slippage fails closed;
5. stale quote rejects;
6. crossed/invalid quote rejects;
7. closed/unknown session rejects;
8. disconnected/unknown provider rejects;
9. partial fill cannot exceed authorization;
10. rejected fill creates zero exposure;
11. duplicate request cannot double-fill;
12. cancel/replace cannot enlarge/invert/substitute;
13. timestamp regression/latency violation rejects;
14. stale risk/portfolio state rejects;
15. reconciliation pending/failed blocks new exposure;
16. kill state dominates execution;
17. exposure monotonicity holds end-to-end;
18. SHADOW_ONLY and broker_write_authority=FALSE are immutable;
19. audit lineage is complete;
20. deterministic replay yields identical output.

## Interpretation boundary
Passing RND-0060V would establish stronger operational realism and safety for shadow execution. It would not demonstrate trading profitability, validation success, or permission to trade live.
