# RND-0074 — AUDUSD 2019 NY closing offset exact cross-pair missingness

**Operator-reported, development-only read-only timestamp diagnostic. Evidence remains quarantined, and no economic/strategy admission follows.**

Scope: 2019 weekdays other than January 1 and December 25, at 16:15 and 16:20 America/New_York local time (illustrative 16:00 session close plus 15/20 minutes). All checks used existing RND-0033 development discrepancy-ledger missing timestamp sets for AUDUSD, EURUSD, GBPUSD and USDJPY, with no quote or price reading.

Of **75 AUDUSD missing M5 timestamps**, **70** were absent from no other pair's *missing timestamp ledger*, **5** were absent from exactly one other pair, **0** from exactly two other pairs, and **0** from all three other pairs. The counts sum to 75. Thus **70/75 = 93.33%** of these AUDUSD absences are pair-specific by the other pairs' missing-ledger membership. Their timestamp presence in the other pairs' ledgers is not independently checked here as valid bid/ask liquidity, executable prices or even canonical semantic correctness.

This strengthens the descriptive conclusion of instrument-specific AUDUSD candle availability at these offsets throughout 2019. It does **not** identify the causal mechanism: provider non-generation, vendor response behaviour, upstream acquisition effects and source/reference calendar limitations remain unresolved. Do not replace missing candles with other instruments, invent values, drop these minutes retroactively, change source manifests, alter the canonical schedule or claim trading edge.

**Disposition:** further read-only metadata analysis may continue; source status remains `QUARANTINED_UNRESOLVED_DISCREPANCIES` and `seal_allowed=False`. Historical evidence admission, spread/price access, performance/strategy testing, protected-year access, broker authority, calendar promotion and paid data subscriptions all remain **NO-GO absent separately documented human review and authorization**.

**Next design work:** a versioned, outcome-blind pair × session × local clock-offset exposure/missingness protocol with complete denominator accounting, DST/calendar ambiguity, monthly/weekday sensitivity, and an explicit operator decision gate before any economic data access. The limited metadata hash checks are not the full RND-0030 source verifier.
