# RND-0024 Agent Task Governance

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic task acceptance: NONE
Automatic merge or promotion: NONE

## Operator view

An agent may propose and implement a bounded R&D task under `rnd/`. You still
decide whether the task is accepted, whether its evidence is sufficient, and
whether a PR is merged. The intake check catches inconsistent paperwork and
unsafe proposed paths; a green result never impersonates your approval.

## Technical view

`rnd/AGENTS.md` tells agents how to work inside the R&D directory. The pure
`agent_task_policy.py` functions provide two structural checks:

1. `assess_task_intake(spec, events, approval, paths)` validates an RND-0020
   task spec, one queued event for this new task, normalized in-scope paths, and
   an optional content-hashed external approval declaration bound to the
   normalized task-spec hash and exact Git base. Missing approval yields
   REVIEW_REQUIRED. A consistent declaration yields DECLARATIONS_CONSISTENT,
   with `human_identity_authenticated=false` and `task_accepted=false`.
2. `assess_review_handoff(spec, dossier)` verifies the RND-0020 dossier hash,
   task/base/work-packet identity, exact fail-closed authority/capability block
   and status/flag consistency. PASS yields HUMAN_REVIEW_REQUIRED, an incomplete
   dossier yields INCOMPLETE and failed evidence yields BLOCKED. It never sets
   human disposition or merge/promotion authority.

This applies to **new** task intake; it does not rewrite old append-only task
history or forbid documented state corrections in historical streams. The
module reads supplied Python objects only. It does not read files, run Git,
launch tests, contact GitHub, append events or open a PR.

## Approval record shape

The record is a supplied JSON object with version
`RND-external-task-approval-v0.1`, task ID, exact Git base, normalized task-spec
SHA-256, decision `APPROVED`, role `HUMAN`, nonempty approver identifier, UTC
timestamp and a canonical content hash. No other keys are accepted.

This is **not** a signature or authentication mechanism. An agent could write
and rehash JSON claiming to be human. A human-controlled channel must verify
who approved and whether the decision actually occurred before any task state
change. The policy's consistent result is only evidence for that external
decision. Never use it as an autonomous acceptance signal.

## Why the two checks differ

Intake answers whether proposed work is scoped and its supplied declarations
match. Handoff answers whether an existing machine dossier is structurally fit
to place before a person. Neither answers whether the evidence is true or a
trading candidate should advance. That separation is what lets repetitive
checks be automated while the human retains consequential decisions.

## Safety

No new subprocess, network, GitHub API, candidate-code, broker, order,
strategy/risk/sizing, automatic disposition, merge, promotion or capital
authority. Frozen M006e, canonical M005 and the operational observation stack
remain unchanged. Existing workspace audit, tests, GitHub guard and human review
stay in force; an instruction file is not a security boundary.
