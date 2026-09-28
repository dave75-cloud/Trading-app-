# Quantitative research baseline and reproducibility standard

Experiment: `EXP-20260928T115103Z-quant-research-baseline`

## Question

Can the project define a pre-result quantitative research contract that rejects
common forms of backtest contamination before autonomous strategy discovery is
allowed to expand?

## Method

Document the research-data, experiment, simulator and validation standard.
Audit the surviving legacy Champion/M005 research path without rerunning a
search. Add a pure local declaration validator and adversarial tests for missing
provenance, future-bar access, synthetic return clipping, chronological
contamination, undeclared trials, incomplete execution data and authority
escalation.

## Observations

RUNNING. The candidate is deliberately a measuring-instrument task rather than
a strategy experiment. It grants no strategy-selection, broker-write, merge,
promotion or capital authority. Canonical M005 and frozen M006e remain
unchanged.

Independent exact-head validation is required before completion.

## Final independent validation

The user independently checked out exact implementation head
`30d3ff7ab7826abf94fc8bcd4f94252c537925cc` in a clean detached worktree and supplied terminal output:

- worktree status: clean;
- 97 orchestration tests: OK;
- 106 M006f tests: OK;
- `RND_WORKSPACE_AUDIT: PASS`, 25 tasks, 24 experiments, broker writes false,
  protected-path modifications false, promotion authority human-only;
- `git diff --check 1c6fd4641f275b70519b167a2493d7908ad1c1bc...HEAD`:
  no output.

Both GitHub guard workflows also succeeded on that exact tested head.

RND-0025 is complete as a non-operational R&D research-baseline candidate.
It performed no strategy search, ranking or selection. Human merge and
promotion authority remain external and unset; no trading execution or capital
authority is granted.
