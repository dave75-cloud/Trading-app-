# M006f Cumulative Shadow-Observation Monitor

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic promotion: NONE
Human promotion decision: REQUIRED

## Purpose

This monitor sits above the human-reviewed M006f session ledger.

It independently verifies the cumulative ledger and reports quantitative
shadow-observation evidence.

It does not make a promotion, graduation or execution decision.

## Evidence thresholds

The provisional M006f shadow-validation protocol requires at least:

- 25 human-accepted shadow sessions; and
- 100 replay events contained in human-accepted sessions.

Both thresholds are descriptive minimum evidence requirements only.

Reaching them does not authorize promotion.

## Accepted cohort

For evidence-progress purposes, the accepted cohort contains sessions whose
explicit human disposition is:

- ACCEPTED; or
- ACCEPTED_WITH_REVIEW.

REJECTED sessions remain visible in reviewed-session totals but do not count
toward the accepted-session or accepted-event thresholds.

## Independent verification

Before reporting progress, the monitor independently verifies:

- ledger version;
- ledger-content SHA-256;
- reviewed-cohort flag;
- safety and authority fields;
- unique session IDs;
- disposition vocabulary;
- cumulative counts against the underlying session records;
- review-flag aggregation;
- realized-P&L aggregation;
- final-equity observation sequence.

It fails closed on inconsistency.

## Reported evidence

The monitor reports:

- reviewed sessions;
- accepted sessions;
- rejected sessions;
- accepted replay events;
- accepted market-evidence records;
- accepted suppressed chains;
- accepted sessions ending with open positions;
- accepted review-flag counts;
- progress toward 25 accepted sessions;
- progress toward 100 accepted replay events.

It separately reports whether the numerical thresholds have been reached.

## Evidence quality

Threshold counts are not treated as sufficient evidence by themselves.

The monitor also reports:

- whether accepted sessions contain suppressed chains;
- whether accepted sessions end with open positions;
- whether accepted sessions contain review flags.

These facts remain subject to human interpretation.

## Prohibited semantics

The monitor must not output or infer:

- a promotion decision;
- a live-trading decision;
- execution authority;
- capital authority;
- an automatic disposition.

Numerical thresholds being reached must never be represented as automatic
permission to proceed.

## Determinism

The monitor contains no runtime timestamp.

Identical ledger bytes produce identical monitor content and an identical
monitor-content SHA-256.

## Governance

This component is local, offline and R&D-only.

It does not modify M006e.
It does not modify canonical M005.
It has no network capability.
It has no submission capability.
Human promotion authority remains external to the tool.
