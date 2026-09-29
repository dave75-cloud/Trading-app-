# RND-0033 — development-history expansion

Experiment: `EXP-20260929T133500Z-development-history-expansion`

RND-0033 expands from the 2015 four-pair pilot into 2016-2019 for all four M005
pairs. These sixteen new shards are wholly before the UTC year containing the
predeclared development/validation boundary.

The task remains outcome-blind. It tests persistence or change in timestamp,
gap and non-authoritative 17:00 New York structure only.

No calendar regime is promoted by empirical recurrence. No strategy outcome is
permitted. Acquisition and evidence results are pending.

## Acquisition incident

The first acquisition and one verified-resume retry failed closed because the
strict shared parser rejected an OANDA page with zero candles. A credential-
safe diagnostic reproduced the condition at AUDUSD 2017 page 22:
2017-12-31T14:00:00Z through 2018-01-01T00:00:00Z, candles=0.

The correction is quarantine-specific: preserve/hash a valid empty raw page,
record candle_count=0 and empty_raw_page_count, contribute no canonical rows,
and leave schedule/gap accounting independent. The shared parser remains
strict. Revalidation and acquisition retry are pending.
