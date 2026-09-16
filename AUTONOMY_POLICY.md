# Trading R&D Autonomous Authority Policy

Status: GOVERNANCE
Effective: 2026-09-15

## Purpose

This repository may be used for autonomous research and development,
but operational trading authority remains deliberately human-gated.

The current M006e system is in frozen prospective forward observation.
Autonomous work must not alter that experiment.

## Permitted without prior approval

An autonomous agent may:

- perform research and analysis;
- improve documentation;
- design and implement tests;
- analyse historical and prospective evidence;
- develop diagnostic and reporting tools outside frozen components;
- design M006f shadow execution;
- develop non-live shadow-execution candidates;
- prepare analytics and research tooling;
- create candidate branches;
- create draft pull requests;
- revise its own candidate work after tests or review;
- inspect frozen components for context without modifying them.

## Frozen / prohibited paths and authorities

An autonomous agent must not modify or bypass:

- frozen M006e accepted operational components;
- canonical M005;
- accepted provenance manifests;
- accepted hashes;
- forward-observation historical evidence;
- reviewed session dispositions;
- strategy parameters;
- entry or exit rules;
- risk parameters;
- position-sizing rules;
- master-switch behaviour;
- broker credentials;
- broker environment selection;
- live or practice account authority;
- order-submission capability;
- order endpoints;
- production configuration.

## Execution prohibition

Autonomous work must never:

- place a broker order;
- enable broker writes;
- add or activate production execution;
- change ZERO_WRITE_DRY_RUN into write-capable operation;
- promote M006e to M006f;
- promote shadow execution to live execution;
- merge its own pull request.

Shadow-execution work must remain structurally incapable of becoming
live trading through configuration change alone.

## Human gates

Human approval remains mandatory for:

1. pre-session GO / NO-GO;
2. classification of anomalous forward-observation sessions;
3. reviewed session disposition;
4. strategy or risk changes;
5. accepted-stack changes;
6. pull-request merge;
7. M006e -> M006f promotion;
8. any future broker-write or live-execution decision.

## Repository workflow

Autonomous engineering must be PR-first.

Preferred branch pattern:

    agent/rnd-<task>

Candidate work must remain outside frozen source paths unless a human
has explicitly authorised creation of a new versioned candidate.

No autonomous process may overwrite accepted evidence or immutable
historical snapshots.

## Secrets

Never commit:

- API tokens;
- account identifiers where unnecessary;
- passwords;
- private keys;
- .env files;
- machine-local operational configuration;
- broker credentials;
- Terraform state;
- private evidence archives.

## Current experiment

M006e is frozen.

The correct autonomous objective during forward observation is:

    accumulate evidence, build the next safe research layer,
    and prepare shadow-phase candidates without perturbing M006e.


## Canonical M005 boundary

Canonical M005 runtime root:

    data/research_runs/M005_FORWARD_SHADOW_20260804T120245Z/

This runtime tree is machine-local operational state and must not be
modified, rewritten, reinitialised, or repurposed by autonomous R&D.

The following tracked operational source paths are protected from
autonomous modification:

    cli/generate_m005_frozen_signals.py
    cli/capture_m005_signals.py
    cli/check_m005_live_bar_gate.py
    cli/init_m005_shadow.py
    cli/update_m005_polygon_bars.py
    cli/build_m005_provider_acceptance_ledger.py
    cli/update_m005_twelve_data_bars.py
    cli/run_m005_twelve_shadow_observer.py
    run_m005_delayed_reconciliation.sh
    run_m005_twelve_shadow_candidate.sh

These paths may be inspected for context but must not be altered on
agent/rnd-* branches. Any human-authorized successor must be created as a
distinct versioned candidate outside the protected paths.
