# Autonomous R&D Framework

Status: CANDIDATE / NON-OPERATIONAL

This framework coordinates autonomous research without conferring trading authority.

## Core invariants

1. Autonomous work stays outside protected operational paths.
2. Research is reproducible from explicit inputs, commands, outputs, and Git base.
3. Task and experiment histories use append-only JSONL event streams.
4. Experiments fail closed when required metadata or safety declarations are missing.
5. No experiment may claim promotion, broker-write, or capital authority.
6. Human review remains mandatory before accepted-stack or phase changes.
7. Frozen observation evidence is read-only context, never scratch space.

## Task states

`queued`, `running`, `blocked`, `complete`, `cancelled`

Task history is recorded in `queue/task_events.jsonl`. New events are appended rather
than rewriting earlier events.

## Experiment states

`planned`, `running`, `complete`, `rejected`, `archived`

Each experiment lives under `experiments/EXP-YYYYMMDDTHHMMSSZ-<slug>/` with a
`manifest.json` and `notes.md`. History is appended to
`registry/experiment_events.jsonl`.

## Evidence standard

A completed experiment should identify the research question, exact Git base, inputs,
commands, outputs, observed result, and its safety declarations.

## Tooling

`tools/new_experiment.py` creates a new offline experiment skeleton.
`tools/audit_workspace.py` performs an offline structural and safety audit.

Neither tool contains broker, credential, account, market-data, or network access.
