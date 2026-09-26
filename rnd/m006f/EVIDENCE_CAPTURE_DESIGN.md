# M006f Prospective Evidence-Capture Design

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic promotion: NONE
Human integration approval: REQUIRED

## Purpose

This design defines a future offline boundary for creating the exact local
market-evidence records required by the M006f market-evidence contract.

It does not modify M006e or canonical M005 and is not connected to the current
forward-observation stack.

## Architecture

The future path is deliberately one-way:

accepted event
    |
    v
local capture snapshot
    |
    v
offline evidence sealer
    |
    v
M006f market-evidence JSONL
    |
    v
accepted-event replay adapter
    |
    v
offline shadow simulator

M006f itself remains unable to acquire missing evidence.

## Local capture snapshot

A capture snapshot is an immutable local JSON artifact containing:

- event ID;
- event leg;
- pair;
- authoritative event timestamp;
- local price timestamp;
- source-provider label;
- exact bid and ask;
- supporting AUDUSD bid and ask where conversion requires it.

The snapshot is the evidence source. Its file bytes are SHA-256 hashed by the
offline sealer.

## Conversion rules

All conversion factors are derived deterministically from the same local price
snapshot.

Midpoint is used only for AUD conversion arithmetic. It is never substituted
for the target pair's exact bid/ask execution evidence.

Let:

AUDUSD_mid = (AUDUSD_bid + AUDUSD_ask) / 2

For AUDUSD:

- entry base_to_aud = 1
- exit quote_to_aud = 1 / AUDUSD_mid

For EURUSD and GBPUSD:

- entry base_to_aud = pair_mid / AUDUSD_mid
- exit quote_to_aud = 1 / AUDUSD_mid

For USDJPY:

- entry base_to_aud = 1 / AUDUSD_mid
- exit quote_to_aud = 1 / (USDJPY_mid * AUDUSD_mid)

## Timestamp policy

Both event and price timestamps must be explicit UTC timestamps.

The sealer records the evidence exactly as supplied.

RND-0013 does not introduce a maximum age threshold. Any future freshness
threshold would be a separate human-approved operational policy, not something
silently introduced by this R&D layer.

## Provenance

The sealer computes SHA-256 over the original local capture snapshot.

The output evidence record contains:

- source artifact label;
- source artifact SHA-256;
- source-provider label.

This creates a reproducible link from M006f evidence back to the immutable
local capture artifact.

## Fail-closed rules

The sealer rejects:

- unsupported pairs or legs;
- missing event identity;
- non-UTC timestamps;
- missing required pair prices;
- missing AUDUSD conversion prices;
- zero, negative, non-finite or crossed prices;
- contract-invalid output.

It must not invent:

- spreads;
- bid/ask values;
- conversion prices;
- timestamps;
- event identities.

## Governance boundary

This design is prospective only.

It does not authorize modification of frozen M006e during forward observation.

It does not modify canonical M005.

It creates no strategy, sizing, risk, execution, promotion or capital
authority.

Any future operational capture component requires a separate human decision
after the frozen observation phase.
