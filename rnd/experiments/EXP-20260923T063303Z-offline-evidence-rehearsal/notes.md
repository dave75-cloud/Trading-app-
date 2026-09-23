# Offline evidence-chain rehearsal

Experiment: `EXP-20260923T063303Z-offline-evidence-rehearsal`

## Question

Can one harmless `rnd/` candidate's supplied evidence pass through RND-0020,
RND-0021 and RND-0022 contracts without adding execution or merge authority?

## Method

Use the real task planner, plan/evidence functions with an injected synthetic
Git runner, evidence assembler and evaluator in a focused integration suite.
The CLI consumes separately produced local JSON artifacts and writes four
deterministic output objects without overwrite.

## Observations

On code head `ea2164b8506dbfc55af9310a0ef90a8e08c6db61`, 72
orchestration tests, 106 M006f tests, and the workspace audit passed (23 tasks,
22 experiments, broker writes false, protected paths modified false, promotion
human-only). A local smoke rehearsal used the actual RND-0021 bounded Git
actions for eight changed `rnd/` paths, separate test/audit logs, and the
RND-0023 CLI. The provenance and dossier both reported PASS; human disposition
remained unset. These ephemeral artifacts stayed outside the repository.

External attestations are supplied claims; no module here independently proves
the external test or audit actually ran. Trading-system promotion remains
outside this experiment.

## Final independent validation

The user independently checked out exact PR head
`158444d673e50eb9a12d9f699024fd9c0bddee98` and supplied terminal output:

- 72 orchestration tests: OK.
- 106 M006f tests: OK.
- `RND_WORKSPACE_AUDIT: PASS`, 23 tasks, 22 experiments, broker writes false,
  protected-path modifications false, promotion authority human-only.
- `git diff --check 7f09d33213d0aab1afeb9e7311d9957ea8d060ff...HEAD`:
  no output.

Both GitHub guard workflows succeeded on that head. The user subsequently
authorized merge of PR #14. RND-0023 is complete as a non-operational R&D
candidate; no trading execution, promotion or capital authority is granted.
