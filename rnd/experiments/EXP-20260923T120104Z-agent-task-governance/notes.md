# Scoped agent task governance

Experiment: `EXP-20260923T120104Z-agent-task-governance`

## Question

Can new R&D tasks and review handoffs be structurally checked without
mistaking a JSON assertion for a verified human decision?

## Method

Add scoped agent instructions and a pure policy module. Check the existing
task spec, one queued event, scoped proposed paths and a hashed external
approval declaration. Keep authentication and task acceptance external. Check
RND-0020 dossier identity and authority before human review.

## Observations

RUNNING. Focused tests reject rehashed wrong approvals, self-declared agent
approval, unsafe paths, inconsistent queue state and escalated review authority.
They preserve REVIEW_REQUIRED/BLOCKED behavior and a human handoff after PASS.
No signed approval, authenticated identity or operational capability is added.
