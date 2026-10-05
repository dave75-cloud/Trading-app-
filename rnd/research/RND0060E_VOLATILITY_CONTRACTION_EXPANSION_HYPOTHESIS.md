# RND-0060E — Volatility Contraction → Expansion

## Status
PREDECLARED / DEVELOPMENT-ONLY / ONE TRIAL / NO PARAMETER SEARCH

## Independence
This study is independent of Q003 and of RND-0060A/B/C/D. It does not use prior outcome results to choose direction, threshold, pair, time, lookback, or hold period.

## Development evidence
Only DEVELOPMENT_2015_2020 is authorized:
- start inclusive: 2015-01-01T00:00:00Z
- end exclusive: 2020-12-31T19:15:00Z
- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY
- M5 canonical bid/ask/mid complete candles
- RND-0034 gap semantics

Validation 2021–2022 and reserved final 2023–2024 remain closed.

## Frozen sessions
- AUDUSD: [11:00, 14:00) UTC
- EURUSD: [11:00, 13:00) UTC
- GBPUSD: [11:00, 13:00) UTC
- USDJPY: [11:00, 13:00) UTC

## Frozen observation state
For each symbol and weekday, evaluate one contraction state at exactly 11:30 UTC.

Require 24 immediately preceding contiguous complete M5 observations ending at 11:30 UTC, i.e. timestamps 09:35 through 11:30 inclusive (23 five-minute intervals, 24 observed bars).

Define:
- baseline window = first 18 bars (09:35 through 11:00 inclusive)
- short window = most recent 6 bars (11:05 through 11:30 inclusive)
- baseline range = max(mid_high) - min(mid_low) over baseline window
- short range = max(mid_high) - min(mid_low) over short window

A valid contraction requires:
1. baseline range > 0
2. short range > 0
3. short_range <= baseline_range / 3

If the 24-bar window is incomplete or non-contiguous, there is no contraction event that day.

## Frozen breakout rule
After a valid 11:30 contraction event, monitor subsequent eligible contiguous complete M5 bars within the symbol's frozen session.

The contraction range is the short-window high/low:
- contraction_high = max(mid_high) over the 6-bar short window
- contraction_low = min(mid_low) over the 6-bar short window

The first subsequent bar whose mid_close is:
- strictly above contraction_high => LONG breakout signal
- strictly below contraction_low => SHORT breakout signal

A close exactly equal to a boundary is not a breakout.

Only the first breakout signal may be used. Maximum one trade per symbol/day.

If no breakout occurs before the frozen session closes, there is no trade that day.

## Entry
Entry is delayed by exactly one eligible contiguous M5 bar after the breakout signal.

The delayed entry bar must:
- exist contiguously after the signal bar
- remain inside the same frozen session and same UTC date

Otherwise the pending signal is cancelled.

Execution:
- LONG enters at ask close
- SHORT enters at bid close
- signal logic uses mid prices only

## Hold / exit
Hold exactly 3 subsequent genuine observed complete M5 bars after the entry bar.

The entry bar does not count as holding bar 1.

Exit:
- LONG at bid close
- SHORT at ask close

If a gap occurs while the economic position is open:
- the position survives
- missing bars do not count toward the 3-bar hold
- the next genuine observation resumes holding-bar counting
- gap exposure is recorded

## Prohibited variations
No alternate:
- observation timestamp
- 6-bar short window
- 18-bar baseline window
- 1/3 contraction ratio
- use of close-only range in place of high/low range
- breakout buffer
- reverse-direction breakout
- entry delay
- hold period
- pair-specific rules
- pair dropping
- weights
- volatility or spread filters
- Q003 references
- parameter search

## Trial count
Exactly 1 declared trial.

## Readout
For each symbol and the four-pair portfolio report:
- contraction-event count
- breakout-signal count
- trade count
- terminal net equity
- realized net sum
- max drawdown
- execution cost drag
- annual realized net 2015–2020
- leave-one-pair-out realized net sum
- integrity reconciliation

## Falsification screen
`ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW` only if ALL are true:
- portfolio terminal normalized net equity > 1
- portfolio realized net sum > 0
- at least 3 of 4 pair terminal net equities >= 1
- portfolio max drawdown >= -0.10
- at least 4 of 6 development years have positive aggregate realized net
- every leave-one-pair-out realized net sum > 0
- integrity reconciliation passes

Any failure => `DEVELOPMENT_FALSIFIED`.

No EXTEND, rescue, tuning, validation opening, promotion, capital allocation, broker writes, or automatic merge follows from this study.
