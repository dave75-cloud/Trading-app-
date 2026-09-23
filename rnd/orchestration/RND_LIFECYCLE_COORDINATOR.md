# Governed R&D Lifecycle Coordinator

Status: R&D CANDIDATE / NON-OPERATIONAL
Task: RND-0020
Automatic merge: NONE
Automatic promotion: NONE
Human merge decision: REQUIRED

## Purpose

RND-0020 introduces a contract boundary between a human-approved R&D objective,
a future coding agent, external validation tools, and the human merge gate.

It does not execute implementation commands. It does not create branches,
pull requests, dispositions, promotions, or trading actions.

## Lifecycle

human-approved task specification
    |
    v
task-spec contract validation
    |
    v
deterministic hashed work packet
    |
    v
external coding agent / implementation process
    |
    v
candidate evidence manifest
    |
    v
deterministic evidence evaluator
    |
    v
review dossier
    |
    v
HUMAN MERGE DECISION

## Task specification

The contract requires explicit:

- task identity and exact 40-character Git base;
- objective;
- allowed R&D path prefixes;
- additional prohibited path prefixes;
- required output paths;
- required validation evidence labels;
- success criteria;
- stop conditions;
- mandatory human gate;
- automatic merge = false;
- automatic promotion = false.

Allowed implementation authority is restricted to `rnd/`.

## Work packet

Planning mode emits a deterministic content-hashed packet. It contains:

- exact task/Git identity;
- scope boundaries;
- known protected operational prefixes;
- required deliverables;
- validation labels;
- stop/success conditions;
- explicit capability denial;
- human-only merge/promotion authority.

The planner does not execute a shell or contact GitHub/network services.

## Candidate evidence

The evaluator consumes evidence created externally. It does not execute the
validation commands itself.

Candidate evidence records:

- task and Git-base identity;
- the exact work-packet hash;
- changed paths;
- output paths and SHA-256 values;
- validation labels with PASS/FAIL and evidence hashes;
- an exact fail-closed safety declaration.

## Review semantics

`PASS`

All identity, scope, required-output, validation and safety gates are satisfied.

`REVIEW_REQUIRED`

The candidate is structurally safe but required outputs or validation evidence
are incomplete. This is not permission to merge.

`FAIL_CLOSED`

Identity/provenance mismatch, protected/out-of-scope change, failed required
validation, or authority/safety expansion was detected.

Every dossier leaves human disposition unset and records merge/promotion
authority as NONE.

## Security boundary

RND-0020 contains no:

- subprocess/shell execution;
- network or GitHub API capability;
- credentials;
- broker transport;
- market-data acquisition;
- submission capability;
- strategy/risk/sizing authority;
- autonomous branch/PR creation;
- autonomous task acceptance;
- autonomous merge;
- autonomous promotion.

This task validates contracts between agents. A future R&D task would be needed
before any command-execution or external-agent invocation layer is introduced.
