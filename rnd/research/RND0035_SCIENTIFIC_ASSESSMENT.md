# RND-0035 Scientific Assessment — Development Robustness and R000 Reference Diagnostics

Status: **DEVELOPMENT EVIDENCE COMPLETE FOR 2015–2019 / HUMAN REVIEW REQUIRED / NO PROMOTION AUTHORITY**

## Scope

This assessment records the scientific interpretation of the governed RND-0035 development evidence only. It does not open validation or final-test data, does not select a strategy, and does not promote any RND-0035 variant.

Bound external evidence:

- 36-trial A/C/D/E/F development report SHA-256: `038af0e5b669c2f8f2ebb1947c1b765810965ed584963246b85a43cce50cc264`
- R000 B/D/G reference diagnostics report SHA-256: `81d037eb5998375ccff13c68dac564722adc183f8970cb656bf4bf0194e1849c`
- authorized evidence identity: `20/20`
- development interval represented here: 2015–2019 only; 2020 remains missing from the predeclared RND-0029 development partition.

## 1. R000 remains economically adverse overall

R000 2015–2019 completed-trade net equity indices:

- AUDUSD: `0.80379677`
- EURUSD: `1.01777557`
- GBPUSD: `0.98658356`
- USDJPY: `0.96903723`

The observed equal-unit four-pair concurrent reference ends at normalized equity `0.9393058526`, with normalized max drawdown `-0.0624927993`.

Therefore the fixed R000 M005 reference is not a positive four-pair development result over 2015–2019.

## 2. Adversity is not explained by one bad year

Combined R000 net return sums are negative in every observed year:

- 2015: `-0.0725357276`
- 2016: `-0.0627228953`
- 2017: `-0.0417109711`
- 2018: `-0.0380192029`
- 2019: `-0.0277877925`

Every leave-one-year-out aggregation remains negative. This materially weakens any explanation based on one isolated adverse calendar year.

Trade counts also decline substantially through the sample: 759 (2015), 728 (2016), 310 (2017), 282 (2018), 195 (2019). This remains an important regime/activity diagnostic for later 2020 assembly.

## 3. Pair concentration

AUDUSD is the dominant adverse contributor, with completed-trade net return sum `-0.2170846819` over 885 trades.

EURUSD is the only pair with positive completed-trade net return sum (`+0.0182714928`). Removing AUDUSD leaves the other three pairs still slightly negative (`-0.0256919075`), while removing EURUSD makes the aggregate materially more adverse (`-0.2610480823`).

Thus the four-pair weakness is not solely an AUDUSD artifact, although AUDUSD is the largest adverse component.

## 4. Extreme-trade concentration is not sufficient to explain the result

The largest 1% of trades by absolute net return contribute about `7.72%` of total absolute net-return magnitude; the largest 5% contribute about `23.40%`.

Their signed contributions are positive, not negative. The adverse R000 result therefore is not caused by a handful of extreme losing trades dominating the sample.

## 5. Cost sensitivity is severe

R000 gross-to-net evidence:

- AUDUSD gross `0.91706599`, net `0.80379677`, already below break-even before any added stress.
- EURUSD gross `1.05278068`, net `1.01777557`, with only `0.409762` additional adverse round-trip bps per completed trade before break-even.
- GBPUSD gross `1.07309996`, net `0.98658356`, already below break-even after observed costs.
- USDJPY gross `0.99445280`, net `0.96903723`, already below break-even even gross.

The predeclared D-family stresses deteriorate monotonically. The reference effect is therefore not comfortably separated from realistic execution friction.

## 6. Dependence-aware stationary bootstrap does not rescue R000

Across all nine frozen seed/block configurations:

- AUDUSD has essentially zero positive-total resamples (0 to 0.01%).
- USDJPY positive-total fractions are only about 3%–7%.
- GBPUSD positive-total fractions are about 35%–37%.
- EURUSD is the lone marginally favorable pair, with positive-total fractions about 63%–67%.

Average bootstrap compounded equity remains close to the observed pair result in each case. This supports the interpretation that the adverse/marginal pair results are not artifacts of IID ordering assumptions.

## 7. A-family higher-volatility observation is scientifically interesting but outcome-derived

Within the predeclared OFAT volatility-threshold trials, increasing the threshold toward `.0006` produced a coherent development-period improvement pattern with fewer trades. At A016 (`0.0006`) three pairs were above net equity 1.0 and AUDUSD was materially less adverse.

This is a legitimate robustness finding because A016 was frozen before outcomes were observed. However, its scientific status is **hypothesis-generating only**:

- A016 is not the new reference strategy.
- no threshold above `.0006` may be searched informally;
- no pair-specific threshold selection is allowed;
- no session/threshold joint search is allowed;
- validation/final data must not be opened to resolve the hypothesis.

The separate `RND0035_FOLLOWUP_HYPOTHESIS_QUARANTINE.md` governs this observation.

## 8. Session, gap and execution perturbations

C-family results show meaningful session sensitivity, especially for AUDUSD, but no uniform four-pair improvement. The no-pair-specific-hour-search prohibition remains necessary.

E-family gap-policy changes alter trade frequency and some pair outcomes but do not explain away the broad R000 weakness.

F-family conservative execution perturbations are mixed rather than universally catastrophic. This reduces concern that R000 depends entirely on one exact fill convention, but it does not create a robust four-pair edge.

## Scientific conclusion

**RND-0035 falsifies the proposition that fixed R000 M005 is a robust positive four-pair development strategy over 2015–2019.** The evidence is broad: adverse aggregate economics, negative yearly sums, adverse leave-one-year-out results, severe cost sensitivity, and dependence-aware resampling that does not rescue three of four pairs.

At the same time, RND-0035 generates one controlled follow-up hypothesis: stronger volatility gating may improve signal-to-friction quality by reducing low-amplitude trades. That hypothesis is not established and remains quarantined pending completion of the missing 2020 development evidence and a separately predeclared experiment.

## Next governed step

Proceed to RND-0036 acquisition and sealing of the remaining RND-0029 development interval:

- start inclusive: `2020-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- four frozen symbols, M5, OANDA PRACTICE historical evidence semantics
- acquisition/quarantine/sealing only
- **no strategy outcomes** during acquisition.

Only after RND-0036 is sealed may a separate human-reviewed task assemble 2015–2020 development evidence and decide whether any fixed follow-up hypothesis is authorized.

## Authority

- validation open: **FALSE**
- final test open: **FALSE**
- strategy selection: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- promotion authority: **HUMAN_ONLY**
