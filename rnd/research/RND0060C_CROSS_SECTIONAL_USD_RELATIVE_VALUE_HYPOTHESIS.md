# RND-0060C — Development-Only Cross-Sectional USD Relative-Value Hypothesis

Status: PREDECLARED / NOT YET EXECUTED

## Scientific separation

This is an independent cross-sectional relative-value family. It is not a Q003 volatility-ratio variant, not an RND-0060A opening-range breakout variant, and not an RND-0060B single-pair displacement-fade or its inversion. It uses no Q003 prospective evidence, no consumed 2021–2022 validation evidence, and no 2023–2024 reserved-final evidence.

## Development evidence

2015-01-01T00:00:00Z through 2020-12-31T19:15:00Z exclusive, using the already admitted AUDUSD, EURUSD, GBPUSD and USDJPY M5 bid/ask/mid development evidence and frozen gap/accounting semantics.

## Single fixed hypothesis

At exactly 11:30 UTC on each weekday:

1. Require all four symbols to have complete, contiguous M5 observations from 11:00 through 11:30 UTC inclusive. This supplies six contiguous five-minute intervals and seven mid closes per symbol.
2. Compute each symbol's raw 30-minute mid-close return from 11:00 to 11:30.
3. Convert each raw return to USD-strength orientation:
   - AUDUSD, EURUSD, GBPUSD: USD-oriented return = -raw return;
   - USDJPY: USD-oriented return = +raw return.
4. For each symbol, compute a leave-one-pair-out peer mean from the other three USD-oriented returns and define residual = symbol USD-oriented return - peer mean.
5. Select the single symbol with the largest absolute residual. If the maximum absolute residual is tied exactly, declare no trade for that day.
6. Trade only that selected outlier toward cross-sectional convergence:
   - if its residual says USD is unusually strong in that pair, position for USD weakening in that pair;
   - if its residual says USD is unusually weak in that pair, position for USD strengthening in that pair.
   Operational side mapping is fixed: for AUDUSD/EURUSD/GBPUSD, side = sign(residual); for USDJPY, side = -sign(residual).
7. No minimum residual threshold is used. This avoids introducing a tunable displacement cutoff.
8. Execute on the next contiguous complete M5 bar at 11:35 UTC, using ask for long entry and bid for short entry. If that bar is missing or non-contiguous, cancel the day's pending signal.
9. Hold exactly three subsequent genuine observed M5 bars after the entry bar, then exit using bid for long and ask for short. Missing nominal bars do not count; an already-open economic position survives a gap under frozen RND-0034 semantics.
10. Maximum one portfolio trade per weekday.

## Search space

None. Declared trial count: 1.
No alternative observation time, lookback, residual threshold, peer construction, tie rule, holding period, pair exclusion, pair-specific parameter, volatility filter, Q003 filter, weighting, stop, target, or cost filter is authorized.

## Predeclared readout

Report per pair and portfolio:
- trade count;
- terminal net equity;
- realized net sum;
- max drawdown;
- annual realized net contribution for 2015–2020;
- bid/ask cost drag;
- leave-one-pair-out aggregate realized net sum;
- selected-pair counts.

Portfolio accounting uses the existing fixed-one-return-unit-per-pair concurrent path normalized as 1 + equal-unit P&L / 4. It is research accounting only, not capital sizing.

## Development falsification screen

The mechanism is only eligible for a later candidate-review task if all are true on development evidence:
- portfolio terminal net equity > 1.0;
- portfolio realized net sum > 0;
- at least 3 of 4 pair terminal net equities >= 1.0;
- portfolio max drawdown >= -0.10;
- at least 4 of 6 development years have positive aggregate realized net contribution;
- every leave-one-pair-out aggregate realized net sum > 0;
- integrity/reconciliation checks pass.

Failure of any criterion closes RND-0060C as development-falsified. Passing only permits a separate human-reviewed candidate-review task; it does not authorize validation, shadow, promotion, reserved-final access, broker writes or capital allocation.
