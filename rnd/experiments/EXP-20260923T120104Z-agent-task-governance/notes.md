# Scoped agent task governance

Experiment: `EXP-20260923T120104Z-agent-task-governance`

## Question

Can new R&D tasks and review handoffs be structurally checked without
mistaking a JSON assertion for a verified human decision?

## Method

Add scoped agent instructions and a pure policy module. Check the existing
task spec, one queued event, scoped proposed paths and a hashed external
approval declaration. Keep authentication and task acceptance external. Check
RND-0020 dossier identity and authority before human review.

## Observations

RUNNING. Focused tests reject rehashed wrong approvals, self-declared agent
approval, unsafe paths, inconsistent queue state and escalated review authority.
They preserve REVIEW_REQUIRED/BLOCKED behavior and a human handoff after PASS.
No signed approval, authenticated identity or operational capability is added.

## Final independent validation

The user independently checked out exact code head
`f756779d063a48d6bdbb00b861a329a2c092953e` in a clean detached worktree and supplied terminal output:

- worktree status: clean;
- 85 orchestration tests: OK;
- 106 M006f tests: OK;
- `RND_WORKSPACE_AUDIT: PASS`, 24 tasks, 23 experiments, broker writes false,
  protected-path modifications false, promotion authority human-only;
- `git diff --check 28a8cf2fa474e2692db66fe7cdf104565ee1eb76...HEAD`:
  no output.

Both GitHub guard workflows also succeeded on that exact tested head. A later
shell attempt failed only after the temporary validation directory had been
removed while it was still the shell's current working directory; it occurred
after the complete successful run and is not part of the validation result.

RND-0024 is complete as a non-operational R&D candidate. Human merge and
promotion authority remain external and unset; no trading execution or capital
authority is granted.
