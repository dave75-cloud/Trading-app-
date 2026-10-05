# RND-0051 — Shadow / Risk Architecture Contract

Status: ARCHITECTURE / FIXTURE-ONLY / ZERO-WRITE

## Purpose

Build and test the control path that a future validated candidate would have to traverse before any broker action could ever be contemplated:

candidate signal intent -> shadow proposal -> policy/risk checks -> accept/reject decision -> immutable audit record.

RND-0051 uses fixture/synthetic intents only. It does not consume Q003 prospective outcomes and does not create broker orders.

## Separation of authority

The strategy layer may propose an intent but may not allocate capital, choose production risk limits, call broker endpoints, or promote itself.

The risk layer may accept or reject a shadow proposal under an injected test policy but may not send an order.

The execution layer is absent from RND-0051.

## Required intent fields

- candidate_fingerprint
- intent_id
- symbol
- side (`LONG`, `SHORT`, `FLAT`)
- decision_time_utc
- evidence_time_utc
- requested_units (fixture quantity only)
- source_state (`SHADOW_FIXTURE` only)

## Required fail-closed checks

A fixture proposal must be rejected if any of the following applies:

- candidate fingerprint mismatch;
- symbol outside the four-pair universe;
- invalid side;
- stale evidence according to injected fixture policy;
- decision precedes evidence;
- duplicate intent ID;
- requested fixture units are non-positive for LONG/SHORT;
- requested fixture units exceed injected fixture max-units policy;
- projected gross fixture exposure exceeds injected fixture limit;
- projected currency-leg fixture exposure exceeds injected fixture limit;
- policy kill switch is active;
- broker_writes is anything other than false;
- capital_authority is anything other than false;
- source state is anything other than `SHADOW_FIXTURE`.

## Output

Pure decision only:

- `SHADOW_ACCEPT`
- `SHADOW_REJECT`

with deterministic reason codes. No order object suitable for submission may be produced.

## Explicit prohibitions

- no OANDA token/account access;
- no HTTP broker call;
- no order endpoint construction;
- no live or practice write;
- no capital allocation;
- no production sizing policy;
- no Q003 prospective outcome access;
- no automatic promotion;
- no automatic merge.

broker_writes=FALSE
capital_authority=FALSE
execution_authority=FALSE
