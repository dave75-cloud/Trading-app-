# RND-0060A — Development-Only Opening-Range Breakout Hypothesis

Status: PREDECLARED / NOT YET EXECUTED

## Scientific separation

This child task is independent of the Q003 ratio threshold and the exhausted R000 absolute-volatility threshold line. It uses no Q003 prospective evidence, no 2021–2022 consumed validation evidence, and no 2023–2024 reserved-final evidence.

## Development evidence

2015-01-01T00:00:00Z through 2020-12-31T19:15:00Z exclusive, using the already admitted four-pair M5 bid/ask/mid development evidence and RND-0034 gap semantics.

## Single fixed hypothesis

For each symbol/day and its already frozen UTC session start:

1. Require 12 immediately preceding eligible contiguous complete M5 bars before the first eligible session bar.
2. Compute the maximum mid high and minimum mid low across those 12 pre-session bars.
3. On the first eligible session bar only:
   - if its mid close is strictly above the 12-bar pre-session high, declare LONG;
   - if its mid close is strictly below the 12-bar pre-session low, declare SHORT;
   - otherwise no trade for that symbol/day.
4. Execute on the next eligible contiguous M5 bar using ask for long entry and bid for short entry.
5. Hold exactly 3 eligible contiguous bars, then exit using bid for long and ask for short.
6. A gap before execution cancels the pending signal; a gap during an open economic position follows the frozen RND-0034 economic-position gap semantics.
7. Maximum one trade per symbol/day.

## Search space

None. Declared trial count: 1.
No breakout buffer, lookback alternatives, hold alternatives, session alternatives, pair-specific parameters, pair dropping, weighting, volatility filters or ratio filters are authorized.

## Predeclared readout

Report per pair and portfolio:
- trade count;
- terminal net equity;
- realized net sum;
- max drawdown;
- annual realized net contribution for 2015–2020;
- bid/ask cost drag;
- leave-one-pair-out aggregate realized net sum.

## Development falsification screen

The mechanism is only eligible for a later candidate-review task if all are true on development evidence:
- portfolio terminal net equity > 1.0;
- portfolio realized net sum > 0;
- at least 3 of 4 pair terminal net equities >= 1.0;
- portfolio max drawdown >= -0.10;
- at least 4 of 6 development years have positive aggregate realized net contribution;
- every leave-one-pair-out aggregate realized net sum > 0;
- integrity/reconciliation checks pass.

Failure of any criterion closes RND-0060A as development-falsified. Passing does not authorize validation, shadow, promotion, reserved-final access, broker writes or capital allocation.
