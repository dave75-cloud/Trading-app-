# RND-0060B — Development-Only Intraday Displacement Mean-Reversion Hypothesis

Status: PREDECLARED / NOT YET EXECUTED

## Scientific separation

RND-0060B is a new independent mechanism family. It is not a Q003 volatility/friction threshold variant and not an RND-0060A breakout continuation variant. It uses no Q003 prospective evidence, no consumed 2021–2022 validation evidence, and no 2023–2024 reserved-final evidence.

## Development evidence

2015-01-01T00:00:00Z through 2020-12-31T19:15:00Z exclusive, using the already admitted four-pair M5 bid/ask/mid development evidence and frozen RND-0034 gap semantics.

## Single fixed hypothesis

For each symbol independently, during its already frozen UTC session only:

1. Require 7 immediately consecutive complete M5 observations: the current eligible session bar plus the six immediately preceding contiguous complete M5 bars.
2. Compute six-bar displacement from the mid close six bars earlier to the current mid close:
   `displacement = current_mid_close / mid_close_6_bars_earlier - 1`.
3. Use one fixed absolute displacement threshold of 0.0020 (20 basis points).
4. On the first eligible session bar of the day satisfying the threshold:
   - if displacement >= +0.0020, declare SHORT mean reversion;
   - if displacement <= -0.0020, declare LONG mean reversion;
   - otherwise no signal.
5. Execute on the next eligible contiguous M5 bar using bid for short entry and ask for long entry.
6. Hold exactly 3 genuine observed eligible bars after entry, then exit using ask for short and bid for long.
7. A gap before execution cancels the pending signal. A gap while an economic position is open follows frozen RND-0034 semantics: the position survives; missing nominal bars do not count toward holding time; observed bars resume the count.
8. Maximum one trade per symbol/day. Once a signal has occurred, no later same-day signal is permitted even if the pending entry is cancelled by a gap.

## Search space

None. Declared trial count: 1.
No alternative displacement threshold, lookback, hold, session, entry delay, pair-specific parameter, pair dropping, weighting, volatility filter, spread filter, Q003 ratio filter, or RND-0060A breakout condition is authorized.

## Predeclared readout

Report per pair and portfolio:
- trade count;
- terminal net equity;
- realized net sum;
- max drawdown;
- annual realized net contribution for 2015–2020;
- bid/ask execution cost drag;
- leave-one-pair-out aggregate realized net sum.

Portfolio accounting is frozen before outcomes as the existing fixed-one-return-unit-per-pair concurrent path normalized as `1 + equal_unit_pnl / 4`; no capital sizing is introduced.

## Development falsification screen

The mechanism is only eligible for a later candidate-review task if all are true on development evidence:
- portfolio terminal net equity > 1.0;
- portfolio realized net sum > 0;
- at least 3 of 4 pair terminal net equities >= 1.0;
- portfolio max drawdown >= -0.10;
- at least 4 of 6 development years have positive aggregate realized net contribution;
- every leave-one-pair-out aggregate realized net sum > 0;
- integrity/reconciliation checks pass.

Failure of any criterion closes RND-0060B as development-falsified. Passing grants only eligibility for a later human candidate-review task. It does not authorize validation, shadow, promotion, reserved-final access, broker writes, capital allocation, or live authority.
