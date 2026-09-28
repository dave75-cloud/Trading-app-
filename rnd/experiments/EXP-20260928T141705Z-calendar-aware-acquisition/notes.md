# Calendar-aware OANDA historical acquisition quarantine

Experiment: `EXP-20260928T141705Z-calendar-aware-acquisition`

## Research boundary

RND-0030 is deliberately structural. It may acquire bid/ask/mid historical
candles and inspect timestamps, completeness, hashes and provenance. It may not
calculate M005 signals, trades or performance.

## Why quarantine exists

The ordinary OANDA FX session can be represented deterministically in
America/New_York local time, including daylight-saving transitions. Public
holidays can alter ordinary hours, however, so a generic session calendar is
not sufficient to prove exact historical completeness.

The returned candle set is therefore compared with an independently generated
ordinary-session schedule. Missing or unexpected timestamps are recorded, not
silently accepted. A discrepancy can be removed from the expected calendar
only through separately recorded official OANDA trading-hours evidence.

## Memory and interruption control

The 2015-2025 horizon is divided into ten UTC calendar-year shards per symbol.
A shard is written atomically to a new external directory. Existing shards are
never overwritten. Resume skips a shard only after verifying raw-page hashes,
aggregate bundle bytes, canonical-row digest, schedule digest and discrepancy
ledger.

The runner defaults to 0.6 seconds between page requests because the current
urllib transport is not deliberately managed as a persistent connection.

## Final-test boundary

2023-01-01T09:40:00Z through 2025-01-01T00:00:00Z remains outcome-sealed.
Acquisition and structural auditing are allowed; strategy evaluation is not.

## Current state

No historical network acquisition has yet been executed under RND-0030.

## Independent exact-head validation

Implementation HEAD `1382309a66892c4b808ac703e047fd365138df35` was independently validated in a clean
detached worktree.

- orchestration: 249 tests, OK;
- M006f: 106 tests, OK;
- workspace audit: PASS;
- tasks: 30;
- experiments: 29;
- broker writes: FALSE;
- protected paths modified: FALSE;
- promotion authority: HUMAN_ONLY;
- diff check against `baa62608d734f0562470d6b4b1bc4eeeda4aa909`: clean.

This validation completed the RND-0030 mechanism only. No OANDA historical
network acquisition was executed and no strategy outcome was calculated.
