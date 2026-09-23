# R&D agent instructions

These instructions apply only under `rnd/`. The operational trading stack is
frozen in forward observation. Treat its files and accepted evidence as
read-only context.

## Authority and roles

- A human approves objectives, accepts tasks, reviews evidence, decides PR
  merges and authorizes any promotion, strategy/risk/sizing change, execution or
  capital use. An agent must not infer those decisions from a machine PASS.
- A planning or coding agent may propose scoped R&D work, create a branch and
  draft PR, implement under `rnd/`, and report tests and audit results. It must
  not self-approve its task, claim human identity, or merge its own PR.
- External test/audit attestations are claims supplied by an independently
  controlled process. Their hashes and bindings do not prove execution truth.
- A reviewer may critique implementation and evidence. A reviewer report is
  not a human disposition or promotion authority.

## Before and during a task

1. Use an explicit RND task spec and exact Git base. Check the allowed and
   prohibited path prefixes, required outputs, validation labels, success
   criteria and stop conditions before implementation.
2. Keep all changes under `rnd/`. Do not modify frozen M006e, canonical M005,
   accepted manifests, operational configuration, strategy/risk/sizing, broker
   credentials, master switch, order capability, or protected paths.
3. Keep task and experiment histories append-only. Preserve unrelated dirty or
   untracked files. Never invent, backfill, drop or rewrite failed evidence.
4. Stop and surface a mismatch, absent approval, failed validation, unsafe
   path, exceeded task scope or evidence tied to another candidate HEAD.
5. Tests/audits of candidate Python require an external human-controlled
   process until a separately reviewed OS sandbox exists. RND-0021 itself may
   execute only its two fixed read-only Git actions.

## Handoff

Provide the exact candidate HEAD, changed paths, output hashes, validation
results, audit result, provenance and unresolved flags in a draft PR. A machine
PASS means structurally reviewable evidence; it never authorizes merge or
promotion. Wait for explicit human review and merge authorization.

These instructions guide agents; they do not authenticate a human, sandbox a
process, or enforce repository permissions. The task-spec validator, workspace
audit, tests, repository controls and human gate remain separate checks.
