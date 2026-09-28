# Immutable historical data and controlled M005 reconstruction

Experiment: `EXP-20260928T124200Z-historical-data-m005-reconstruction`

## Question

Can the project move from behavioural M005 reproducibility toward a defensible
historical reconstruction without fabricating absent data, tuning the frozen
strategy, or leaking information from a future reserved final test?

## Method

Define an execution-grade immutable snapshot contract, an explicit acquisition
plan whose four required pair snapshots remain MISSING, a fixed M005
reconstruction declaration, and pure-local validators for snapshot identity,
SHA-256 integrity, bid/ask presence, complete candles, timestamp structure,
reserved-test access and authority boundaries.

## Important boundary

RND-0027 does not claim that historical data have been acquired. The reserved
final-test date boundary is deliberately `SEALED_BOUNDARY_UNBOUND`: strategy
metrics and signals are prohibited, and even the date boundary cannot be
silently inserted into the RND-0027 declaration.

The next evidence step is acquisition/binding of immutable read-only historical
snapshots under a separate controlled gate. Independent exact-head validation
of this candidate remains required.
