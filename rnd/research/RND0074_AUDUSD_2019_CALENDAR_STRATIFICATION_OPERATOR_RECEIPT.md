# RND-0074 — AUDUSD 2019 calendar-stratification operator receipt

**Operator output: AUDUSD_2019_CALENDAR_STRATIFICATION_METADATA_ONLY_PASS; admitted=False.**

Script: `rnd0074_audusd_calendar_stratification.py` with original 2019 four-pair quarantined ledger evidence and a SHA-matched AUDUSD common schedule; no price parsing, strategy evaluation, archive writes or broker permissions.

## Results (2019 illustrative NEW_YORK_CLOSE +15 and +20 minutes)

| Measure | Primary | Exclude local Jan 1 and Dec 25 (sensitivity only) |
| --- | ---: | ---: |
| Eligible pair-offset observations | 522 | 518 |
| Missing +15 | 45 | 43 |
| Missing +20 | 34 | 32 |
| Total missing | 79 | 75 |
| Missing rate | 15.13% | 14.48% |
| Distinct affected local dates | 70 | 68 |
| AUDUSD-missing timestamps shared by exactly 1 / 2 / 3 / 4 pairs (including AUDUSD) | 70 / 5 / 0 / 4 | 70 / 5 / 0 / 0 |

The four extra missing observations in the primary view correspond to the four two-offset slots on the two excluded local dates; four-pair missingness there is consistent with a common-calendar effect but does NOT establish closure.

## Monthly sensitivity: missing / eligible

Jan 7/44; Feb 5/40; Mar 3/42; Apr 4/44; May 8/46; Jun 10/40; Jul 12/46; Aug 3/44; Sep 4/42; Oct 7/46; Nov 8/42; Dec 4/42. Monthly missing sum 75; denominator sum 518. Highest proportions: July 26.09%, June 25%; lowest August 6.82%, March 7.14%.

## Weekday sensitivity: missing / eligible

Monday 20/104 (19.23%); Tuesday 15/104 (14.42%); Wednesday 17/102 (16.67%); Thursday 10/104 (9.62%); Friday 13/104 (12.50%). Totals reconcile: 75/518.

## Interpretation and limitations

A visible nonuniform temporal missingness pattern is a **descriptive** result from one calendar year and two adjacent offsets. It is not proof of non-random data-generation, a statistically significant seasonal/weekday effect, precise OANDA calendar closures, or economically exploitable signal. Adjacent offsets and overlapping dates are not independent observations; month-versus-weekday differences might be explained by calendar clustering. The shared-reference workaround verifies declared schedule bytes, not missing original files or full RND-0030 source provenance.

Research implications for *future explicitly approved* economic testing: predeclare timestamp eligibility masks; retain per-window/weekday/month attrition denominators; fail closed on missing signal/execution data; avoid forward-filling through missing bars; sensitivity-check excluding affected dates and alternative authenticated schedule conventions; never assume resulting performance bias direction.

Open issues: provenance of twelve missing 2016–2019 original standard schedules; original full source verification; authenticated historical schedule; further end-to-end adversarial tests. **CONTINUE_METADATA_ONLY; NO-GO historical economic-data admission and trading/strategy changes.**
