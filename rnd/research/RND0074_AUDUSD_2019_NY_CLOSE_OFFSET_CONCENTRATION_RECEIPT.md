# RND-0074 — AUDUSD 2019 NY CLOSE Gap Concentration Receipt

**Status: OPERATOR-REPORTED METADATA-ONLY DIAGNOSTIC; NO ADMISSION OR CAUSAL ATTRIBUTION.**

The operator applied an outcome-blind, read-only diagnostic to AUDUSD/2019 `standard_schedule.json` and `discrepancy_ledger.json` within the quarantined RND-0033 development archive. New York convention closing boundary = 16:00 local, 12 candidate M5 starting timestamps at offsets -30,-25,...,+25 minutes. Eligibility restricted to timestamps in original reference calendar; missing required membership in original missing ledger. This agrees with the earlier frozen-clock coverage pilot, which recorded 213 missing out of 3132 baseline-eligible labels (93.1992% coverage).

**Operator output:** `Total missing: 213`; `Affected dates: 120`; top 12 dates `2019-01-01=12, 2019-12-25=12, 2019-11-05=7, 2019-04-19=5, 2019-04-22=5, 2019-07-23=5, 2019-11-08=5, 2019-05-22=4, 2019-05-27=4, 2019-07-03=4, 2019-07-04=4, 2019-02-04=3`.

| Weekday | Missing pair-window timestamps |
|---|---:|
| Monday | 58 |
| Tuesday | 49 |
| Wednesday | 44 |
| Thursday | 28 |
| Friday | 34 |

| Minute offset relative to NY 16:00 | Missing |
|---|---:|
| -30 | 13 |
| -25 | 14 |
| -20 | 14 |
| -15 | 10 |
| -10 | 8 |
| -5 | 6 |
| 0 | 8 |
| +5 | 23 |
| +10 | 26 |
| +15 | 45 |
| +20 | 34 |
| +25 | 12 |
| **Total** | **213** |

Summaries: 65 before 16:00; 148 at/after 16:00; 128 at +5/+10/+15/+20 (60.1% of 213). Both January 1 and December 25 contribute 12 each, leaving 189 interval occurrences and 118 affected dates if those two dates are *excluded only as a sensitivity analysis* (not a modification of baseline or proof of historical closure).

**Critical interpretation limits:** The 16:00 local boundary is an illustrative predeclared clock convention, not a documentary OANDA close; this count cannot establish broker outage, market hours, or liquidity. No denominator adjustment by offset/weekday has yet been conducted; hourly prevalence and relative rates are not established. Some date-specific gaps might be acquisition issues or holiday effects. The per-instrument gap concentration is not an authorised reason to discard observations or promote the calendar. No actual market price, strategy return, signal, protected year, order endpoint or paid vendor queried.

**Recommended next test:** Perform the *same* predeclared offset aggregation for all four pairs, reporting expected and missing counts (and therefore rates) per offset, including an independently labelled diagnostic excluding Jan 1 / Dec 25 only. Establish whether AUDUSD +15/+20 concentration is pair-specific and persists outside those two dates. Keep original calendar and quarantine unchanged.
