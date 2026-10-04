# RND-0038 — Full Development R000 Scientific Assessment

Status: **COMPLETE / HUMAN REVIEWED SCIENTIFIC ASSESSMENT**

## Scope

This assessment interprets the governed RND-0038 R000 reference completion over the complete 2015–2020 development partition only. Validation and reserved-final evidence remain closed.

External report SHA-256:
`5654fe89201b606d404aed36f8d8893e5b85cee90a3f0f11425067bdec9dd17d`

## Full-development R000 results

- AUDUSD: 1,172 trades; gross equity 0.9411478069; net equity 0.7887742732; net max drawdown -0.2289049428.
- EURUSD: 516 trades; gross equity 1.0576785197; net equity 1.0155473372; net max drawdown -0.0495847801.
- GBPUSD: 891 trades; gross equity 1.1069315731; net equity 0.9903297569; net max drawdown -0.0493355620.
- USDJPY: 346 trades; gross equity 1.0080082395; net equity 0.9765517231; net max drawdown -0.0422686804.

Observed equal-unit four-pair normalized reference:
- final equity index: 0.9372903482
- max drawdown: -0.0697714440
- realized completed-trade net-return sum: -0.2508386073

## 2020 contribution

The added 2020 development segment contributed 651 completed trades and remained slightly negative in aggregate:

- AUDUSD: net-return sum -0.0179832530
- EURUSD: net-return sum -0.0020467547
- GBPUSD: net-return sum +0.0041178849
- USDJPY: net-return sum +0.0078501050
- combined: net-return sum -0.0080620178

Therefore 2020 does not reverse the R000 conclusion. It modestly reinforces the prior 2015–2019 falsification while showing some pair-level heterogeneity.

## Temporal robustness

All six individual development years have negative aggregate net-return sums. All leave-one-year-out aggregations also remain negative, including leave-2020-out, which reproduces the already-adverse 2015–2019 aggregate.

This means the negative full-development result is not explained by a single adverse year.

## Cost robustness

Additional round-trip break-even cost headroom remains absent for AUDUSD, GBPUSD and USDJPY. EURUSD remains only marginally positive, with approximately 0.299 additional basis points per completed round trip before break-even.

Thus R000 remains highly cost-fragile.

## Dependence-aware bootstrap

Across the frozen stationary-bootstrap configurations, positive-total fractions are approximately:

- AUDUSD: 0.0000–0.0004
- EURUSD: 0.6165–0.6429
- GBPUSD: 0.4120–0.4362
- USDJPY: 0.1116–0.1838

Only EURUSD shows a majority-positive resampled total, and its cost headroom remains small. The four-pair R000 reference is therefore not supported as a robust positive development strategy.

## Scientific conclusion

**R000 is rejected as a robust four-pair positive development edge over the complete predeclared 2015–2020 development partition.**

2020 does not rescue the reference. The result remains adverse across years, pairs, cost diagnostics and dependence-aware resampling.

This conclusion does not validate any RND-0035 alternative. In particular, A016 / volatility threshold 0.0006 remains an outcome-derived development observation only.

## Next research implication

The coherent RND-0035 observation that higher volatility eligibility improved economics may now justify a separately predeclared falsification study, but only if treated as a new hypothesis generated from development evidence rather than a promoted strategy.

The next task should therefore test a **coarse higher-volatility eligibility hypothesis** without extending the threshold grid above 0.0006, without pair-specific tuning, without session-threshold interaction search, and without accessing validation or reserved-final evidence.

## Authority

- validation open: FALSE
- final test open: FALSE
- strategy selection: FALSE
- portfolio sizing: FALSE
- broker writes: FALSE
- capital authority: FALSE
- automatic promotion: FALSE
- automatic merge: FALSE
- human review required: TRUE
