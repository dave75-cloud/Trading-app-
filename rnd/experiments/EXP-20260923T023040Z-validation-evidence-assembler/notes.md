# RND-0022 — Governed validation-evidence assembler

## Research question

Can bounded machine evidence and externally attested validation evidence be
combined into one exact RND-0020 candidate-evidence object without executing
candidate code or granting broader authority?

## Candidate design

RND-0020 work packet
        |
        +-----------------------------+
        |                             |
        v                             v
RND-0021 execution evidence     external validation attestations
        |                             |
        +-------------+---------------+
                      |
                      v
        deterministic RND-0022 assembler
                      |
              +-------+-------+
              |               |
              v               v
    candidate evidence   provenance manifest
              |
              v
        RND-0020 evaluator
              |
              v
        HUMAN MERGE DECISION

## Exact-head binding

Every source artifact must bind to one exact 40-character repository HEAD.
Evidence from different candidate revisions cannot be combined.

The assembler also cross-checks the candidate changed-path manifest against
RND-0021 scope-check observations when that machine evidence is present.

## External evidence trust boundary

External validation records are attestations. RND-0022 validates:

- task/base/work-packet binding;
- exact tested HEAD;
- label and PASS/FAIL shape;
- external evidence SHA-256;
- producer identifier;
- attestation content hash.

It does not independently prove that the external runner actually executed the
test or audit.

## RND-0021 provenance verification

RND-0022 validates:

- bundle content hash;
- executor authority/capability boundary;
- execution-plan SHA-256 shape;
- every action-evidence content hash;
- exact action/validation-row agreement;
- overall PASS/FAIL consistency;
- scope-check changed-path binding.

## Validation-label policy

Only labels required by the work packet are accepted.

- duplicate or unknown labels fail closed;
- missing labels yield REVIEW_REQUIRED;
- FAIL remains FAIL and is never rewritten.

## Integration finding

While aligning RND-0022 with the merged RND-0021 implementation, review found
an internal argv inconsistency: RND-0021's safe-Git allowlist required
`--ignore-submodules=all`, while generated diff actions omitted it.

The branch corrects generated `diff-check` and `scope-check` argv to match
the already-approved allowlist and adds a regression proving every generated
action argv is accepted by that internal allowlist. This does not expand
executor authority.

## Authority boundary

RND-0022 has no subprocess, network, GitHub API, candidate-code execution, Git
mutation, broker transport/submission, automatic disposition, automatic merge
or automatic promotion authority.

## Validation state

COMPLETE as a non-operational R&D candidate. Human merge and promotion remain
external.

Final validation target:
- 65 orchestration tests;
- 106 M006f tests;
- workspace audit PASS;
- 22 tasks / 21 experiments;
- clean diff check.

## Adversarial evidence hardening

Before independent validation, review tested whether a forged JSON object could
claim to be RND-0021 evidence while carrying arbitrary argv.

RND-0022 now independently verifies:

- exact RND-0021 executor version;
- executor authority/capability declarations;
- action ID equals validation label;
- action ID is in the RND-0021 allowlist;
- exact argv equals the executor-generated argv for that action/base;
- repository-root working-directory marker;
- action content hashes and validation-row equality;
- PASS scope-check evidence cannot contain violations.

A focused regression rehashes a forged `git status` action and proves the
assembler rejects it.

Final independent validation target is now 65 orchestration tests, 106 M006f
tests, workspace audit PASS, and a clean diff check.

## Final independent validation

Exact tested code head: `be4de484ed38f2e5bb46e11c305de1a86f51ed07`.

- 65 orchestration tests passed.
- 106 M006f regression tests passed.
- `RND_WORKSPACE_AUDIT: PASS` with 22 tasks and 21 experiments.
- Broker writes and protected-path modifications: false.
- Promotion authority: human-only.
- `git diff --check agent/rnd-foundation-20260916...HEAD`: clean.

These results complete RND-0022 evidence assembly as an R&D candidate. External
validation attestations remain assertions about test execution, and the
assembler cannot independently prove that the external runner ran a test.
Human review, merge, trading-system promotion, execution and capital authority
remain external.
