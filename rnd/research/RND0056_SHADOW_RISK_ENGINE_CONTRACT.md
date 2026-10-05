# RND-0056 — Shadow Portfolio Risk Engine

Status: CONTRACT FROZEN / FIXTURE ONLY / ZERO WRITE

## Purpose

Extend RND-0051 from single-intent guardrails to deterministic portfolio-aware shadow risk evaluation.

## Inputs

- frozen candidate fingerprint;
- fixture-only shadow intents;
- fixture positions/exposures;
- explicit risk policy;
- current/decision timestamps;
- previously seen intent IDs.

## Required controls

- candidate identity;
- symbol and side allow-list;
- duplicate/idempotency rejection;
- stale-evidence rejection;
- kill-switch rejection;
- per-intent unit limit;
- per-pair absolute position limit;
- portfolio gross exposure limit;
- portfolio net exposure limit;
- currency-leg exposure aggregation and limit;
- maximum concurrent non-flat pairs;
- authority-escalation rejection;
- deterministic reason codes and receipt output.

## Currency-leg semantics

For a pair BASE/QUOTE, long units add BASE exposure and subtract QUOTE exposure; short units subtract BASE and add QUOTE exposure. Fixture units are abstract risk units, not broker order quantities.

## Non-authority

No market-data retrieval, order construction, broker calls, credentials, capital allocation, live-environment authority, candidate promotion or automatic execution.
All results must state broker_writes=FALSE, capital_authority=FALSE, execution_authority=FALSE.
