# Reproducibility and governance self-test

Experiment: `EXP-20260921T010120Z-framework-self-test`

## Question

Can the governed R&D framework record and reproduce a deterministic offline result without broker, credential, network, protected-path, strategy, or capital authority?

## Method

A fixed JSON object was written to `input.json`. The object was parsed, serialized into canonical JSON using sorted keys and compact separators, terminated by a newline, encoded as UTF-8, and hashed with SHA-256. The resulting digest was written to `result.sha256` and independently recomputed before completion.

## Observations

The recomputed digest matched the recorded digest exactly: `8de8ce8723f9610568bb3954edc3eb5fc81a07431420b54a99d791926096c8a2`.

The experiment remained entirely offline and inside `rnd/`. It did not confer promotion, broker-write, strategy, execution, or capital authority.

## Result

PASS — deterministic offline reproducibility demonstrated for this framework self-test.
