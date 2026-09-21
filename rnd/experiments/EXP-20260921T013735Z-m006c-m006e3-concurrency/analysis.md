# RND-0004 — M006c/M006e.3 Concurrency-Race Design Analysis

## Finding

The 17 September failure is consistent with a scheduler/concurrency-contract
mismatch.

M006e.3 snapshots the M006c state hash before its processing window and compares
that hash again near the end of the run. During the incident, an independently
scheduled M006c process changed that state. M006e.3 detected the change and
failed closed.

The reviewed incident evidence records zero trading writes and no safety
violation. The fail-close protection therefore operated as intended.

## Candidate controls

### Scheduler serialization — preferred

Place M006c and M006e.3 under one sequencing authority so their state-sensitive
execution windows cannot overlap.

Advantages:

- prevents the observed race by construction;
- preserves the existing M006e.3 integrity check;
- does not require changing M006e.3 decision or safety logic;
- does not rely on estimated runtime or clock spacing.

This is the preferred post-observation design candidate.

### Shared mutual-exclusion lock

Require M006c and M006e.3 to acquire the same lock around state-sensitive
activity.

This also prevents overlap by construction, but both execution paths must
correctly participate and stale-lock handling becomes an additional mechanism
requiring validation.

This is the preferred fallback if centralized sequencing is unavailable.

### Schedule deconfliction

Offset the independent schedules so executions normally occur at different
times.

This reduces collision probability but cannot eliminate the race. Runtime
variation, retries, host load or delayed starts can recreate the overlap.

It should not be the primary long-term control.

### Weaken the hash-integrity check

Rejected.

The before/after hash comparison is the control that detected the unexpected
concurrent state change. Weakening it would remove evidence of the race rather
than fixing the race itself.

## Recommendation

After frozen forward observation is complete, prototype scheduler serialization
outside the accepted stack.

Retain the existing M006e.3 before/after hash comparison as a secondary
fail-closed integrity defence even after serialization is introduced.

## Authority

This is design-only R&D.

It does not authorize modification of M006e, M006c, M005, strategy parameters,
risk sizing, broker execution, promotion, or capital deployment.
