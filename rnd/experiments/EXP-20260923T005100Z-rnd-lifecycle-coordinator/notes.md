# RND-0020 — Governed R&D lifecycle coordinator

## Research question

Can a planner/evaluator layer coordinate autonomous R&D work without itself
receiving code-execution, network, merge, promotion or trading authority?

## Candidate architecture

human-approved task specification
    |
    v
contract validation
    |
    v
deterministic hashed work packet
    |
    v
external coding agent / implementation process
    |
    v
externally produced candidate evidence
    |
    v
deterministic evaluator
    |
    v
review dossier
    |
    v
HUMAN MERGE DECISION

## Planning boundary

Planning mode validates a local task specification and emits one deterministic
content-hashed work packet. It does not execute shell commands, create branches
or PRs, contact external services, or modify task status.

## Evaluation boundary

Evaluation mode verifies:

- task identity and exact Git base;
- work-packet binding to the original task specification;
- changed-path scope and protected-path exclusions;
- required output declarations and hashes;
- required validation evidence labels and PASS/FAIL results;
- exact fail-closed safety declarations.

Missing required outputs or validation evidence yield REVIEW_REQUIRED.
Identity, scope, protected-path, failed-validation or safety violations yield
FAIL_CLOSED.

## Security hardening

All task and candidate repository paths are normalized and reject absolute,
backslash, dot or dot-dot traversal forms before scope evaluation.

Allowed task authority is restricted to paths under rnd/.

## Authority boundary

The candidate has:

- network capability: false;
- subprocess capability: false;
- GitHub API capability: false;
- broker transport: false;
- submission capability: false;
- automatic disposition: false;
- automatic merge: false;
- automatic promotion: false;
- merge authority: NONE;
- promotion authority: NONE;
- human review required: true.

## Validation state

RUNNING.

RND-0020 must not be marked complete until the exact branch head passes the
focused orchestration tests, the existing M006f suite, the R&D workspace audit,
and diff checks.
