# RND-0058 — Shadow Execution/Reconciliation Simulator

Status: CONTRACT FROZEN / FIXTURE ONLY / ZERO WRITE

## Purpose

Exercise order-lifecycle and reconciliation architecture without constructing or submitting broker orders.

## Inputs

- accepted shadow intent receipt;
- accepted risk decision receipt;
- fixture market/execution events;
- deterministic simulator policy.

## Lifecycle

INTENT_ACCEPTED -> SHADOW_ORDER_PLANNED -> SHADOW_ACKNOWLEDGED -> SHADOW_PARTIAL / SHADOW_FILLED / SHADOW_CANCELLED / SHADOW_REJECTED -> RECONCILED.

## Required controls

- exact candidate fingerprint;
- intent/risk receipt identity binding;
- idempotent shadow order ID;
- no state skipping;
- no fill before acknowledgement;
- filled quantity cannot exceed planned quantity;
- cumulative fills monotonic;
- cancellation terminal except reconciliation;
- reconciliation must match simulated fills and position delta;
- stale/duplicate fixture events rejected;
- deterministic audit receipt.

## Non-authority

The simulator must not contain broker URLs, credentials, HTTP clients, broker order payload builders, or write methods. It grants no broker, capital, live-environment, promotion or merge authority.
