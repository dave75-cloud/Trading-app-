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

RUNNING. Focused rehearsal tests pass locally. Final independent validation
must bind to the exact PR head. External attestations are supplied claims; no
module here proves the external test or audit actually ran. Human disposition
and trading-system promotion remain outside this experiment.
