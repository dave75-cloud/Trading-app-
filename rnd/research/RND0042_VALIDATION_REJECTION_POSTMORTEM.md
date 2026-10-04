# RND-0042 — Validation Rejection Scientific Post-Mortem

Status: **CLOSED / VALIDATION_REJECTED**

## Outcome

The sole fixed validation candidate (M005 with volatility eligibility threshold `0.0006`) was evaluated on the sealed RND-0041 validation partition under the predeclared RND-0040 decision rule.

Mechanical classification: `VALIDATION_REJECTED`.

Validation report:

- `~/Trading-evidence/rnd0042-validation-candidate-20261004.json`
- SHA-256: `8636b73a887a082d6cf4b73aadd67b9ac7c6bc2db17d534928d12153df542548`

Receipt commit: `21cc45b30535a0650993a00cad1cadba10431859`.

## Primary criteria

- terminal equity > 1.0: **FAIL**
- aggregate realized completed-trade net-return sum > 0: **FAIL**
- at least 3 of 4 pairs net non-negative: **FAIL**
- pair concentration <= 70% of positive aggregate contribution: **FAIL**
- year concentration <= 70% of positive aggregate contribution: **PASS**
- four-pair equal-unit max drawdown >= -0.10: **PASS**
- evidence identity / boundary / leakage / warm-up integrity: **PASS**

Because criteria 1 and 2 failed, rejection is mandatory under the frozen protocol.

## Validation economics

Four-pair concurrent reference:

- final equal-unit normalized equity index: `0.9859543634839679`
- realized completed-trade net-return sum: `-0.05618254606412833`
- equal-unit normalized max drawdown: `-0.022893794914579435`
- timestamp count: `149388`

This was not a risk-control failure. Drawdown remained modest. It was a failure of net economic edge.

Per-pair completed-trade results:

- AUDUSD: gross `1.0099143552663277`, net `0.9699329868941865`, 323 trades, net-return sum `-0.02959808947229024`
- EURUSD: gross `0.9864296718301108`, net `0.9749596920959528`, 129 trades, net-return sum `-0.025160258173758325`
- GBPUSD: gross `1.0122544198718704`, net `0.989032053689164`, 172 trades, net-return sum `-0.010557155558555157`
- USDJPY: gross `1.0167915585384688`, net `1.0090177334750112`, 82 trades, net-return sum `0.009132957140475387`

Only USDJPY remained net-positive. AUDUSD, EURUSD, and GBPUSD failed to retain positive net economics.

Calendar-year net-return sums:

- 2021: `-0.01639748666364234`
- 2022: `-0.03978505940048599`

Both full validation years were negative. The rejection therefore is not explained by a single bad calendar year.

## Cost interpretation

Break-even additional round-trip cost headroom:

- AUDUSD: `0.0` bps
- EURUSD: `0.0` bps
- GBPUSD: `0.0` bps
- USDJPY: `1.0948525597132144` bps

The higher-volatility filter improved development-period signal-to-friction economics, but the untouched validation result shows that this did not generalize as a robust four-pair net edge. Three pairs had no positive incremental cost headroom at all.

## Bootstrap interpretation

Positive-total stationary-bootstrap fractions:

- AUDUSD: `0.2132` to `0.2380`
- EURUSD: `0.0085` to `0.0516`
- GBPUSD: `0.2805` to `0.3126`
- USDJPY: `0.6783` to `0.7900`

Dependence-aware resampling does not rescue the four-pair proposition. USDJPY remains the only pair with consistently favorable validation bootstrap evidence.

## Scientific conclusion

The development-stage observation that stricter volatility gating improved the original M005 economics was real enough to justify confirmatory testing, but it did **not** transfer into a robust four-pair validation edge.

The correct interpretation is:

1. the `0.0006` higher-volatility filter was a useful development hypothesis;
2. it improved historical development economics and reduced cost exposure;
3. it failed untouched validation as a four-pair candidate;
4. the candidate is therefore closed and not promotable;
5. validation evidence may not be reused to tune thresholds, drop pairs, alter sessions, or otherwise rescue the candidate;
6. the reserved final test remains sealed and must not be opened for this rejected candidate.

## Governance consequence

The project should **not** proceed by testing nearby thresholds, excluding AUDUSD, keeping only USDJPY, or otherwise optimizing from validation outcomes.

Any future research must begin from a genuinely new, independently justified hypothesis and return to development-stage research under a fresh predeclared protocol. Validation findings may be retained as negative evidence and as constraints on future hypotheses, but not as a tuning surface.

All execution, capital, broker-write, promotion, and final-test authorities remain closed.
