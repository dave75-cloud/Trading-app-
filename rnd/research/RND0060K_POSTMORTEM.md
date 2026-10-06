# RND-0060K — Postmortem and Closure

## Formal outcome

Classification: `NO_REPRODUCIBLE_DIRECTIONAL_PRESSURE_STRUCTURE`

Authoritative full-development report:

`~/Trading-evidence/rnd0060k-close-location-pressure-full-development-2015-2020-20261006.json`

Report SHA-256:

`ee48a83e5cceb5723e102128d4fc0985e8bfe0c86b82f4d201a2b6f99be76e48`

## Integrity / governance

- development evidence verified: 24/24 pair-years
- trial_count: 1
- parameter_search: FALSE
- trade_simulation: FALSE
- pnl: FALSE
- strategy_candidate: FALSE
- validation_open: FALSE
- final_test_open: FALSE
- reserved_final_access: FALSE
- broker_writes: FALSE
- capital_authority: FALSE
- automatic_promotion: FALSE

## Diagnostic result

Eligible observations: 6116
Excluded market days: 20

Aggregate primary Spearman:

`-0.04310314875807829`

Positive years: 1/6

- 2015: -0.09124551114381876
- 2016: -0.020165455299795045
- 2017: -0.05172393646554324
- 2018: -0.03424640293569953
- 2019: -0.08997255579645733
- 2020: 0.005847935578453469

Positive symbols: 1/4

- AUDUSD: -0.06591405033054926
- EURUSD: -0.07373096464271606
- GBPUSD: 0.008789506766396624
- USDJPY: -0.04581758489971174

Quartile diagnostic:

- bottom quartile mean forward USD-oriented return: 6.260056339152644e-05
- top quartile mean forward USD-oriented return: -3.3560949968400964e-05
- quartile size: 1529

## Interpretation

The frozen 30-minute close-location pressure hypothesis failed broadly rather than marginally. Four of five prespecified criteria failed. The aggregate association was weakly negative, only one of six years was positive, only one of four symbols was positive, and the quartile diagnostic was ordered opposite to the hypothesised continuation relationship.

This result does not weaken RND-0060H's separate cross-sectional activity/magnitude finding. It does strengthen the conclusion that simple directional extraction from contemporaneous state variables is not supported by the current development evidence.

## Closure / anti-overfitting rule

RND-0060K is CLOSED.

Prohibited follow-ups as rescues of this trial:

- no sign inversion based on the observed negative correlation;
- no pair-specific selection based on GBPUSD being the only positive symbol;
- no year selection based on 2020 being the only positive year;
- no nearby observation-time change;
- no nearby lookback or forward-horizon change;
- no pressure-threshold optimization;
- no top/bottom-quartile trading rule derived from these results;
- no weighting optimization;
- no conditioning on RND-0060H after seeing this outcome;
- no validation, reserved-final, broker, capital, promotion, or merge authority created by this result.

## Research-direction decision

The current directional-search sequence should end here. RND-0060H remains the strongest independent structural finding and should be treated as an activity/magnitude state variable rather than repeatedly transformed into a directional predictor.

Recommended next task:

`RND-0060L — Economic Utility of Cross-Sectional Activity State`

The purpose of RND-0060L should be to evaluate whether the frozen RND-0060H activity state can improve decision quality in non-directional ways, such as identifying when movement is more likely to exceed friction, informing admissibility/timing of already-independent signals, execution urgency, or risk-state decisions. It must begin as a development-only, non-trading design review with no outcome-mined thresholds and no use of validation/final evidence.
