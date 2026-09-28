# Controlled OANDA historical acquisition and immutable sealing

Status: R&D CANDIDATE / NON-OPERATIONAL  
Task: RND-0028  
Base: `fb4686421cf93158c7dac813aa03e3fdd06ca701`

## Purpose

RND-0028 implements the acquisition boundary required by RND-0027. It makes
historical evidence acquisition reproducible without granting a generic broker
client, strategy authority or execution authority.

The committed declaration remains `UNBOUND_WINDOW`. No start/end range is
invented in this task and no network acquisition is valid until a later
human-approved declaration binds a research window.

## Pinned OANDA interface

The acquisition surface is intentionally narrow:

- environment: fxTrade Practice only;
- HTTP method: GET only;
- endpoint: account instrument candles only;
- granularity: M5;
- price components: midpoint + bid + ask (`MBA`);
- unsmoothed candles;
- complete candles only;
- no more than 5,000 M5 slots in one request;
- runtime bearer token and account identifier only.

The implementation does not expose a generic HTTP method, generic OANDA path,
live host, order endpoint, trade mutation endpoint or position-close endpoint.

## Evidence chain

Each response page is preserved as exact bytes and hashed independently.
A deterministic length-prefixed bundle digest binds page order and content.
Parsed canonical rows preserve bid, ask **and midpoint** OHLC. The canonical
row digest is independent of raw serialization.

A snapshot cannot become `SEALED` merely because pages were returned. Page
identity, response structure, complete-candle status, strict timestamp order,
overlap/duplicate checks, the declared acquisition window and an explicit gap
ledger/expected timestamp schedule must all be resolved first. Missing market
intervals are never silently forward-filled or interpolated.

## Credential boundary

The access token and practice account ID are runtime inputs. They are not
accepted as declaration fields, snapshot metadata or evidence output. Error
messages and evidence summaries must not echo either value.

## Storage boundary

A sealed acquisition package must be written outside the governed repository.
An existing target is immutable: overwrite is rejected. Corrections require a
new snapshot identity and new target.

## Midpoint provenance correction

RND-0027 required bid/ask/mid acquisition at the snapshot level but its parsed
row schema omitted midpoint OHLC. RND-0028 closes that gap: canonical rows bind
midpoint OHLC as well as bid/ask OHLC before M005 reconstruction can rely on
them.

## Reserved final test

The reserved final-test boundary remains `SEALED_BOUNDARY_UNBOUND`. RND-0028
does not bind or open it and does not permit signal generation, trade
simulation, P&L/equity metrics, parameter selection or strategy ranking.
