# RND-0021 Controlled Local R&D Executor

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic merge: NONE
Automatic promotion: NONE
Human merge decision: REQUIRED

## Purpose

RND-0021 adds the first bounded execution layer beneath the RND-0020 lifecycle
coordinator.

The executor turns an already validated RND-0020 work packet into a hashed
execution plan, runs only a tiny read-only Git allowlist, and emits immutable
validation evidence that RND-0020 can consume.

## Security refinement

A hard-coded unit-test command still executes candidate-controlled Python.
Therefore RND-0021 v1 deliberately does not run:

- unit tests;
- candidate Python modules;
- repository scripts;
- package installers;
- arbitrary interpreters;
- shell fragments.

Those remain external validation evidence until a separately reviewed OS-level
sandbox exists.

## Allowlisted actions

Exactly two action IDs exist:

- `diff-check`
  - commit-to-commit `git diff --check` from the exact work-packet base to HEAD;
  - external diff, text conversion and submodule worktree inspection are disabled.

- `scope-check`
  - commit-to-commit changed-path discovery from the exact base to HEAD;
  - external diff, text conversion and submodule worktree inspection are disabled;
  - paths are compared with work-packet allowed, prohibited and protected
    prefixes.

Worktree status is deliberately excluded. On older Git versions, repository
configuration such as `core.fsmonitor` can cause a status/index refresh to
invoke an external helper. Worktree cleanliness therefore remains external
validation evidence rather than executor authority.

No caller supplies an executable, argv array, working directory or shell text.

## Two-stage execution

1. `plan`
   - validates the RND-0020 work packet;
   - accepts only allowlisted action IDs already authorized by the work packet;
   - sorts them deterministically;
   - emits a content-hashed execution plan.

2. `execute`
   - verifies the work packet and execution-plan hashes;
   - proves the work-packet Git base is an ancestor of local HEAD;
   - runs the fixed action argv with `shell=False`;
   - writes hashed evidence;
   - refuses evidence overwrite.

## Process boundary

Every child process:

- is `/usr/bin/git`;
- uses one exact approved read-only argv shape;
- runs from the repository root;
- receives a small sanitized environment;
- receives stdin from the null device;
- has external diff and text conversion disabled where applicable;
- has a fixed timeout;
- captures stdout/stderr to temporary files before hashing.

Git mutation commands are not in the allowlist and are rejected before
`subprocess.run`.

## Evidence

Each action records:

- action ID / validation label;
- exact argv;
- fixed working-directory label;
- exit code and timeout state;
- PASS / FAIL;
- SHA-256 and byte count for stdout;
- SHA-256 and byte count for stderr;
- bounded previews;
- action-evidence SHA-256;
- scope observations where applicable.

The bundle also records:

- task ID;
- exact work-packet Git base;
- local repository HEAD;
- work-packet content hash;
- execution-plan content hash;
- overall PASS / FAIL;
- RND-0020-compatible validation records;
- executor capability and authority declarations;
- execution-evidence content hash.

## Authority

RND-0021 has no:

- network capability;
- GitHub API capability;
- broker transport;
- submission capability;
- candidate-code execution;
- arbitrary subprocess capability;
- shell capability;
- automatic disposition;
- automatic merge;
- automatic promotion;
- merge or promotion authority.

The only subprocess authority is the fixed read-only Git allowlist above.

## Deliberate next boundary

Autonomous unit-test execution is not part of RND-0021. Candidate code can only
be run safely after a later task establishes an actual operating-system sandbox
with independently reviewed network and filesystem restrictions.
