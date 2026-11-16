# RND-0074 — Calendar missingness, source provenance, and downstream bias protocol

**Disposition: CONTINUE_METADATA_ONLY; NO-GO historical economic-data admission.** No changes to frozen trading machinery, original evidence, or broker authority.

## Established operator-observed baseline (not findings of the new module)

2019 New York illustrative local close, +15/+20 min, excluding local Jan 1/Dec 25 **for sensitivity only**: AUDUSD missing 43/259 at +15 and 32/259 at +20; combined **75 missing out of 518 pair-offset opportunities**, on **68 distinct local dates**; cross-pair membership among these AUDUSD missing opportunities: **70 AUDUSD only; 5 additionally missing in exactly one other pair**. These are recorded ledger missing timestamps. They do not establish market closures, source-candle authenticity, a liquidity mechanism, or performance.

The operator observed only four of sixteen 2016–2019 original `standard_schedule.json` files: AUDUSD/2016, AUDUSD/2017, AUDUSD/2019 and EURUSD/2018. The other twelve are missing. All four 2019 quarantine manifests declare the same schedule file digest `d3bd447bc9d8757bc11f3fe57c9e872e1f661a0447eba541dd199a02aadaf66b`; surviving AUDUSD/2019 file is 1,947,585 bytes and matches. **Matching expected bytes across manifests are not evidence that the three missing original files were physically present at acquisition time.**

## A. Source-provenance investigation (no restoration)

1. Inventory each of 16 year/pair source directories, manifest hash declarations and physical schedule presence; record which *surviving* files hash-match their own manifest. Attribute cause of absent originals **UNKNOWN**, not inferred from file or parent directory modification dates.
2. Check any existing original acquisition logs, read-only external backups or original RND-0030 verification records for evidence of schedule creation or later removal. Do not search protected validation years. Any restoration requires separate explicit approval and independently hash-matched immutable copies; never silently write originals.
3. Verify that a shared schedule is only substituted for diagnostics where pair/year manifest SHA-256 matches the reference year; never reuse 2019 reference for 2016–2018.
4. Independently rerun full RND-0030 raw-page/canonical evidence provenance before any future economic-data admission. Current RND-0074 hashing of price files as opaque bytes is only a **limited** check.

## B. Predeclared calendar-stratification procedure

New script `rnd/tools/rnd0074_audusd_calendar_stratification.py`, using the shared-reference original-file verifier, inspects 2019 AUDUSD illustrative NY CLOSE local date windows at offsets +15 and +20 only. Emits counts by local month, weekday, and offset, separately for all eligible weekdays (primary) and exclusion of local January 1 and December 25 (sensitivity). Each cell has eligible count, missing count, present count, coverage percent and distinct affected dates. Also emits **union** distinct affected dates, and exact four-pair membership for AUDUSD missing timestamps. Output contains no specific timestamp lists, price data, or trade outcomes. Both views must internally reconcile stratified missing and eligible totals. The operator will compare the sensitivity totals to previously observed 75/68/70/5, rather than hardcoding these targets.

Date strata are descriptive, not validated market calendars or causal tests. Small monthly denominator cells and overlapping offsets make independence assumptions dubious. Differences in missingness across weekdays or DST regimes may indicate **sampling/clock/provider artefacts**; this module does not establish which.

## C. Potential selection-bias implications and future gates

- If missing candles occur nonrandomly around a targeted signal or execution time, a naïve complete-case backtest can over-represent readily observable periods and omit difficult market states. This is a **risk hypothesis**, not evidence of realised profit/loss bias.
- Day/weekday/session-time concentration can distort opportunity counts, overnight carry boundaries, costs and apparent regime balance even if raw returns are never examined.
- Guardrails for a *future separately authorised* backtest: log an explicit missingness mask **before** computing signals; report eligibility denominators and attrition by pair/window/month/weekday; pre-specify no-trade/skip rules for missing data and prohibit look-ahead or forward-fill across missing candles; analyse sensitivity to removing affected dates and to alternative admissible calendar conventions; segregate development, validation and reserved final periods. These are design requirements, not authority to run a backtest.
- No economic effect sign, magnitude, or causal attribution is knowable from ledger missingness alone.
- Admission remains blocked pending authentic source provenance, documented historical OANDA calendar, documented missing original files, and explicit human economic-data access decision.

## D. Test gate

Run the new synthetic test module locally on exact Git commit. It tests real symlink rejection at file/directory/root levels, schema-independent pure missingness aggregation and reconciliation, holiday sensitivity, and no-admission flags. These tests do not prove end-to-end original-source authenticity. On pass, run one bounded operator read-only AUDUSD 2019 metadata stratification and inspect the compact output before any further phase.

**No merge, original archive writes, protected data access, provider purchase, strategy adjustment, trading or capital authority.**
