# RND-0060D — Three-Bar Directional Persistence

Status: PREDECLARED / NOT YET EXECUTED

## Research question

Does short-horizon serial directional persistence exist after three immediately consecutive same-sign M5 mid-close returns, net of bid/ask execution costs, across the fixed four-pair development universe?

This is an independent mechanism study. It does not reuse Q003, RND-0060A, RND-0060B, or RND-0060C signal logic and must not be modified after observing development outcomes.

## Authorized evidence

Development evidence only:

- 2015-01-01T00:00:00Z inclusive
- 2020-12-31T19:15:00Z exclusive
- AUDUSD, EURUSD, GBPUSD, USDJPY
- admitted M5 bid/ask/mid complete candles
- existing RND-0034 gap semantics

Validation 2021-2022 and reserved final 2023-2024 remain closed.

## Fixed sessions

Use the already frozen UTC session windows:

- AUDUSD: 11:00 <= UTC < 14:00
- EURUSD: 11:00 <= UTC < 13:00
- GBPUSD: 11:00 <= UTC < 13:00
- USDJPY: 11:00 <= UTC < 13:00

## Fixed signal rule

For each symbol and UTC calendar day:

1. Consider only complete M5 bars inside that symbol's frozen session.
2. A signal requires four immediately consecutive session bars on the M5 grid, producing exactly three contiguous mid-close returns.
3. If all three returns are strictly positive, signal LONG on the close of the fourth bar.
4. If all three returns are strictly negative, signal SHORT on the close of the fourth bar.
5. A zero return breaks the streak and produces no signal.
6. The first qualifying streak of the symbol/day is the only signal opportunity for that symbol/day. No later same-day signal may replace it.
7. There is no minimum return magnitude, volatility filter, spread filter, trend filter, price-level filter, cross-pair filter, or Q003-derived filter.

## Fixed execution rule

1. Enter on the next immediately contiguous M5 bar after the signal bar.
2. The entry bar must remain inside the same frozen session; otherwise cancel the pending signal.
3. LONG entry uses ask close. SHORT entry uses bid close.
4. The entry bar itself does not count as holding bar 1.
5. Hold exactly three subsequent genuine observed bars.
6. LONG exit uses bid close. SHORT exit uses ask close.
7. A gap before delayed entry cancels the pending signal.
8. A gap while an economic position is open does not close the position; missing nominal bars do not count toward the three-bar hold. The next genuine observed bars continue the hold under RND-0034 economic-position semantics.
9. Maximum one trade per symbol/day.

## Search space

NONE.

Declared trial count: 1.

Forbidden after outcome observation:

- alternative streak lengths;
- reverse-direction / mean-reversion version of the same streak;
- alternative holding periods;
- alternative entry delay;
- minimum move thresholds;
- pair dropping or pair-specific rules;
- session changes;
- volatility, spread, cost, or Q003 filters;
- weighting or portfolio optimization;
- any parameter search.

## Predeclared readout

Per pair and portfolio:

- trade count;
- terminal net equity;
- realized net return sum;
- maximum drawdown;
- annual realized net contribution for 2015-2020;
- bid/ask execution cost drag;
- leave-one-pair-out aggregate realized net return sum.

## Development falsification screen

RND-0060D is eligible only for later candidate-review discussion if ALL are true:

1. portfolio terminal net equity > 1.0;
2. portfolio realized net sum > 0;
3. at least 3 of 4 pair terminal net equities >= 1.0;
4. portfolio maximum drawdown >= -0.10;
5. at least 4 of 6 development years have positive aggregate realized net contribution;
6. every leave-one-pair-out aggregate realized net sum > 0;
7. integrity/reconciliation passes.

If any criterion fails, classification is DEVELOPMENT_FALSIFIED.

If all criteria pass, classification is only ELIGIBLE_FOR_LATER_CANDIDATE_REVIEW.

Neither outcome grants validation access, final-test access, broker-write authority, capital authority, promotion authority, or merge authority.
