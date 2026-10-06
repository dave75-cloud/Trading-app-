# RND-0060H Postmortem

## Classification

CROSS_SECTIONAL_STRUCTURE_DETECTED

## Frozen study

RND-0060H tested whether the 11:30 UTC cross-sectional dispersion of the four USD-oriented 30-minute returns (AUDUSD, EURUSD, GBPUSD, USDJPY; population standard deviation) had a repeatable development-only association with subsequent 30-minute market-wide realized movement.

Primary response: equal-weight mean of the four pairs' next-30-minute relative realized mid ranges.
Secondary response: population standard deviation of the four next-30-minute USD-oriented close returns.

The study used DEVELOPMENT_2015_2020 only, exactly one declared trial, no parameter search, no trade simulation, no P&L, and no validation/final/reserved/broker/capital authority.

## Frozen screen result

All predeclared criteria passed.

- aggregate primary Spearman: 0.34287948215254677 (frozen hurdle >= 0.05)
- annual primary Spearman positive: 6/6 years
- per-symbol forward-range Spearman positive: 4/4 symbols
- top-quartile mean primary response > bottom-quartile mean primary response
- integrity reconciliation: PASS

Eligible market-wide observations: 1531
Excluded observations: 18

Annual primary Spearman:
- 2015: 0.24415233129376646
- 2016: 0.3252526637860827
- 2017: 0.3069216467463479
- 2018: 0.24191839240251148
- 2019: 0.2982285679219424
- 2020: 0.35319068109765783

Per-symbol primary Spearman:
- AUDUSD: 0.25313582458466577
- EURUSD: 0.2688865084693795
- GBPUSD: 0.2275088536129867
- USDJPY: 0.2702149133943151

Quartile diagnostic:
- bottom-quartile mean primary response: 0.0010591938742475293
- top-quartile mean primary response: 0.0014679172413174049
- top/bottom ratio: approximately 1.386

Secondary aggregate Spearman: 0.19517733191511005

## Interpretation

This is broad, reproducible cross-sectional structure in the development evidence, not a marginal threshold pass and not a result driven by one pair or one year. The association is materially stronger than the weak univariate state associations seen in RND-0060F and RND-0060G.

The result supports the scientific proposition that higher cross-sectional dispersion among the four USD-oriented 30-minute returns at 11:30 UTC is associated with greater subsequent 30-minute market-wide realized movement.

It does NOT establish a profitable trading rule, direction, entry method, threshold, position-sizing rule, expected P&L, validation success, or promotion eligibility.

## Governance conclusion

RND-0060H is COMPLETE with CROSS_SECTIONAL_STRUCTURE_DETECTED.

This result may justify a separate human-approved candidate-mechanism design/review task. Any such task must be predeclared independently and must not silently convert this descriptive structure into a trading rule.

Prohibited post-hoc actions include:
- selecting a threshold or quartile cutoff from these results,
- choosing a pair based on the observed per-symbol coefficients,
- selecting a different observation time or lookback based on this result,
- inferring directionality from the realized-range association,
- opening validation or reserved-final evidence,
- creating broker/capital/execution authority,
- automatic promotion.

A next task, if human-approved, should explicitly separate mechanism-design hypotheses from this completed structure study and preserve the one-trial/no-search discipline.

## Evidence identity

Full development report:
`~/Trading-evidence/rnd0060h-cross-sectional-dispersion-state-full-development-2015-2020-20261006.json`

Report SHA-256:
`499ce54cbacb37b5dc86071f707df31e6207b8064f0bca5b96e1d2042436dcc3`

Outcome receipt commit:
`947f3fc2e651a0f27e344f7cae19627e0338234b`
