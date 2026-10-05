# RND-0044 — Scientific Assessment

Status: COMPLETE / HUMAN REVIEW

## Headline

Authoritative classification: `RATIO_ONLY_MIXED_OR_NON_MONOTONIC`.

This label should not be read as a generic failure. The development evidence shows a materially stronger and more specific pattern:

- net economics improve monotonically across the ratio-only ladder Q001 -> Q002 -> Q003;
- Q003 is the first tested arm in this research line to produce positive four-pair realized completed-trade net-return sum and terminal equal-unit normalized equity above 1.0;
- Q003 drawdown is controlled and materially improved relative to Q000;
- Q003 passes year-concentration and leave-one-year / leave-one-pair majority robustness checks;
- Q003 fails the predeclared candidate-freeze-review rule because only two of four pairs finish with net equity index >= 1.0 (EURUSD and GBPUSD), while USDJPY is slightly below 1.0 and AUDUSD remains negative.

Therefore RND-0044 is best interpreted as: **ratio-only mechanism materially supported, but cross-pair coherence is insufficient for candidate freeze under the frozen rule**.

## Key Q003 evidence

- portfolio realized net-return sum: `+0.02539740608893785`
- terminal four-pair equal-unit normalized equity: `1.0063493515222344`
- concurrent max drawdown: `-0.022779961106376256`
- positive-year concentration share: `0.5348272784419509`
- leave-one-year-out improvement vs Q000: positive for all six exclusions
- leave-one-pair-out improvement vs Q000: positive for all four exclusions

Per pair Q003 net equity:

- AUDUSD: `0.9551193270027919`
- EURUSD: `1.0572584066225545`
- GBPUSD: `1.0154271352656874`
- USDJPY: `0.9981662326903039`

Thus the sole predeclared candidate-freeze-review blocker is the 3-of-4 pair profitability criterion.

## Governance conclusion

No strategy selection is authorized. Do not freeze Q003 automatically. Do not drop AUDUSD, tune pair-specific thresholds, add new ratio values, or open validation/reserved-final evidence based on this result.

The next research question should target **cross-pair heterogeneity / transferability**, not another numerical ratio search. A new RND task should predeclare a structural falsification analysis that asks whether the ratio-only mechanism has a common cross-pair effect or whether its apparent success is pair-dependent.

Validation access: FALSE
Reserved final open: FALSE
Strategy selection: FALSE
Broker writes: FALSE
Capital authority: FALSE
Automatic promotion: FALSE
Automatic merge: FALSE
Human review required: TRUE
