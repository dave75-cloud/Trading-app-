# RND-0044 — Ratio-Only Replacement Development Study

Status: **PREDECLARED / DEVELOPMENT OUTCOMES CLOSED**

## Purpose

RND-0044 follows the RND-0043 mechanism-level result `MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH` without freezing any candidate arm.

The new structural hypothesis is that the dimensionless signal-to-friction gate may make the legacy absolute volatility floor (`0.0005`) redundant. RND-0044 therefore tests the ratio gate as a replacement for, not an addition to, the old absolute-volatility eligibility rule.

This is not an extension of the threshold grid and does not add any new signal-to-friction ratios.

## Authorized evidence

Development only:

- start inclusive: `2015-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- timeframe: M5
- governed RND-0037 24/24 development assembly

Prohibited:

- consumed 2021–2022 validation evidence;
- reserved-final evidence beginning `2023-01-01T09:40:00Z`;
- any post-development evidence for rule selection.

## Frozen base mechanics

All M005 mechanics remain frozen except the absolute-volatility eligibility condition:

- fast MA 20;
- slow MA 50;
- volatility window 12;
- population std (`ddof=0`);
- signal delay 1 observed eligible bar;
- minimum hold 3 observed bars;
- sessions unchanged;
- bid/ask execution unchanged;
- gap handling unchanged;
- all four pairs unchanged.

## Experimental change

For RND-0044 ratio-only arms, the old absolute condition `sigma12_mid_return >= 0.0005` is disabled as an entry-eligibility requirement.

The only volatility/friction eligibility rule is:

`signal_to_friction = sigma12_mid_return / relative_spread`

with the same contemporaneous definitions frozen by RND-0043.

## Predeclared arms

No new ratio values are introduced.

- `Q000`: frozen R000 reference (`0.0005` absolute floor, no ratio gate)
- `Q001`: ratio-only `>= 3.0`, no absolute floor
- `Q002`: ratio-only `>= 5.0`, no absolute floor
- `Q003`: ratio-only `>= 8.0`, no absolute floor

These are falsification arms, not candidate strategies.

## Primary questions

1. Does removing the absolute floor improve or degrade the RND-0043 mechanism across the same coarse ratio ladder?
2. Does the ratio-only mechanism produce positive aggregate development net economics at any predeclared arm?
3. Is any improvement coherent across pairs and years rather than driven by one pair or one year?
4. Does drawdown remain controlled relative to Q000?
5. Do leave-one-year-out and leave-one-pair-out results preserve the sign of aggregate improvement in a majority of exclusions?
6. Does trade count remain large enough to avoid a trivial scarcity explanation?
7. Is the ordering across 3.0, 5.0, 8.0 coherent rather than an isolated best point?

## Predeclared interpretation

Classification is one of:

- `RATIO_ONLY_SUPPORTED_FOR_CANDIDATE_FREEZE_REVIEW`
- `RATIO_ONLY_SUPPORTED_FOR_FURTHER_RESEARCH_ONLY`
- `RATIO_ONLY_MIXED_OR_NON_MONOTONIC`
- `RATIO_ONLY_FALSIFIED`

`RATIO_ONLY_SUPPORTED_FOR_CANDIDATE_FREEZE_REVIEW` requires all of:

1. at least one ratio-only arm has four-pair realized completed-trade net-return sum > 0;
2. its four-pair equal-unit normalized terminal equity index > 1.0;
3. at least 3 of 4 pairs have net equity index >= 1.0;
4. four-pair concurrent maximum drawdown >= -0.10;
5. no single positive development year contributes >70% of positive aggregate net contribution;
6. leave-one-year-out and leave-one-pair-out improvement vs Q000 are positive in a majority of exclusions;
7. no evidence, chronology, leakage, or gap-semantics violation occurs.

If the mechanism materially improves Q000 but no arm meets all candidate-freeze-review conditions, classification is `RATIO_ONLY_SUPPORTED_FOR_FURTHER_RESEARCH_ONLY`.

If results are isolated/non-monotonic/concentrated, classify `RATIO_ONLY_MIXED_OR_NON_MONOTONIC`.

If ratio-only arms fail to improve aggregate net economics or materially worsen them, classify `RATIO_ONLY_FALSIFIED`.

No arm may be frozen automatically even if the first classification is reached; a separate human candidate-freeze decision is required.

## Required diagnostics

For each arm and pair:

- trade count;
- hit rate;
- gross and net equity;
- net-return sum;
- max drawdown;
- execution-cost drag;
- entry ratio distribution;
- rejected-entry count.

Portfolio diagnostics:

- per-year and pair×year net contributions;
- leave-one-year-out;
- leave-one-pair-out;
- top 1% and top 5% absolute contribution shares;
- break-even additional round-trip cost by pair;
- stationary bootstrap under the frozen RND-0035 configuration family;
- four-pair concurrent reference statistics.

## Governance

- development outcomes: **FALSE pending separate human authorization**
- new ratio thresholds: **FALSE**
- pair-specific thresholds: **FALSE**
- strategy selection: **FALSE**
- validation access: **FALSE**
- reserved final test open: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
