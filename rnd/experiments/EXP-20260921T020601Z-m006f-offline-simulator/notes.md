# M006f offline shadow simulator

Experiment: `EXP-20260921T020601Z-m006f-offline-simulator`

## Question

A deterministic local simulator can model already-approved actions, adverse spread/slippage, AUD-valued realized P&L, exposure and drawdown without recalculating strategy sizing.

## Method

Work was confined to governed R&D artifacts outside frozen operational paths.
Executable code, where present, is offline and uses local explicit inputs only.

## Result

PASS: 7 offline unit tests passed; duplicate events, invalid exits and opaque reversals fail closed; network and submission capability remain absent.

## Governance

No frozen component, strategy parameter, risk rule, sizing authority, accepted
evidence, broker authority, or capital authority is modified or conferred.
Human review remains mandatory for phase changes and merge.
