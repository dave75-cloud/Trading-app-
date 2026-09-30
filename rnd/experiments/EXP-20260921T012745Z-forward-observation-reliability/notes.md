# Forward-observation reliability analysis

Experiment: `EXP-20260921T012745Z-forward-observation-reliability`

## Question

Do the recorded forward-observation failures through 17 September 2026 show unexplained safety failures, or are they accounted for by contained operational/provider causes?

## Method

The experiment used read-only copies of the immutable cumulative ledger, session CSV, formal report, and available reviewed dispositions. `analyze_reliability.py` derived cycle totals, coverage, failure taxonomy, event counts, integrity status, and source hashes entirely offline.

## Result

- 9 accepted sessions from 9 observed session records.
- 339 of 387 expected cycles observed (87.60%).
- 329 PASS and 10 FAIL cycles.
- 9 contained upstream/provider failures.
- 1 contained local concurrency/state-race failure.
- 0 unclassified raw failures.
- 17 authoritative events, all represented in provider-path and reconciliation evidence.
- 0 recorded safety violations.
- 0 M006e.2 hash-failure sessions.
- One sub-80% coverage session: 14 September at 74.4%.

## Interpretation

Within the copied evidence, the recorded FAIL cycles are fully accounted for by contained operational causes. This supports a reliability/infrastructure classification rather than a recorded execution-safety breach. Missing or unobserved cycles remain an availability concern and are not treated as safety failures without additional evidence.

This experiment does not assess profitability, strategy quality, parameter selection, promotion readiness, or live-trading suitability.

## Governance

The analysis was offline and confined to `rnd/`. Frozen M005/M006e files were not modified. No broker-write, execution, promotion, strategy, sizing, or capital authority is conferred.
