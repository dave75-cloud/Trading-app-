# Prospective challenger cohort monitor

Experiment: `EXP-20260922T003643Z-challenger-prospective-monitor`

## Question

Can a fresh prospective Twelve Data versus Polygon cohort be monitored without
rewriting historical evidence, modifying canonical M005, or granting automatic
promotion authority?

## Method

A read-only monitor was built under `rnd/challenger/`.

It consumes explicit local snapshots of:

- the immutable prospective-cohort baseline;
- the provider acceptance session ledger;
- the provider acceptance pair ledger.

The monitor evaluates only sessions on or after 2026-09-22 UTC.

## Result

PASS.

Initial real snapshot:

- prospective sessions: 0 / 10
- delayed-signal disagreements: 0
- volatility-eligibility disagreements: 0
- integrity errors: 0
- automatic promotion: false
- human review required: true
- canonical M005 modified: false

Four offline tests passed:

1. empty fresh cohort;
2. ten clean sessions;
3. one disagreement blocks the requirement;
4. incomplete pair evidence fails closed.

The governed R&D workspace audit also passed.

## Governance

Historical challenger evidence remains unchanged.

No frozen M006e component, canonical M005 state, strategy parameter, risk rule,
broker authority, accepted evidence, or capital authority was modified.

Meeting the prospective evidence requirement does not promote the provider.
Human review remains mandatory.
