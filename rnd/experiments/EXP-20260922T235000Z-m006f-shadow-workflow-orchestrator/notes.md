# RND-0019 — Bounded prospective shadow-workflow orchestrator

## Research question

Can the accepted-session evidence-selection step be automated without granting
the agent discretion to invent evidence, resolve ambiguity, create a human
disposition, update reviewed ledgers, or promote a trading system?

## Candidate design

The candidate performs deterministic local discovery over explicit read-only
roots. It selects only one eligible, unprocessed session and delegates all
downstream replay, simulation, packaging and dossier creation to RND-0018.

Zero eligible sessions and multiple eligible sessions are stop conditions.

## Safety boundary

- offline local files only;
- source observation evidence remains read-only;
- no market-data acquisition;
- no credential handling;
- no broker transport;
- no submission capability;
- no automatic human disposition;
- no reviewed-ledger update;
- no cumulative-monitor update;
- no automatic promotion;
- promotion authority remains NONE.

## Validation status

RUNNING.

Implementation and focused tests have been added to the dedicated RND-0019
branch. The experiment must not be marked complete until the exact branch head
passes the focused orchestrator suite, full M006f suite, workspace audit and
diff checks.
