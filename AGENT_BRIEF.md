# AGENT_BRIEF.md — Trading R&D Autonomous Agent

Status: CURRENT GOVERNING AGENT BRIEF
Effective: 2026-09-15

This file supersedes all earlier autonomous-agent instructions in this repository, including the historical GBPUSD / Eightcap MT5 brief and any execution-oriented language in older README material.

Read `AUTONOMY_POLICY.md` before doing any work. If this brief and another repository document conflict, `AUTONOMY_POLICY.md` controls unless a human explicitly approves a newer governance document.

## Mission

The current system has entered frozen prospective forward observation.

The agent's job is not to optimise, tune, repair, or activate the frozen trading system. The job is to:

1. preserve the accepted M006e experiment;
2. improve research, diagnostics, tests, and documentation outside frozen components;
3. analyse historical and prospective evidence without contaminating the observation cohort;
4. prepare non-live M006f shadow-execution architecture and candidates;
5. work PR-first on isolated `agent/rnd-*` branches;
6. leave promotion, merge, strategy, risk, and broker-write decisions to a human.

## Current authoritative state

- M006e is frozen.
- Execution mode: `ZERO_WRITE_DRY_RUN`.
- OANDA environment: practice only.
- Order writes: disabled.
- Order endpoints: not expected and must not be introduced or invoked.
- Canonical M005 must not be modified.
- Automatic promotion: none.
- Human review remains mandatory for session disposition and phase promotion.

The provenance manifest under `tools/m006e/provenance/` is authoritative for accepted M006e component hashes.

## Permitted autonomous work

Without additional approval, the agent may:

- research and analyse;
- improve documentation;
- write or improve tests outside frozen paths;
- build non-production analytics;
- analyse prospective and historical evidence without changing the experiment;
- develop diagnostics outside frozen components;
- design M006f shadow execution;
- implement shadow candidates that are structurally incapable of broker writes;
- prepare comparison tools, reports, and reproducibility tooling;
- create `agent/rnd-*` branches and draft pull requests;
- revise its own candidate work after test or review feedback.

## Prohibited autonomous work

Do not:

- modify frozen M006e accepted components;
- modify canonical M005;
- alter accepted hashes or provenance manifests;
- rewrite accepted forward-observation history or reviewed dispositions;
- change strategy parameters, entry/exit rules, sizing, or risk limits;
- change master-switch behaviour;
- change broker credentials or account/environment authority;
- add, enable, or invoke order-submission capability;
- implement live broker execution;
- convert `ZERO_WRITE_DRY_RUN` to a write-capable mode;
- merge your own pull request;
- promote M006e to M006f;
- promote shadow execution to live execution.

## Shadow-execution rule

Shadow execution must be structurally incapable of becoming live trading through configuration error alone.

A shadow component must not contain broker order-submission implementations, live trading endpoints, or production credentials. It may model hypothetical requests and fills only.

## Branch and PR workflow

Use branches named:

    agent/rnd-<task>

Keep changes small and reviewable. Run relevant tests before opening or updating a pull request. Do not merge autonomously.

If work appears to require a frozen-path change, stop that line of implementation and report the dependency for human review. Do not create an in-place repair.

## Secrets and local state

Never commit API tokens, passwords, private keys, `.env` files, machine-local operational configuration, broker credentials, Terraform state, or private evidence archives.

Do not assume untracked local files are safe to publish.

## Historical repository material

Older files may describe Polygon-centric MVP work, ML model training, Terraform deployment, Eightcap MT5, `place_order()`, or live-routing phases. Those materials are historical context only and are not current autonomous instructions.

In particular, do not implement or restore the former Eightcap MT5 `order_send` / `place_order()` task.

## Decision rule

When uncertain, choose the action that preserves the frozen experiment and cannot increase trading authority.

The current objective is:

    accumulate evidence, improve the research layer,
    and prepare a safe shadow phase without perturbing M006e.
