# RND-0021 — Controlled local R&D work-packet executor

## Research question

Can the R&D system execute useful validation actions autonomously without
turning the executor into a general shell or granting candidate code hidden
network/process/filesystem authority?

## Security finding

A hard-coded unit-test command still executes candidate-controlled Python.
RND-0021 therefore excludes candidate Python and repository-script execution
from its authority.

The v1 subprocess boundary is restricted to internally constructed, read-only
`/usr/bin/git` argv only.

## Candidate design

RND-0020 work packet
    |
    v
deterministic action-ID selection
    |
    v
hashed execution plan
    |
    v
read-only Git allowlist
    |
    v
hashed execution evidence
    |
    v
RND-0020 evaluator
    |
    v
HUMAN MERGE DECISION

## Allowlisted actions

- `diff-check`
- `scope-check`
- `worktree-clean-check`

The caller cannot provide executables, argv arrays, shell text, working
directories, network targets, or Git mutation commands.

## Process hardening

- executable fixed to `/usr/bin/git`;
- `shell=False`;
- repository-root working directory fixed in code;
- stdin disconnected;
- sanitized environment;
- external diff/text conversion disabled;
- fixed timeout;
- stdout/stderr captured to temporary files then hashed;
- non-allowlisted argv rejected before subprocess invocation.

## Evidence

Execution evidence binds:

- task and Git-base identity;
- repository HEAD;
- work-packet hash;
- execution-plan hash;
- exact argv and exit code for each action;
- stdout/stderr hashes and bounded previews;
- scope/worktree observations;
- action evidence hashes;
- RND-0020-compatible validation rows;
- human-only authority declarations;
- bundle content hash.

## Authority boundary

- candidate-code execution: false;
- arbitrary subprocess: false;
- network: false;
- GitHub API: false;
- broker transport/submission: false;
- shell: false;
- automatic disposition: false;
- automatic merge: false;
- automatic promotion: false;
- merge/promotion authority: NONE.

## Validation state

RUNNING.

RND-0021 must not be marked complete until the exact branch head passes the
focused orchestration suite, existing M006f suite, workspace audit, and diff
check.
## Initial independent validation finding

The first independent run passed 40 of 41 orchestration tests, all 106 M006f
tests, the workspace audit, and the diff check.

The single failure was an integration-test setup error: the test built a work
packet authorized for all three executor labels, then asked RND-0020 to evaluate
that packet against a task specification containing only two labels. RND-0020
correctly rejected the provenance mismatch.

The test was corrected so the same task specification is used to build the work
packet and to evaluate the resulting candidate evidence. No executor runtime
logic changed. RND-0021 remains RUNNING pending re-validation of the corrected
head.
