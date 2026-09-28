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

## Independent exact-head validation

Corrected implementation HEAD `35ccb3affaa685a1bebe3c490bf6853420f0e0ca` was
independently validated in a clean detached worktree against foundation
`fb4686421cf93158c7dac813aa03e3fdd06ca701`:

- `git status --short`: clean;
- orchestration: 175 tests, OK;
- M006f: 106 tests, OK;
- workspace audit: PASS; tasks=28; experiments=27; broker_writes=FALSE;
  protected_paths_modified=FALSE; promotion_authority=HUMAN_ONLY;
- `git diff --check`: clean.

The first candidate `4db3af6881a7fffec97cad6b7290d54f501569e0`
correctly failed independent validation with 16 orchestration errors caused by
missing `Decimal` / `InvalidOperation` imports and two trailing-whitespace
findings. No completion records were written for that candidate. The corrected
implementation imported the dependencies, added a provider-decimal-string
regression, removed the whitespace defects, and was then revalidated at the
exact HEAD above.

Completion bookkeeping records this validation only. It does not bind an
acquisition window, perform historical network acquisition, open the reserved
final test, evaluate M005 performance, change strategy/risk/sizing or capital
authority, or authorize merge/promotion.
