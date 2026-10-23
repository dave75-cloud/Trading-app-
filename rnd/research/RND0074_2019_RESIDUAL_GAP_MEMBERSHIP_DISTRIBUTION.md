# RND-0074 — 2019 residual missing-timestamp pair membership

**Status: operator-reported read-only development timestamp analysis; no evidence admission.**

Operator applied a less-than-12-consecutive-M5-run criterion **within each pair**, using only `missing_timestamps` in the RND-0033 2019 development discrepancy ledgers for AUDUSD, EURUSD, GBPUSD and USDJPY. They counted distinct timestamp membership in each of the four pair-specific residual sets.

| Number of pair-specific residual sets containing timestamp | Distinct timestamps |
| --- | ---: |
| Exactly 1 | 2349 |
| Exactly 2 | 283 |
| Exactly 3 | 37 |
| Exactly 4 | 25 |
| **Total distinct** | **2694** |

Membership-weighted total = 2349 + 2*283 + 3*37 + 4*25 = **3126 pair-timestamp occurrences**, reconciling with prior per-pair residual totals: AUDUSD 1605, EURUSD 555, GBPUSD 690, USDJPY 276 (sum 3126). Exactly-one-pair fraction: 2349/2694 = 87.19% of distinct residual timestamps. The 25 four-way shared values are the same previously recorded four-way intersection (not independently rechecked here).

Interpretation: residual-gap timestamps are predominantly pair-specific **within this per-instrument run-length definition**. This does not demonstrate zero trading activity, an OANDA outage or liquidity behaviour. Pair-specific residual classification does not exclude membership in a longer run for a different pair: cross-classification and causal attribution remain outstanding.

The existing 2019 closure-shaped run timestamps (627) are exactly shared across the four pairs, but closure status is not independently documented.

Next: repeat the exact same membership analysis in the 2016–2018 development-only ledgers, without opening candle prices or protected years. Original quarantines, evidence bytes, calendar and strategy authority untouched; no new provider charges.
