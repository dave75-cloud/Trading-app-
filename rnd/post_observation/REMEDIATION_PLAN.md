# Post-Observation Remediation Package

Status: DESIGN ONLY  
Deployment authority: NONE

This package records three known engineering issues discovered during frozen
forward observation. It deliberately contains no in-place patch to an accepted
component.

## A. Reconciliation validation-row linkage

Observed issue: the reconciliation loader can read `validation_rows` as though
it were the row collection, while the validator report uses that field as a
count and stores the actual collection in `rows`.

Post-observation candidate behaviour:

1. read `rows` when it is a list;
2. treat `validation_rows` only as a count;
3. fail closed on contradictory count versus list length;
4. regression-test entry, exit and two-leg reversal reports;
5. preserve old evidence unchanged.

Acceptance test: a report with `validation_rows=2` and two list entries must
produce two linked validation rows.

## B. Provider diagnostic file selection

Observed issue: lexicographic selection can prefer an older all-history file
over the current day-specific diagnostic.

Post-observation candidate behaviour:

1. inspect report metadata, not filename ordering alone;
2. require an exact target day match;
3. reject multiple equally-current candidates unless hashes/contents agree;
4. fail closed when no target-day diagnostic exists.

Acceptance test: when an older all-history file and current day file coexist,
the current target-day evidence must be selected.

## C. M006c / M006e.3 concurrency

Observed issue: an independent state writer can mutate M006c state inside the
M006e.3 before/after hash window.

Preferred candidate: scheduler serialization.

Required properties:

- one sequencing authority for both state-sensitive stages;
- no overlapping critical windows;
- preserve M006e.3 before/after integrity comparison;
- retain fail-closed behaviour;
- record start/end timestamps and sequence IDs;
- test delayed starts, long runtimes and retries.

Fallback: a shared mutual-exclusion protocol with explicit stale-lock recovery.

Schedule spacing alone is not an adequate primary control.

## Remediation order

1. build candidates outside protected paths;
2. unit and failure-injection tests;
3. frozen-evidence replay;
4. human review;
5. only after forward observation is formally ended, create versioned successor
   components;
6. never rewrite accepted historical evidence.

No remediation in this package is authorized for deployment.
