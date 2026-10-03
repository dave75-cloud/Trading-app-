# RND-0036 — Remaining 2020 Development Acquisition and Seal

Status: **PREDECLARED / NOT YET AUTHORIZED TO ACQUIRE**

## Purpose

RND-0036 closes the only remaining historical-data gap in the predeclared RND-0029 development partition. It is an acquisition, quarantine, integrity and evidence-sealing task only. It is not a strategy experiment and must produce no M005, A016, Champion or other strategy outcomes.

## Exact scope

The authoritative RND-0029 development partition is:

- start: `2015-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`

RND-0031/32/33 already cover governed development evidence through 2019. Therefore RND-0036 may acquire only:

- start inclusive: `2020-01-01T00:00:00Z`
- end exclusive: `2020-12-31T19:15:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- granularity: M5
- provider/source semantics: existing OANDA PRACTICE historical acquisition declaration
- candle requirement: complete bid/ask/mid evidence only

The interval `2020-12-31T19:15:00Z` onward is validation and is prohibited from RND-0036 development evidence.

## Acquisition invariants

RND-0036 must reuse the existing governed acquisition/quarantine semantics established by RND-0028 through RND-0033:

1. Raw provider responses are immutable evidence.
2. Canonical rows are deterministic and identity-bound by SHA-256.
3. No synthetic candles, interpolation, backfill or invented prices.
4. Provider gaps are retained and classified; an empirical historical closure candidate is not documentary market-calendar authority.
5. Existing calendar-quarantine rules remain descriptive and fail-closed.
6. All four symbols must cover the exact authorized interval or the task does not graduate.
7. Any request or response containing a timestamp at or after the validation boundary must be rejected or quarantined outside the RND-0036 development evidence package.
8. No result may modify earlier RND-0031/32/33 evidence identities.

## Warmup

No additional earlier-period acquisition is needed merely for RND-0036 sealing. If a later development reconstruction requires warmup, the RND-0029 rule permits at most 50 prior M5 bars from the development partition for state initialization only; those rows may not generate trades or returns. Existing governed 2019 evidence is the source for such warmup.

## Explicit outcome prohibition

During RND-0036 acquisition and sealing, the following are prohibited:

- strategy signals;
- positions or trade simulation;
- P&L, returns, equity, drawdown, hit rate or strategy scores;
- comparing R000 with A016 or any other RND-0035 variant;
- extending the volatility-threshold grid;
- Champion reconstruction;
- parameter selection or strategy promotion.

The A016 development observation must not change the data interval, acquisition method, calendar treatment, inclusion rules or evidence thresholds.

## Required evidence package

The final RND-0036 evidence record must include, for each symbol:

- authorized interval;
- canonical row count;
- raw page/bundle identity;
- canonical rows SHA-256;
- expected/standard schedule identity where applicable;
- gap ledger and quarantine classifications;
- boundary proof showing no canonical row at or after `2020-12-31T19:15:00Z`;
- provider/source identity;
- acquisition completion state.

It must additionally report four-symbol common coverage and an overall PASS/FAIL seal.

## Graduation

RND-0036 may graduate only when all four symbol evidence packages are identity-bound and the exact truncated development interval is sealed. Graduation does **not** authorize strategy evaluation. A separate human-reviewed task must combine 2015–2020 development evidence and decide what fixed hypotheses, if any, may be evaluated.

## Authority

- validation open: **FALSE**
- reserved final test open: **FALSE**
- strategy selection: **FALSE**
- broker writes: **FALSE**
- portfolio sizing: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
