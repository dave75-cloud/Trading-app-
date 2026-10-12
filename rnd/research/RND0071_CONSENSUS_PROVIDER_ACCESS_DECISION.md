# RND-0071 — Historical Consensus Provider Access Decision

## Status
GOVERNED SOURCE-SELECTION DECISION — OUTCOME-BLIND — NO PROVIDER PURCHASE — NO FX OUTCOMES OPENED

## Purpose
Select the cheapest defensible path for obtaining historical, point-in-time market consensus required by RND-0070, without weakening provenance standards or creating vendor lock-in.

## Inheritance
RND-0071 inherits unchanged:
- RND-0064 canonical provenance requirements;
- RND-0066 split-source architecture;
- RND-0067 verified FRED/ALFRED actual-value and revision backbone;
- RND-0069 verified official BLS historical timing adapter;
- RND-0070 historical consensus provenance admission standard.

The only unresolved input is defensible contemporaneous pre-release market consensus.

## Provider comparison

### Financial Modeling Prep (FMP)
Strengths:
- low-cost and free access tiers;
- economic calendar exposes date, previous, estimate and actual;
- documentation states calendar times are UTC.

Limitation:
- public documentation describes a continuously refreshed economic calendar and an `estimate` field, but does not establish a preserved point-in-time snapshot or prove that a historical estimate is exactly the pre-release consensus that was visible before publication;
- no documented point-in-time calendar endpoint or consensus-capture timestamp was identified.

Decision: `NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF`.

FMP may be reconsidered only if the provider supplies documentary evidence establishing immutable or reconstructable pre-release consensus snapshots for the required historical period.

### Finnhub
Strengths:
- dedicated global economic-data product;
- advertises 10 years of economic-calendar history;
- current price approximately USD 50/month, billed quarterly.

Limitations:
- public documentation reviewed does not establish that historical calendar estimate values are preserved point-in-time consensus snapshots rather than current/restated historical fields;
- advertised 10-year calendar depth in 2026 does not safely establish complete coverage of the 2015 boundary required by DEVELOPMENT_2015_2020.

Decision: `NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF`.

### EODHD
Strengths:
- explicit economic-event API with estimate, actual and previous values;
- free API-key entry point exists.

Limitation:
- provider explicitly states economic-event data are available only from 2020.

Decision: `REJECT_INSUFFICIENT_HISTORY_FOR_DEVELOPMENT_2015_2020`.

### Trading Economics
Strengths:
- explicit point-in-time economic-calendar documentation intended for backtesting without look-ahead;
- schema defines `Forecast` as consensus from a representative group of economists;
- schema separately defines `TEForecast` as Trading Economics' own projection;
- historical examples predate the development interval and demonstrate date-ranged calendar retrieval;
- current Standard API plan includes Economic Calendar access.

Current cost discipline:
- Standard plan: USD 49 one-week trial, then USD 199/month;
- trial limit: 100 requests and 100,000 data points;
- this is materially cheaper than the previously considered Professional trial and is sufficient for a tiny predeclared provenance pilot.

Decision: `PREFERRED_BOUNDED_PROVENANCE_PILOT_CANDIDATE`.

## Correction to prior cost assumption
Earlier project discussion treated the Professional USD 99 trial as the first API-capable Trading Economics option. Current official pricing shows that the Standard plan also includes API and Economic Calendar access with a USD 49 one-week trial. RND-0071 supersedes the earlier cost assumption.

## Governed recommendation
Do not purchase or begin a trial yet.

First build and hostile-test an offline Trading Economics consensus acquisition adapter with:
- frozen 2019-Q1 US CPI scope only;
- point-in-time endpoint construction;
- `Forecast` accepted only as consensus;
- `TEForecast` explicitly rejected as a consensus substitute;
- API credentials only via environment variable;
- secret redaction from logs/receipts;
- immutable raw-response hashing;
- predeclared request budget <= 10 calls for the pilot;
- no FX, returns, P&L, strategy signals, validation, reserved-final or prospective outcomes;
- provider-purchase authority false.

Only after that machinery passes local hostile tests may a human choose whether to activate the USD 49 Standard trial.

## Exit decision
RND-0071 status is complete when the repository enforces this provider classification and no-cost-before-machinery rule.

## Authority
No provider purchase authority.
No trial activation authority.
No market-outcome access.
No validation access.
No reserved-final access.
No prospective-outcome access.
No broker-write authority.
No capital authority.
No live-execution authority.
No automatic merge.
