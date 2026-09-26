# M006f Shadow Execution Architecture

Status: DESIGN ONLY / NON-OPERATIONAL  
Authority: NONE  
Broker transport: ABSENT  
Production-capable configuration path: ABSENT

## Purpose

M006f is a deterministic shadow-execution layer for accepted trading decisions.
It measures hypothetical execution behaviour without acquiring broker, account,
credential, network, strategy, sizing, promotion, or capital authority.

M006f does not create signals and does not decide whether a trade should exist.
It consumes an already-approved decision record and models what would have
happened under an explicit local execution model.

## Structural safety rule

A configuration change alone must never be able to turn M006f into an
execution system.

Therefore M006f contains no:

- broker transport;
- HTTP client;
- account identifier;
- credential loader;
- environment selector;
- submission method;
- production routing;
- endpoint string;
- write retry logic.

A future write-capable system would have to be a different component and pass a
separate human approval gate.

## Inputs

Each shadow action must be supplied as local data and must include:

- immutable event ID;
- authoritative event timestamp;
- pair;
- action type;
- already-approved absolute units;
- entry side where applicable;
- local bid and ask snapshot;
- explicit conversion factor needed for AUD-valued accounting;
- source provenance.

M006f must not silently obtain missing market or conversion data.

## Event model

Supported primitive actions:

- `entry`
- `exit`

A reversal must be represented as two ordered primitives:

1. exit existing shadow position;
2. entry in the opposite direction.

Opaque one-step reversal is invalid.

## Fill model

The first candidate uses a deterministic adverse fill model.

For a long:
- entry uses ask plus configured adverse slippage;
- exit uses bid minus configured adverse slippage.

For a short:
- entry uses bid minus configured adverse slippage;
- exit uses ask plus configured adverse slippage.

Slippage is a shadow assumption only. It must be recorded with every result and
must not change the frozen strategy.

## Ledger

The simulator maintains an append-only logical ledger containing:

- event ID;
- timestamp;
- pair;
- action;
- side;
- units;
- reference bid/ask;
- shadow fill;
- slippage assumption;
- AUD-valued realized P&L where applicable;
- resulting shadow position;
- equity;
- drawdown;
- provenance.

Duplicate event IDs fail closed.

Entry into an already-open pair fails closed. Exit from a flat pair fails
closed. Negative or crossed prices fail closed.

## Accounting

Cross-pair accounting is explicit rather than inferred.

Entry records provide `base_to_aud`, used for nominal AUD exposure.
Exit records provide `quote_to_aud`, used to convert realized quote-currency
P&L into AUD.

Missing or non-positive conversion factors fail closed.

This avoids hidden market-data dependencies and makes the replay fully
reproducible.

## Outputs

Minimum run outputs:

- final AUD equity;
- realized AUD P&L;
- maximum drawdown;
- maximum gross nominal AUD exposure;
- per-event shadow ledger;
- final positions;
- input and configuration hashes.

## Separation from M006e

M006f is downstream and observational.

M006e must not:
- import M006f;
- wait for M006f;
- depend on M006f success;
- mutate behaviour based on M006f output.

M006f failure therefore cannot contaminate the frozen observation cohort.

## Promotion boundary

Completing or validating M006f does not authorize practice or production
execution. Phase promotion remains a human decision.
