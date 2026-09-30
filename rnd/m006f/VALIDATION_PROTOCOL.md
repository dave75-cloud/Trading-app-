# M006f Shadow Validation Protocol

Status: CANDIDATE PROTOCOL  
Automatic promotion: NONE

## Objective

Determine whether the M006f shadow layer is reliable, deterministic and useful
enough for a human to consider a later phase. This protocol does not authorize
broker execution.

## Entry conditions

Before a shadow observation cohort begins:

- frozen forward-observation review has authorized the transition;
- exact M006f source hashes are recorded;
- offline unit and replay tests pass;
- broker transport is absent;
- network capability is absent;
- submission capability is absent;
- accepted decision input schema is frozen;
- shadow fill assumptions are frozen;
- starting equity/accounting conventions are frozen.

## Minimum evidence floor

Collect at least:

- 25 accepted shadow sessions; and
- 100 accepted shadow events.

Both requirements must be met. The longer requirement governs. These are
minimum review thresholds, not automatic graduation.

## Hard gates

All must remain true:

- zero broker-write capability;
- zero unexplained duplicate event IDs;
- zero unexplained event omissions;
- zero ledger corruption;
- zero unexplained replay divergence;
- exact source integrity maintained;
- all reversals decomposed into exit then entry;
- all accounting conversions explicit and positive;
- all blocked events carry a reason;
- no dependency from M006e back to M006f.

Any hard-gate failure requires human review and normally extends or rejects the
candidate.

## Determinism gate

For an identical input file and frozen configuration:

- output input hash must match;
- per-event fills must match;
- realized P&L must match;
- final equity must match;
- maximum drawdown must match;
- final positions must match.

Expected replay agreement: 100%.

## Coverage and reconciliation

For every accepted upstream action, shadow processing must classify it as one
of:

- modelled;
- intentionally blocked by frozen shadow validation rules;
- explicitly unavailable because required local evidence was missing.

Unexplained disappearance is not acceptable.

## Metrics to report

Report without tuning:

- event count;
- entry/exit counts;
- per-pair counts;
- modeled spread cost;
- modeled slippage cost;
- realized shadow P&L;
- equity path;
- maximum drawdown;
- maximum gross nominal AUD exposure;
- open-position duration where derivable;
- failure/blocked reasons;
- replay consistency.

Profitability is evidence, not a promotion rule.

## Review outcomes

At the end of the minimum cohort, the dossier must present evidence for a human
to choose one of:

- continue shadow observation;
- reject/reengineer shadow layer;
- authorize design work for a later controlled practice-only phase.

The system itself must not choose among these outcomes.
