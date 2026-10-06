# RND-0060M — Activity-Aware Strategy Admissibility / Execution-Control Design Review

## Status

FROZEN DESIGN REVIEW — NO STRATEGY TEST — NO P&L — NO VALIDATION

## Purpose

RND-0060H established a reproducible development-only relationship between 11:30 UTC cross-sectional USD dispersion and subsequent 30-minute market activity. RND-0060L then established that the same activity state is associated with materially better subsequent movement relative to contemporaneous spread friction. RND-0060J and RND-0060K did not establish reproducible directional information.

RND-0060M therefore asks an architectural question rather than a new market-direction question:

> How may the frozen RND-0060H activity state be used safely as an admissibility or execution-control input for a separately generated directional signal without allowing the activity model to create direction, tune strategy parameters, or obtain execution authority?

This task does not test a trading strategy and does not create an activity threshold.

## Governing scientific facts carried forward

The design may rely only on the following established development findings:

1. RND-0060H: higher cross-sectional USD dispersion at 11:30 UTC is associated with greater subsequent 30-minute market activity/magnitude.
2. RND-0060L: higher cross-sectional USD dispersion is associated with a higher subsequent 30-minute movement-to-friction ratio.
3. RND-0060J and RND-0060K: the tested directional mechanisms did not establish reproducible direction.

No stronger claim is permitted. In particular, RND-0060M must not treat the activity state as predicting long/short direction or positive expected return.

## Architectural separation

The future decision path must preserve three distinct layers:

### Layer A — independent directional source

Produces only a directional intent or abstention, for example:

- LONG
- SHORT
- FLAT / NO SIGNAL

The directional source must be defined independently of the RND-0060H activity state.

### Layer B — activity admissibility / execution-control state

Consumes the frozen RND-0060H activity state and may, in a later separately predeclared task, produce only execution-admissibility metadata such as:

- activity state observed;
- activity quality / movement-to-friction context;
- admissible / not-admissible, if and only if a threshold has been separately frozen by an authorised task;
- execution urgency or passive/aggressive handling class, if separately defined and validated.

Layer B must never:

- choose LONG versus SHORT;
- reverse a directional signal;
- create a trade when Layer A is FLAT;
- alter the directional model's parameters;
- size capital;
- bypass risk controls;
- submit an order.

### Layer C — risk and execution authority

Consumes an already-approved directional intent plus admissibility metadata but remains independently governed by risk limits, execution controls, broker-write permissions, capital authority, kill switches, and human promotion gates.

Layer C retains final veto authority.

## Preferred first application

The preferred first downstream use of the RND-0060H/RND-0060L state is **strategy admissibility**, not position sizing and not direction.

Rationale:

- it uses the activity signal for the thing it actually predicts: opportunity magnitude relative to friction;
- it does not require the activity state to forecast sign;
- it can be implemented as a veto-only control, which is safer than using the state to create exposure;
- it preserves the independence of directional research;
- it is compatible with the existing shadow/risk/control architecture built in RND-0051 through RND-0059.

This is an architectural preference only. It does not authorize an admissibility rule yet.

## Veto-only principle

Any future activity-aware admissibility layer must obey:

> Activity state may suppress or defer an independently generated trade intent, but it may not create, reverse, enlarge, or directionally modify exposure.

This principle is mandatory for the first activity-aware integration study.

## Threshold prohibition in RND-0060M

RND-0060M must not select or estimate a cutoff such as:

- dispersion >= X;
- top quartile only;
- movement-to-friction >= Y;
- percentile >= P;
- high/medium/low activity buckets selected from observed performance.

The quartile evidence from RND-0060H/RND-0060L remains descriptive. It is not converted into a trading threshold here.

Any threshold or continuous decision mapping requires a new separately predeclared research task with explicit anti-overfitting controls and human approval before outcome inspection.

## No Q003 outcome contamination

Q003 remains in prospective accumulation. RND-0060M must not inspect, condition on, or infer from Q003 prospective trades, P&L, win rate, pair ranking, drawdown, or other outcomes.

RND-0060M also does not modify the frozen Q003 candidate.

A future study may consider whether an activity-admissibility layer can be evaluated using an independently declared directional source, but using Q003 itself would require an explicit human gate because Q003 is presently frozen under prospective observation.

## Interface contract for future implementation

A future activity-admissibility component should expose a record conceptually equivalent to:

```text
observation_timestamp_utc
activity_state_value
activity_state_definition_id
admissibility_rule_id_or_none
admissibility_decision_or_none
reason_code
source_evidence_identity
validation_status
broker_authority = FALSE
capital_authority = FALSE
```

The component must not contain:

- order quantity;
- account NAV;
- leverage instruction;
- stop-loss or take-profit placement;
- LONG/SHORT generation;
- broker endpoint invocation;
- promotion authority.

## Fail-closed behavior

If activity-state inputs are missing, stale, structurally invalid, non-reconciled, or outside the authorised observation contract, the future admissibility layer must fail closed:

- no admissibility approval;
- no inferred replacement value;
- no interpolation;
- no fallback threshold;
- no execution escalation.

## Research sequence recommended after RND-0060M

The next empirical task should not immediately optimise a threshold.

The recommended sequence is:

1. define a generic activity-admissibility contract and hostile fixtures;
2. choose a single independently justified directional probe or shadow signal source under a separate human-approved declaration;
3. predeclare exactly one admissibility mapping or threshold-selection rule before outcomes are inspected;
4. test only on authorised development evidence;
5. require breadth, stability, friction, and anti-overfitting diagnostics;
6. if successful, conduct a separate human review before any validation, prospective, shadow, or execution integration.

## Explicit prohibitions

RND-0060M must not:

- run a backtest;
- simulate trades;
- calculate P&L, equity, drawdown, Sharpe, win rate, or trade expectancy;
- select or tune an activity threshold;
- reopen RND-0060J or RND-0060K;
- invert failed directional mechanisms;
- cherry-pick symbols, years, times, lookbacks, or horizons;
- use consumed validation 2021–2022;
- access reserved final 2023–2024;
- inspect Q003 prospective outcomes;
- change Q003;
- create broker-write authority;
- create capital authority;
- authorize promotion;
- authorize merge.

## Governance state

- design_review_only = TRUE
- development_outcomes_opened_in_this_task = FALSE
- trade_simulation = FALSE
- pnl = FALSE
- threshold_selected = FALSE
- directional_signal_created = FALSE
- validation_open = FALSE
- final_test_open = FALSE
- reserved_final_access = FALSE
- prospective_candidate_outcomes_open = FALSE
- broker_writes = FALSE
- capital_authority = FALSE
- automatic_promotion = FALSE
- automatic_merge = FALSE
- HUMAN_ONLY promotion authority remains unchanged

## Design decision

RND-0060M adopts the following architecture for future activity-aware research:

> The RND-0060H activity state is an execution-admissibility context signal only. Its first permissible strategy-facing role is veto-only. Direction must originate independently; risk and execution authority remain separate; no activity threshold is selected in this task.

## Completion criterion

RND-0060M is complete when this architecture is frozen and reviewed. No empirical market outcome is required or permitted for completion.
