# RND-0057 — Control/API Schema Contract

Status: CONTRACT FROZEN / NO EXECUTION AUTHORITY

## Purpose

Define machine-readable contracts for lifecycle state and human authority without granting authority by state alone.

## Required schema families

1. CandidateIdentity
2. EvidenceStatus
3. ValidationDecision
4. ShadowIntent
5. RiskDecision
6. HumanAuthorityReceipt
7. ReconciliationStatus
8. ControlEnvelope

## Core invariants

- candidate fingerprint required wherever candidate-scoped;
- timestamps UTC Z and M5-aligned where market-evidence related;
- authority fields default false;
- lifecycle state never implies broker-write, capital or live authority;
- human authority receipt must identify the exact transition/action authorized;
- rejected candidate state is terminal;
- structural inconclusive may return only to evidence accumulation;
- execution eligibility is not execution authority;
- all unknown fields/states/actions fail closed;
- API schemas carry no credentials or secrets.

## Authority bits

strategy_evaluation_authorized, shadow_authorized, risk_policy_authorized, broker_writes_authorized, capital_authority, live_environment_authorized.

## Non-authority

No broker calls, order submission, capital allocation, candidate promotion, reserved-final access or automatic transition authority.
