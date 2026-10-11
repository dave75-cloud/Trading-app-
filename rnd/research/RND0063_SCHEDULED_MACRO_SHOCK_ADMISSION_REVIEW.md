# RND-0063 — Scheduled Macro-Information Shock Admission Review

## Status
ADMISSION REVIEW COMPLETE — DEVELOPMENT TEST NOT YET OPENED

## Governing standard
RND-0062 Research Admission & Multiple-Hypothesis Standard.

## Purpose
Assess whether the Rank-1 RND-0061 research direction — scheduled macro-information shock response — has earned the right to consume development evidence.

This task is design/admission only. It does not inspect strategy outcomes, does not access 2021–2022 consumed validation, does not access 2023–2024 reserved final, and does not inspect Q003 or RND-0060Q/R prospective outcomes.

## Hypothesis family
- hypothesis_family_id: `MACRO_SHOCK_DIRECTIONAL_REPRICING`
- family_trial_index: 1
- lifetime_related_trial_count: 1
- prior family outcomes: none
- conceived after prior unrelated intraday price-pattern failures, but before any result in this family

The family counter may not be reset by renaming a later macro-event hypothesis.

## Economic mechanism
Scheduled macroeconomic releases create discrete information shocks when the released value differs from the market's contemporaneous expectation. The immediate repricing pressure should be directional with respect to the sign of the standardized surprise and the currency to which the release is economically relevant.

The claimed edge is not that volatility rises around scheduled releases; that is already broadly plausible and would be descriptive only. The directional claim is that a sufficiently defined positive or negative information surprise causes a consistent short-horizon repricing of the affected currency after executable transaction costs.

## Why this is independent of prior failed trials
This is not a rescue of RND-0060A–K or RND-0060T. It does not reuse:
- opening-range breakout;
- displacement mean reversion;
- cross-sectional relative value;
- three-bar persistence;
- contraction/expansion;
- spread-state or volatility-state persistence;
- cross-sectional dispersion as direction;
- signed dispersion;
- close-location pressure;
- cross-pair lead/lag.

The directional input is exogenous scheduled information surprise, not a transformed version of prior FX price outcomes. No failed task parameter, sign, lookback, session, threshold, weak instrument, or pair ranking is being rescued.

## Falsifiable claim
A frozen, point-in-time macro-surprise sign mapping should produce a directionally consistent post-release FX response that remains economically positive after bid/ask-aware costs across years and relevant instruments.

The mechanism is falsified if the frozen surprise-to-direction mapping fails the predeclared primary economic criterion, minimum effect threshold, cross-year robustness, or cross-instrument robustness.

## Proposed development partition
FX market data: DEVELOPMENT_2015_2020 only.

No 2021–2022 validation data.
No 2023–2024 reserved-final data.
No Q003 prospective outcomes.
No RND-0060Q/R prospective economic outcomes.

## Required external event data
A valid directional test requires point-in-time macro-event observations with, at minimum:
- event identity;
- affected currency/economy;
- scheduled release timestamp as known before release;
- actual released value;
- contemporaneous pre-release consensus/expectation;
- unit and transformation definition;
- revision flag and treatment;
- source identity and immutable provenance;
- event cancellation/reschedule handling;
- release-time ambiguity/DST handling;
- enough historical coverage for 2015–2020.

The event source must preserve what was knowable at the time. Later-revised consensus or retrospectively normalized surprise values may not substitute silently for contemporaneous expectation data.

## Direction rule — concept frozen, numeric implementation not yet authorized
The intended directional mechanism is:
1. compute a standardized signed surprise from actual minus contemporaneous consensus, with sign conventions frozen by event family before testing;
2. map the surprise sign to expected strengthening/weakening of the affected currency according to the predeclared economics of the release;
3. translate currency strengthening/weakening into LONG/SHORT direction for the relevant FX pair by base/quote orientation;
4. evaluate only after the scheduled release boundary using executable bid/ask semantics.

No direction may be inferred from post-release FX price movement itself.

## Event universe — not yet frozen
The exact release families are deliberately NOT selected in this task because doing so without a governed point-in-time event dataset would create hidden researcher degrees of freedom.

Candidate economic classes considered before any outcome test include:
- central-bank policy-rate decisions;
- CPI/inflation releases;
- labour-market releases;
- GDP/growth releases;
- high-salience activity releases.

These alternatives are disclosed as design degrees of freedom. No class may be selected after comparing development outcomes.

## Instruments considered
Existing project FX universe:
- AUDUSD
- EURUSD
- GBPUSD
- USDJPY

The final event-to-instrument mapping must be frozen before outcome access and may not be changed to drop weak pairs later.

