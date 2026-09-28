# Predeclared historical window and sealed chronological partition

Experiment: `EXP-20260928T140147Z-historical-window-partition`

## Question

Can the project bind a useful historical horizon and an untouched final-test
period before any M005 outcome is calculated?

## Predeclared rule

The requested horizon is 2015-01-01T00:00:00Z through
2025-01-01T00:00:00Z. Partitions are based on elapsed UTC time at 60/20/20 and
snapped forward to the next M5 boundary.

This produces:

- development ending 2020-12-31T19:15:00Z;
- validation ending 2023-01-01T09:40:00Z;
- reserved final test ending 2025-01-01T00:00:00Z.

All four fixed M005 symbols must satisfy the complete requested horizon or the
evidence gate fails closed. No outcome-dependent common-coverage fallback is
permitted.

## Boundary

The final-test boundary becomes known but remains sealed. Structural identity,
coverage and completeness may be checked; signals, trades, strategy metrics,
parameter selection and ranking remain prohibited.

No OANDA historical request has been made by this experiment. Binding an
acquisition declaration is not execution authority and does not itself fetch
data.
