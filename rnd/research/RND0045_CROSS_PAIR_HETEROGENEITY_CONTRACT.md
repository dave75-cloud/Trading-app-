# RND-0045 — Cross-Pair Heterogeneity Study

Status: **PREDECLARED / DEVELOPMENT OUTCOMES CLOSED**

## Purpose

RND-0045 follows RND-0044 without introducing any new trading rule, threshold, pair selection, or validation access.

RND-0044 showed that the ratio-only `Q003` rule (`signal_to_friction >= 8.0`, with no absolute volatility floor) produced positive four-pair development economics, but did not satisfy the predeclared 3-of-4 pair-positive requirement. EURUSD and GBPUSD finished above 1.0 net equity, USDJPY finished close to flat, and AUDUSD remained materially negative.

The purpose of RND-0045 is therefore structural falsification of cross-pair transferability:

> Does the same frozen Q003 mechanism have a sufficiently common effect across AUDUSD, EURUSD, GBPUSD, and USDJPY, or is the apparent aggregate edge fundamentally pair-dependent?

RND-0045 is diagnostic research only. It does not authorize pair dropping, pair-specific thresholds, strategy selection, validation, promotion, or capital allocation.

## Frozen mechanism

The mechanism under study is fixed exactly as RND-0044 Q003:

- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY;
- timeframe: M5;
- MA fast: 20;
- MA slow: 50;
- volatility window: 12;
- population standard deviation (`ddof=0`);
- ratio-only entry rule: `signal_to_friction >= 8.0`;
- no absolute volatility floor;
- sessions unchanged;
- one-observation signal delay unchanged;
- minimum hold three observed bars unchanged;
- bid/ask execution unchanged;
- gap semantics unchanged.

No strategy mechanics may change inside RND-0045.

## Authorized evidence

Development evidence only:

- start inclusive: `2015-01-01T00:00:00Z`;
- end exclusive: `2020-12-31T19:15:00Z`;
- governed RND-0037 24/24 development assembly;
- RND-0044 Q003 trade/equity output may be recomputed deterministically from the same governed evidence or loaded from a SHA-bound authoritative RND-0044 report.

Prohibited:

- consumed 2021-2022 validation evidence;
- reserved-final 2023-2024 evidence;
- any post-development data used to choose rules;
- any pair deletion or weighting change.

## Null and structural hypotheses

### H0 — material pair heterogeneity

The Q003 treatment effect is not sufficiently common across the four pairs; aggregate improvement is driven by pair-specific behavior and cannot yet support a common-rule candidate.

### H1 — common mechanism with bounded heterogeneity

The Q003 treatment effect is directionally common enough across pairs, with pair differences that are bounded and not dominated by a single pair, to justify a later common-rule candidate-freeze review.

RND-0045 does **not** test whether Q003 is profitable on unseen data. It tests only whether development evidence supports a common cross-pair mechanism.

## Predeclared estimands

For each symbol, compute Q003 minus Q000 on the same 2015-2020 evidence for:

1. completed-trade net-return sum;
2. net equity index change;
3. maximum drawdown change;
4. execution-cost drag change;
5. trade-count change;
6. yearly net-return-sum treatment effect for each year 2015-2020;
7. leave-one-year-out treatment effect;
8. stationary-bootstrap distribution of aggregate pair net-return under the frozen RND-0035 bootstrap family where technically compatible.

Also compute across-pair diagnostics:

- sign coherence of full-period Q003-vs-Q000 improvement;
- dispersion of pair treatment effects;
- maximum pair share of total positive treatment-effect magnitude;
- minimum pair treatment effect;
- median pair treatment effect;
- pair rank stability across years;
- number of years in which each pair's Q003-vs-Q000 treatment effect is positive;
- number of pairs with positive treatment effect in each year;
- leave-one-pair-out aggregate treatment effect;
- aggregate result with each pair omitted strictly as a diagnostic, not as authority to remove a pair.

## Predeclared classification

Classification is exactly one of:

- `COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW`
- `COMMON_MECHANISM_SUPPORTED_WITH_MATERIAL_HETEROGENEITY`
- `PAIR_DEPENDENT_MECHANISM`
- `COMMON_MECHANISM_FALSIFIED`

### COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW

Requires all of:

1. Q003 minus Q000 full-period net-return-sum treatment effect is positive for at least 3 of 4 pairs;
2. no pair has a negative full-period treatment effect worse than 35% of the total positive treatment-effect magnitude of the other pairs;
3. every leave-one-pair-out aggregate Q003-vs-Q000 treatment effect is positive;
4. at least 4 of 6 calendar years have positive aggregate four-pair treatment effect;
5. in at least 4 of 6 years, at least 3 of 4 pairs have positive yearly treatment effect;
6. no single pair contributes more than 70% of total positive full-period treatment-effect magnitude;
7. no evidence, chronology, leakage, or gap-semantics violation occurs.

### COMMON_MECHANISM_SUPPORTED_WITH_MATERIAL_HETEROGENEITY

Used when:

- the four-pair aggregate treatment effect is positive;
- every leave-one-pair-out aggregate treatment effect is positive;
- at least 3 of 4 full-period pair treatment effects are positive;
- but one or more of the stricter candidate-review coherence conditions fail.

This classification permits further structural research only, not candidate freeze.

### PAIR_DEPENDENT_MECHANISM

Used when aggregate Q003-vs-Q000 improvement exists but:

- fewer than 3 of 4 pairs have positive full-period treatment effect; or
- leave-one-pair-out positivity fails; or
- one pair dominates the treatment effect beyond the predeclared concentration bound.

### COMMON_MECHANISM_FALSIFIED

Used when the aggregate Q003-vs-Q000 treatment effect is non-positive or the direction of effect is broadly adverse across pairs.

## Important interpretation rule

A pair may be diagnostically adverse without being removed. RND-0045 has **no authority** to:

- exclude AUDUSD or any other pair;
- assign pair-specific weights;
- assign pair-specific thresholds;
- introduce a new ratio value;
- alter sessions;
- alter MA windows, hold time, delay, spread treatment, or gap semantics.

Any future proposal to alter the universe or make rules pair-specific would require a separate predeclared research task with its own falsification logic.

## Governance

- development outcomes: **FALSE pending separate human authorization**
- new ratio thresholds: **FALSE**
- pair dropping: **FALSE**
- pair-specific rules: **FALSE**
- pair weighting: **FALSE**
- strategy selection: **FALSE**
- validation access: **FALSE**
- reserved final open: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
