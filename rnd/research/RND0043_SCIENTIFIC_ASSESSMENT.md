# RND-0043 — Scientific Assessment

Status: **MECHANISM SUPPORTED FOR FURTHER RESEARCH / NO CANDIDATE FROZEN**

## Result binding

- Development report: `~/Trading-evidence/rnd0043-signal-friction-development-20261004.json`
- Report SHA-256: `33e6a4855c84c8497203d22a24f60b100d8a1d47e3ce25565536df40d5bff561`
- Classification: `MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH`
- Best coherent arm under the predeclared mechanism rule: `F003` (`signal_to_friction >= 8.0`)

## What was supported

The signal-to-friction mechanism materially improved the development economics relative to the ungated F000 reference across the predeclared ladder. Portfolio realized completed-trade net-return sum improved from approximately `-0.25084` at F000 to `-0.24227` at F001, `-0.08349` at F002, and `-0.03075` at F003. Concurrent equal-unit normalized maximum drawdown improved from approximately `-0.06977` at F000 to `-0.06754`, `-0.03863`, and `-0.02128` respectively.

The leave-one-year-out and leave-one-pair-out diagnostics were positive-majority at the stricter arms, and F003 satisfied the predeclared year-concentration condition. This supports the mechanism-level hypothesis that requiring realized short-horizon movement to dominate current spread friction removes a substantial portion of economically weak trades.

## Why F003 is not yet a candidate strategy

Despite being the best coherent arm, F003 still has negative aggregate development net economics:

- portfolio completed-trade net-return sum: approximately `-0.03075`;
- concurrent terminal normalized equity index: approximately `0.99231`;
- only GBPUSD is net-positive at F003;
- AUDUSD remains materially negative;
- EURUSD and USDJPY remain slightly negative.

Therefore the mechanism is supported, but no arm is sufficiently strong to freeze as a validation candidate. Selecting F003 merely because it is the least-negative development arm would convert mechanism research into outcome-driven strategy selection.

## Scientific conclusion

RND-0043 demonstrates a useful structural effect, not yet a deployable or validation-ready strategy. The correct next step is a further development-only falsification that tests whether the dimensionless signal-to-friction mechanism should replace, rather than merely supplement, the old absolute volatility floor.

This is a distinct structural hypothesis: if the ratio already expresses movement relative to executable friction, the legacy absolute volatility threshold may be redundant or may interfere with portability across pairs and regimes.

## Governance

- candidate strategy frozen: **FALSE**
- strategy selection: **FALSE**
- validation access: **FALSE**
- previously consumed 2021–2022 validation reuse: **PROHIBITED**
- reserved-final 2023–2024 access: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
