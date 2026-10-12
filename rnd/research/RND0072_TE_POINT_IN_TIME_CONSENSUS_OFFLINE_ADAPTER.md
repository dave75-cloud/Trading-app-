# RND-0072 — Trading Economics Point-in-Time Consensus Offline Adapter

## Status
GOVERNED OFFLINE ADAPTER — SYNTHETIC FIXTURES ONLY — NO PROVIDER ACCESS — NO FX OUTCOMES

## Purpose
Build and hostile-test the smallest adapter needed to admit historical pre-release survey consensus from a future bounded Trading Economics pilot without spending money, using credentials, or opening market outcomes.

## Inheritance
RND-0072 inherits RND-0062 through RND-0071 without relaxation. In particular:
- RND-0064 canonical macro-event provenance remains authoritative;
- RND-0069 provides independent official BLS exact timing for the frozen US CPI sample;
- RND-0070 requires historical point-in-time market consensus and prohibits model-forecast substitution;
- RND-0071 selects Trading Economics only as the preferred bounded pilot candidate, not as an authorized purchase.

## Provider semantics frozen from current documentation
For the Trading Economics economic calendar:
- `Forecast` = consensus forecast from a representative group of economists;
- `TEForecast` = Trading Economics' own projection and is not market consensus;
- `DateSpan=0` = event date/time is known;
- point-in-time calendar retrieval is intended for backtesting without look-ahead.

## Frozen pilot scope
Future live pilot, if separately human-authorized:
- country: United States;
- family: CPI;
- reference periods: 2019-01, 2019-02, 2019-03;
- expected release events: the three CPI releases already frozen in RND-0069;
- maximum live provider requests: 10;
- no FX joins;
- no strategy calculations;
- no provider auto-renew/purchase authority.

## Admission contract
A consensus observation is structurally admissible only if all are true:
1. provider is Trading Economics;
2. country/economy is United States;
3. CPI event family maps to the predeclared `US_CPI_HEADLINE` link key;
4. reference period is in the frozen 2019-Q1 sample;
5. event timing is exact (`DateSpan=0`);
6. exact release timestamp matches the independently governed BLS timestamp;
7. `Forecast` exists and parses numerically;
8. `Forecast` is tagged `MARKET_CONSENSUS`;
9. `TEForecast` is preserved only as non-admissible auxiliary provenance and can never substitute for `Forecast`;
10. the acquisition layer supplies a point-in-time snapshot timestamp strictly before release;
11. raw payload hash and source identity are present;
12. no market-outcome fields enter the record.

## Request budget firewall
The future live adapter must default to zero live calls and may never exceed 10 calls for this pilot. A counter must fail closed before call 11.

## Credential firewall
No API key may be committed, logged, printed, stored in receipts, or pasted into chat. A future live layer may read credentials only from environment/configuration and must redact request URLs.

## Output
The offline adapter emits only a `ConsensusEvidence`-compatible structural record plus provenance metadata. It does not create a full macro surprise event and does not touch FRED actuals or FX outcomes.

## Authority
provider_access_authority = FALSE
provider_purchase_authority = FALSE
strategy_outcome_open = FALSE
validation_open = FALSE
reserved_final_open = FALSE
prospective_outcomes_open = FALSE
promotion_authority = FALSE
broker_write_authority = FALSE
capital_authority = FALSE
live_execution_authority = FALSE
automatic_merge = FALSE

## Exit criteria
RND-0072 completes when hostile tests demonstrate:
- Forecast admitted only under pre-release point-in-time semantics;
- TEForecast never substitutes;
- exact BLS timing agreement required;
- malformed/late/missing/estimated-time rows fail closed;
- request cap and credential firewall are enforced;
- all protected authorities remain false.
