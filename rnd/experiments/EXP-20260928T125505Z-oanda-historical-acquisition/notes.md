# Controlled OANDA historical acquisition and immutable sealing

Experiment: `EXP-20260928T125505Z-oanda-historical-acquisition`

## Question

Can the project admit real historical M5 evidence through a narrowly scoped,
read-only OANDA Practice interface while preserving the no-write authority
boundary and the RND-0027 reserved-test seal?

## Method

Implement an exact practice-host/account-instrument-candles request surface,
deterministic <=5000-slot chunking, complete bid/ask/mid response parsing,
page-level and aggregate raw hashing, canonical parsed-row hashing, explicit gap
evidence, immutable external storage guards and runtime-only credentials.

RND-0028 also closes the RND-0027 parsed-row provenance gap by requiring
midpoint OHLC in canonical rows, not merely in the snapshot-level component
declaration.

## Boundary

The committed acquisition declaration remains `UNBOUND_WINDOW`. Therefore the
runner fails closed before any network call until a later human-approved
declaration binds a research window. The reserved final-test boundary remains
`SEALED_BOUNDARY_UNBOUND`.

No historical strategy result, M005 signal, trade simulation, P&L/equity
metric, parameter search, strategy ranking, broker write, capital authority,
automatic promotion or automatic merge is part of this experiment.
