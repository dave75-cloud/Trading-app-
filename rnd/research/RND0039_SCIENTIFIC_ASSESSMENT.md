# RND-0039 — Scientific Assessment

## Status

**HIGHER-VOLATILITY HYPOTHESIS SUPPORTED, BUT NOT PROMOTABLE AS A ROBUST FOUR-PAIR EDGE**

## Scope

This assessment concerns only the predeclared two-point development comparison between:

- R000 volatility threshold `0.0005`; and
- higher-volatility treatment threshold `0.0006`.

Evidence scope is the complete governed 2015–2020 development partition. Validation and reserved-final evidence remain closed.

## Full-development comparison

Across all four pairs, the `0.0006` treatment improves net equity and max drawdown relative to `0.0005`, while materially reducing trade count and execution-cost drag.

- AUDUSD: net equity `0.7887742732 -> 0.8812064711`; max drawdown `-0.2289049428 -> -0.1299451558`; trades `1172 -> 686`; cost drag `0.1765978593 -> 0.1066113875`.
- EURUSD: net equity `1.0155473372 -> 1.0171756454`; max drawdown `-0.0495847801 -> -0.0312012207`; trades `516 -> 306`; cost drag `0.0406521419 -> 0.0250591261`.
- GBPUSD: net equity `0.9903297569 -> 1.0399341860`; max drawdown `-0.0493355620 -> -0.0240873190`; trades `891 -> 466`; cost drag `0.1113195453 -> 0.0613542727`.
- USDJPY: net equity `0.9765517231 -> 1.0116401781`; max drawdown `-0.0422686804 -> -0.0262085687`; trades `346 -> 193`; cost drag `0.0317052562 -> 0.0182943364`.

The improvement is not purely a fee artifact. AUDUSD and USDJPY improve gross equity as well as net equity. GBPUSD keeps essentially the same positive gross economics while materially reducing cost drag. EURUSD gives up some gross equity but slightly improves net equity through lower friction.

## 2020 contribution

The higher-volatility treatment also survives the addition of 2020, which was not part of the original RND-0035 threshold observation.

Combined 2020 results:

- `0.0005`: 651 trades, gross-return sum `+0.0766273470`, net-return sum `-0.0080620178`.
- `0.0006`: 394 trades, gross-return sum `+0.0705137862`, net-return sum `+0.0143724450`.

2020 treatment improvement is therefore economically meaningful and is not merely a re-expression of the 2015–2019 result.

However, 2020 is not uniformly favorable by pair: AUDUSD and GBPUSD improve materially, while EURUSD and USDJPY are negative under the treatment in 2020. This prevents a claim of pairwise universal robustness.

## Year concentration

The treatment improves the yearly pattern relative to R000 but does not establish year-by-year robustness:

- 2016 and 2020 are positive under `0.0006`.
- 2015, 2017, 2018 and 2019 remain negative.
- 2018 remains notably adverse.

Therefore the hypothesis survives, but persistent temporal concentration remains a material weakness.

## Cost robustness

Under `0.0006`, break-even additional round-trip cost headroom is:

- AUDUSD: `0.0 bps`;
- EURUSD: `0.5565441518 bps`;
- GBPUSD: `0.8403222978 bps`;
- USDJPY: `0.5996512559 bps`.

Thus the treatment substantially improves friction robustness for EURUSD, GBPUSD and USDJPY, but AUDUSD remains economically adverse even before any further cost increase.

## Dependence-aware bootstrap

The stationary-bootstrap positive-total fractions materially improve under `0.0006`:

- AUDUSD: approximately `0.0039–0.0137`;
- EURUSD: `0.6759–0.6878`;
- GBPUSD: `0.8782–0.9119`;
- USDJPY: `0.6107–0.6634`.

This is strong supportive evidence for GBPUSD and moderate supportive evidence for EURUSD and USDJPY. AUDUSD remains decisively adverse.

## Four-pair concurrent reference

Observed equal-unit four-pair concurrent results:

- `0.0005`: final normalized equity `0.9372903482`, max drawdown `-0.0697714440`, realized completed-trade net-return sum `-0.2508386073`.
- `0.0006`: final normalized equity `0.9861496424`, max drawdown `-0.0228605470`, realized completed-trade net-return sum `-0.0554014304`.

This is a large improvement in both terminal outcome and drawdown. Nevertheless, the treatment portfolio remains below `1.0`, so RND-0039 does **not** establish a robust positive four-pair edge.

## Scientific conclusion

RND-0039 supports the hypothesis that higher volatility eligibility at the predeclared `0.0006` threshold improves signal-to-friction economics relative to R000 over the complete 2015–2020 development period.

The support is substantive because:

1. all four pairs improve net equity and max drawdown;
2. cost drag falls materially across all four pairs;
3. the effect survives into newly added 2020 development evidence;
4. bootstrap support materially improves for three of four pairs; and
5. the observed concurrent four-pair result moves substantially closer to break-even with much lower drawdown.

But the hypothesis is **not sufficient for promotion** because:

1. the four-pair equal-unit portfolio still finishes below `1.0`;
2. AUDUSD remains materially adverse;
3. only two of six development years are positive in aggregate under the treatment;
4. 2020 is not pairwise consistent; and
5. the experiment was itself motivated by prior development outcomes, so validation evidence remains essential before any claim of out-of-sample edge.

## Governance conclusion

- hypothesis status: **SUPPORTED, QUALIFIED**
- robust four-pair edge established: **FALSE**
- strategy promotion authorized: **FALSE**
- further threshold search authorized: **FALSE**
- pair-specific tuning authorized: **FALSE**
- validation open: **FALSE**
- final test open: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- human review required before any next stage: **TRUE**
