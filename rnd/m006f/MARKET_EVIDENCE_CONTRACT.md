# M006f Prospective Market-Evidence Contract

Status: R&D CANDIDATE
Version: M006f-market-evidence-v0.1
Authority: NONE
Automatic promotion: NONE

## Purpose

This contract defines the local evidence required to convert an accepted
M006e event leg into an M006f offline shadow-execution primitive.

The contract does not acquire market data and does not authorize execution.
It only defines the evidence that must already exist locally.

## Record format

One JSON object per line.

Each record represents one logical event leg identified uniquely by:

`event_id` + `leg`

Required common fields:

- `contract_version`
- `event_id`
- `leg`
- `pair`
- `event_timestamp_utc`
- `price_timestamp_utc`
- `bid`
- `ask`
- `source_provider`
- `source_artifact`
- `source_artifact_sha256`

Allowed pairs:

- AUDUSD
- EURUSD
- GBPUSD
- USDJPY

Allowed legs:

- entry
- exit
- reversal_entry
- reversal_exit

## Price evidence

`bid` and `ask` must be explicit positive finite numbers.

`ask` must be greater than or equal to `bid`.

Midpoint-only evidence is insufficient.

The contract does not permit reconstruction of bid/ask from:

- bar close;
- midpoint;
- assumed spread;
- later market data;
- another provider.

## AUD conversion evidence

Entry legs require:

`base_to_aud`

Exit legs require:

`quote_to_aud`

The required conversion factor must be a positive finite number.

An entry record must not substitute `quote_to_aud` for `base_to_aud`.

An exit record must not substitute `base_to_aud` for `quote_to_aud`.

## Provenance

`source_artifact` identifies the local evidence artifact from which the price
and conversion data were taken.

`source_artifact_sha256` records its SHA-256 digest.

The contract validator checks syntax and structure of the hash but does not
open or alter the source artifact.

## Fail-closed rules

A record is invalid if any required field is missing or malformed.

Duplicate `event_id` + `leg` records are invalid.

Unsupported pairs or legs are invalid.

Crossed, zero, negative, NaN, or infinite prices are invalid.

Missing or invalid conversion factors are invalid.

Invalid evidence must not produce an M006f replay primitive.

## Separation

This contract is prospective R&D only.

It does not modify M006e, canonical M005, accepted observation evidence,
strategy logic, sizing authority, risk authority, or capital authority.

M006f consumes only an already-created local evidence sidecar.

A configuration change alone must not create external connectivity.
