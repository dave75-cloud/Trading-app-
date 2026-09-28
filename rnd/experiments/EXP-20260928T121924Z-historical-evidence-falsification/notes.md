# Controlled reconstruction and falsification of historical trading evidence

Experiment: `EXP-20260928T121924Z-historical-evidence-falsification`

## Question

What historical Champion/M005 claims survive the RND-0025 research standard,
and which claims fail because evidence is missing or legacy methodology can
bias the result?

## Method

Inventory surviving code and explicitly probe missing Champion inputs. Preserve
Git blob identities for source evidence. Separate behavioural reproducibility
from performance reproducibility. Add pure-local falsification helpers for
one-sided clipping, chronological contamination, overlapping-trade portfolio
limitations, ambiguous OHLC stop/target bars, and the M005 performance-evidence
gate.

## Initial finding

The Champion recipe survives but its sized trade logs and final portfolio CSV
are absent from the governed foundation. M005 behavioural semantics are
independently preserved, while an execution-grade historical performance
declaration is blocked by missing bid/ask snapshot identity, untouched final
test provenance, complete trial accounting and accepted mark-to-market
reconstruction evidence.

Independent exact-head validation remains required.

## Independent validation

Validated candidate HEAD: `b9c21feb892457475f5bcf71a6307fe32e641bf4`.

A clean detached worktree independently reported:

- exact HEAD matched the candidate;
- workspace status clean;
- orchestration: 112 tests, PASS;
- M006f: 106 tests, PASS;
- R&D workspace audit: PASS with 26 tasks and 25 experiments;
- broker writes: FALSE;
- protected paths modified: FALSE;
- promotion authority: HUMAN_ONLY;
- diff check against `2a493bd0b09f4bd357a8696405d88cd8ab3dc28f`: clean.

GitHub safeguards on that exact candidate HEAD also completed successfully:
Current System Validation and Autonomous R&D Guard.

Completion bookkeeping is records-only. It does not change the validated
research implementation, M005/M006e operational code, strategy/risk/sizing
authority, promotion authority or broker-write capability. Merge remains a
separate human decision.
