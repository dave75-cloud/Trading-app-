# AUDUSD 2015 pilot calendar-evidence hardening

Experiment: `EXP-20260929T114553Z-audusd-2015-pilot-calendar-hardening`

## Pilot result

The first real OANDA historical pilot shard completed for AUDUSD/2015 and
passed independent structural verification.

The authoritative RND-0030 schedule comparison found 849 missing and 255
unexpected timestamps. The shard remains quarantined and unsealed.

## Falsification result

A non-authoritative candidate that adds the 17:00 New York M5 start reduces
unexpected observations from 255 to one. This is strong evidence against
applying the present-day 17:05 baseline unchanged to 2015, but returned candles
cannot authorize a historical-calendar rewrite.

The sole remaining unexpected timestamp is Friday 2015-08-28 17:05 New York.

## Gap structure

Under the diagnostic candidate schedule, 856 timestamps remain missing. Three
large closure-shaped runs contain 648 bars. The remaining 208 bars occur in
short runs and remain explicit source gaps.

No missing value is synthesized. No long run is promoted to a holiday closure
without independent historical evidence.

## Documentary review

Current official OANDA material supports the present 17:05-16:59 ordinary
session and the existence of holiday-specific schedule changes. Current OANDA
legal material also describes FX availability approximately as 5 p.m. Sunday
through 5 p.m. Friday New York.

The review did not locate authoritative surviving OANDA documentation that
pins the exact 2015 daily-break rule or exact 2015 holiday intervals. The
historical-calendar hypothesis therefore remains non-authoritative.

## Expansion boundary

Do not acquire the remaining 39 shards under this task. After exact-head
validation and human merge review, the next controlled expansion should test
the other three M005 pairs for UTC year 2015 before ten-year acquisition.

No M005 signals, trades or performance outcomes are permitted in RND-0031.
