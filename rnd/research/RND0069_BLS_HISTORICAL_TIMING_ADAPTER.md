# RND-0069 — BLS Historical Timing Adapter

## Status
GOVERNED TIMING ADAPTER — OUTCOME-BLIND — NO CONSENSUS — NO FX OUTCOMES

## Purpose
Implement a primary-source historical timing adapter for the frozen US CPI sample using official Bureau of Labor Statistics historical release schedules. The adapter proves exact Eastern Time release scheduling and deterministic UTC conversion without opening consensus, actual-value, FX, validation, reserved-final, or prospective economic outcomes.

## Inheritance
RND-0069 inherits without modification:
- RND-0062 research-admission and multiplicity standard;
- RND-0063 macro-shock admission block pending defensible point-in-time macro inputs;
- RND-0064 canonical event/provenance guard;
- RND-0066 split-source architecture;
- RND-0067 verified FRED/ALFRED official-value/revision backbone acquisition;
- RND-0068 verified timing/consensus source-feasibility decision.

## Frozen pilot scope
Event family: Consumer Price Index.
Economy: United States.
Currency: USD.
Reference periods: 2019-01, 2019-02, 2019-03.
Official timing source: BLS historical release schedule/archive.
Local timezone semantic: `America/New_York`.
Expected release clock time for the frozen sample: 08:30 Eastern Time.

## Official timing evidence
The BLS 2019 historical schedule states that all schedule times are Eastern Time and lists:
- CPI for January 2019: Wednesday 13 February 2019 at 08:30;
- CPI for February 2019: Tuesday 12 March 2019 at 08:30;
- CPI for March 2019: Wednesday 10 April 2019 at 08:30.

Archived CPI releases independently corroborate the DST transition:
- 13 February 2019 release: 08:30 EST;
- 12 March 2019 release: 08:30 EDT;
- 10 April 2019 release: 08:30 EDT.

Therefore deterministic UTC timestamps are:
- 2019-02-13T13:30:00Z;
- 2019-03-12T12:30:00Z;
- 2019-04-10T12:30:00Z.

## DST rule
The adapter MUST use an IANA timezone (`America/New_York`) rather than a hard-coded UTC offset. This is required because the frozen sample crosses the US daylight-saving transition between the February and March release dates.

A fixed `UTC-5` or fixed `UTC-4` conversion is prohibited.

## Timing-only firewall
RND-0069 may carry:
- provider/event identity;
- link key;
- event family;
- economy/currency;
- reference period;
- release date;
- local release time;
- timezone name;
- exact UTC timestamp;
- source identity;
- raw hash;
- timing precision.

RND-0069 MUST NOT carry:
- actual-as-released values;
- consensus values;
- FX returns;
- P&L/equity/drawdown;
- hit/win rate;
- pair ranking;
- strategy signals/outcomes.

## Provenance rule
Each normalized timing record requires:
- official source identity;
- immutable raw hash;
- stable provider event identity;
- exact reference period;
- deterministic UTC conversion.

No nearest-date, fuzzy-name, or outcome-informed correction is permitted.

## Eligibility meaning
An RND-0069 record with `timestamp_precision=EXACT` means only that the historical release timestamp is structurally proven from the official timing source.

It does not mean:
- consensus exists;
- surprise input is complete;
- a strategy is admitted;
- any economic efficacy has been shown.

## Exit criteria
RND-0069 is verified when hostile tests prove at minimum:
1. EST conversion is correct;
2. EDT conversion is correct;
3. DST transition is handled through `America/New_York`;
4. malformed dates/times are rejected;
5. wrong event family is rejected;
6. wrong release time is rejected;
7. out-of-scope reference periods are rejected;
8. provenance is mandatory;
9. consensus/actual/market-outcome contamination is rejected;
10. frozen triplet completeness/order/uniqueness is enforced;
11. timing receipt remains timing-only;
12. all execution/promotion/capital/purchase authorities remain false.

## Next governed phase
After RND-0069 verification, proceed to a consensus-only feasibility/admission phase. No timing+consensus+actual composite event should be declared `SURPRISE_INPUT_ELIGIBLE` until the consensus source independently proves historical point-in-time integrity and pre-release chronology.

## Authority
No FX outcome access.
No validation access.
No reserved-final access.
No prospective-outcome access.
No provider-purchase authority.
No broker-write authority.
No capital authority.
No live-execution authority.
No automatic merge.
