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
