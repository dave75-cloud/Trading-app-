# RND-0060A — Development Falsification Post-Mortem

Status: CLOSED — DEVELOPMENT_FALSIFIED

## Outcome

The single predeclared opening-range breakout trial failed the development falsification screen on admitted 2015–2020 evidence.

Portfolio:
- final equal-unit normalized equity index: 0.9703362710479074
- realized completed-trade net return sum: -0.11865491580837043
- equal-unit normalized max drawdown: -0.0302710707545224

Per symbol:
- AUDUSD: 266 trades; terminal net equity 0.9558174007147874; realized net sum -0.04511173346095481; max drawdown -0.045996429116948345; cost drag 0.03410309882513331
- EURUSD: 271 trades; terminal net equity 0.9870374798936657; realized net sum -0.013010617085377136; max drawdown -0.017181085848852584; cost drag 0.016397099412682498
- GBPUSD: 279 trades; terminal net equity 0.9511333401451931; realized net sum -0.0500190101096318; max drawdown -0.050041577481080624; cost drag 0.03141442233364843
- USDJPY: 238 trades; terminal net equity 0.9895195045532978; realized net sum -0.010513555152406682; max drawdown -0.013993920703863072; cost drag 0.016503526652653335

Annual aggregate realized net contribution:
- 2015: -0.022486581773535325
- 2016: -0.02582602532800876
- 2017: -0.004570412731112054
- 2018: -0.006524469653334242
- 2019: -0.027996070519797737
- 2020: -0.0312513558025823

Leave-one-pair-out realized net sum:
- exclude AUDUSD: -0.07354318234741561
- exclude EURUSD: -0.10564429872299329
- exclude GBPUSD: -0.06863590569873862
- exclude USDJPY: -0.10814136065596375

## Falsification criteria

Passed:
- integrity/reconciliation
- portfolio max drawdown >= -0.10

Failed:
- portfolio terminal net equity > 1.0
- portfolio realized net sum > 0
- at least 3 of 4 pair terminal net equities >= 1.0
- at least 4 of 6 development years positive
- every leave-one-pair-out aggregate realized net sum > 0

## Scientific interpretation

This is not a near miss. All four pairs are below 1.0 terminal net equity, all six development years have negative aggregate realized net contribution, and every leave-one-pair-out portfolio remains negative. The mechanism therefore fails cross-pair, cross-year and concentration-robustness screens simultaneously.

The low drawdown is not evidence of useful edge; it reflects a relatively weak-loss profile rather than positive expectancy. Execution cost drag is material but cannot explain the failure away under the frozen design because net results are negative across every pair and year and the predeclared study does not authorize cost-rescue or parameter tuning.

## Closure rule

RND-0060A is closed as DEVELOPMENT_FALSIFIED. No buffer tuning, lookback tuning, hold tuning, session tuning, pair dropping, weighting, volatility filters, ratio filters, validation opening, reserved-final access, shadowing, promotion, broker writes or capital allocation are authorized from this result.

Any follow-up must be a separate independently predeclared hypothesis family under the RND-0060 research firewall.