## Timing degrees of freedom disclosed
Potential post-release execution horizons considered conceptually before testing include immediate next eligible M5 bar and short fixed multi-bar horizons.

No timing choice is authorized yet. The exact entry delay and holding/exit horizon must be frozen after the event-data protocol is defined but before any outcome calculation.

## Threshold degrees of freedom disclosed
Potential surprise treatment choices include:
- nonzero signed surprise;
- standardized surprise magnitude threshold;
- event-family-specific normalization.

No threshold search is authorized. Any eventual threshold must be justified independently of development P&L and frozen before the sole family trial.

## Filters considered and prohibited rescue
Potential eligibility filters that have been considered conceptually include event-family identity, point-in-time consensus availability, release-time integrity, and conflict/overlap handling for simultaneous events.

No volatility, spread, pair, year, direction, or post-release price-derived filter may be added after outcome inspection to rescue the trial.

## Transaction-cost requirements
Any future directional implementation must use:
- bid/ask-aware executable entry and exit;
- no mid-price executable P&L;
- explicit spread cost;
- non-favourable slippage assumption appropriate to event conditions;
- gap-aware semantics;
- no synthetic fill across missing intervals;
- explicit treatment of stale/crossed/unavailable quotes around release time.

Because scheduled releases can widen spreads and impair liquidity, ordinary-session friction assumptions are not automatically adequate.

## Primary metric — to be frozen before development test
The primary metric must be an aggregate realized net economic result after the event-specific execution-cost model. Exact normalization must be frozen in the future executable protocol.

## Minimum economic effect
The eventual protocol must set a numeric minimum economic effect before outcome access. Merely positive terminal equity or nonzero directional association is insufficient.

## Minimum sample adequacy
The eventual protocol must predeclare a minimum number of independent scheduled release events, not M5 rows. Repeated bars after one release do not count as independent events.

## Required robustness if admitted later
A future development run must report at minimum:
- aggregate net result after costs;
- annual results for every included 2015–2020 year;
- leave-one-year-out results;
- results by instrument/economy;
- leave-one-instrument-out results where multi-instrument;
- event counts by year and event family;
- gross-to-net degradation;
- exclusions and missing-event accounting;
- immutable source/provenance identity.

No weak event family, year, or instrument may be dropped after outcomes are visible.

## Degrees-of-freedom declaration
Discretionary choices already recognized before testing:
- signal families considered: 5 broad macro classes;
- event-family universe: not yet selected;
- execution timing variants conceptually considered: >1;
- holding horizons conceptually considered: >1;
- surprise normalization choices: >1;
- surprise thresholds conceptually considered: >1;
- pair/event mappings: >1;
- overlap/conflict handling choices: >1;
- event-specific slippage model choices: >1.

These disclosed freedoms mean the project must NOT treat the eventual run as though the idea appeared fully specified with zero prior design alternatives.

## RND-0062 admission decision
**NOT YET ADMISSIBLE_FOR_DEVELOPMENT_TEST**.

This is not a scientific rejection of the macro-information mechanism. It is an admission-stage structural block.

### Blocking reason
`MISSING_GOVERNED_POINT_IN_TIME_MACRO_EVENT_DATA_PROTOCOL`

The directional input depends on an external historical expectation/actual dataset that is not yet governed, frozen, and provenance-audited inside the project. Without that, the event universe, surprise definition, sign conventions, release timestamps, revision treatment, and sample adequacy cannot honestly be declared complete.

Passing the generic RND-0062 field classifier by setting boolean declarations to TRUE would be methodologically misleading at this stage, so no such synthetic pass is recorded.

## Required prerequisite
Create a separate task to define and validate a historical macro-event data-source and provenance protocol before returning to RND-0063 for final admission.

That prerequisite must establish:
- source(s) and licensing/access assumptions;
- point-in-time integrity;
- 2015–2020 coverage;
- timestamp/time-zone semantics;
- actual/consensus/revision fields;
- currency/event taxonomy;
- missing-data semantics;
- duplicate/conflict handling;
- immutable raw evidence identity;
- no market-outcome inspection during source selection.

## Authority state
- development_outcome_open: FALSE
- validation_open: FALSE
- reserved_final_open: FALSE
- prospective_outcomes_open: FALSE
- candidate_freeze: FALSE
- promotion_authority: FALSE
- broker_write_authority: FALSE
- capital_authority: FALSE
- live_execution_authority: FALSE
- automatic_merge: FALSE

## Interpretation
RND-0063 has done its job by stopping the project before backtesting an incompletely specified exogenous-data hypothesis. The scheduled macro-shock direction remains a high-priority research idea, but it must first earn trustworthy point-in-time event data.
