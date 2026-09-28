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
snapshots under a separate controlled gate.

## Independent exact-head validation

Implementation HEAD `10aa418306e53ffef7a630936079f2fb347e5af0` was independently
validated in a clean detached worktree against foundation
`09f839920a0bf7bede40d8e346ca6c7fcba02cc8`:

- `git status --short`: clean;
- orchestration: 138 tests, OK;
- M006f: 106 tests, OK;
- workspace audit: PASS; tasks=27; experiments=26; broker_writes=FALSE;
  protected_paths_modified=FALSE; promotion_authority=HUMAN_ONLY;
- `git diff --check`: clean.

An earlier candidate correctly failed the workspace audit because its manifest
contained an extra safety-declaration field. The audit was not weakened; the
redundant field was removed and the corrected exact implementation HEAD above
was revalidated successfully.

Completion bookkeeping records this validation only. It does not acquire
historical data, open the reserved final test, evaluate M005 performance,
change strategy/risk/sizing authority, or authorize merge/promotion.
