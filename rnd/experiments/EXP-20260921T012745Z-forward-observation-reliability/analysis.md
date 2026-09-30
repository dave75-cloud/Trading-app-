# RND-0003 — Forward-Observation Reliability Analysis

Observation through: 2026-09-17

## Derived results

- Accepted sessions: 9/9
- Cycles observed: 339/387 (87.60%)
- Missing/unobserved cycles: 48
- PASS / FAIL / SKIP / UNKNOWN: 329 / 10 / 0 / 0
- Contained upstream failures: 9
- Contained local concurrency/state-race failures: 1
- Unclassified raw failures after taxonomy: 0
- Authoritative events: 17
- Provider-path events: 17
- Reconciliation events: 17
- Recorded safety violations: 0
- M006e.2 hash-failure sessions: 0

## Failure sessions

- 2026-09-08: 2 raw FAIL cycle(s), 2 classified upstream; reviewed disposition `ACCEPTED_WITH_CONTAINED_UPSTREAM_FAILURES`.
- 2026-09-09: 3 raw FAIL cycle(s), 3 classified upstream; reviewed disposition `ACCEPTED_WITH_CONTAINED_UPSTREAM_FAILURES`.
- 2026-09-11: 2 raw FAIL cycle(s), 2 classified upstream; reviewed disposition `ACCEPTED_WITH_CONTAINED_UPSTREAM_FAILURES`.
- 2026-09-16: 1 raw FAIL cycle(s), 1 classified upstream; reviewed disposition `CLEAN`.
- 2026-09-17: 2 raw FAIL cycle(s), 1 classified upstream; reviewed disposition `ACCEPTED_WITH_CONTAINED_FAILURES`.

## Coverage warnings

- 2026-09-14: 74.4% coverage (`ACCEPTED_WITH_COVERAGE_WARNING`).

## Interpretation

- All 10 recorded raw FAIL cycles are accounted for by the derived taxonomy: 9 contained upstream/provider failures plus 1 contained local concurrency failure.
- The copied evidence records zero safety violations and no M006e.2 integrity failures.
- The evidence therefore supports an operational-reliability/infrastructure issue classification rather than a recorded execution-safety breach.
- Coverage loss remains a separate availability concern and should not be reclassified as a safety defect without additional evidence.
- This analysis makes no claim about strategy profitability, parameter quality, promotion, or live-trading suitability.

## Governance

- Analysis is offline and derived only from copied immutable evidence.
- Frozen M005/M006e components were not modified.
- No strategy, sizing, broker-write, promotion, or capital authority is conferred.
