# RND-0062 — Research Admission & Multiple-Hypothesis Standard

## Status
FROZEN METHODOLOGICAL GOVERNANCE STANDARD — NO NEW STRATEGY OUTCOME OPENED

## Purpose
Define the predeclared admission, falsification, robustness, multiplicity, and advancement rules that every future independent strategy hypothesis must satisfy before it may consume development evidence or advance toward candidate review.

This standard exists to reduce researcher degrees of freedom, prevent iterative rescue/tuning, distinguish genuine mechanism testing from search, and make future research comparable across hypotheses.

RND-0062 does not test a trading strategy and does not alter Q003, RND-0060Q/R, consumed validation, reserved final, promotion authority, capital authority, or broker-write authority.

## Core principle
A strategy idea must earn the right to consume evidence.

The correct order is:
1. economic mechanism;
2. falsifiable hypothesis;
3. exact data scope;
4. exact parameterization;
5. exact cost model;
6. exact success/failure criteria;
7. multiplicity declaration;
8. frozen implementation;
9. one development trial;
10. hostile robustness review;
11. classification;
12. only then, if justified, separate candidate review.

Backtest attractiveness never substitutes for this order.

## Scope
Applies to all post-RND-0061 independent strategy research unless a later explicit human-approved methodological standard supersedes it.

Protected evidence remains unchanged:
- 2021–2022 validation is consumed and unavailable for new candidate testing;
- 2023–2024 reserved final remains sealed;
- Q003 prospective outcomes remain sealed;
- RND-0060Q/R prospective economic outcomes remain sealed.

Default research partition remains DEVELOPMENT_2015_2020 unless a separately governed data-source protocol explicitly defines another admissible development source.

## Admission gate — required before implementation
A proposed hypothesis is `ADMISSIBLE_FOR_DEVELOPMENT_TEST` only if all required fields are complete and pass review.

### 1. Mechanism statement
Must state, in plain language:
- what economic or microstructural mechanism is claimed;
- why that mechanism should create directional or conditional economic edge;
- why the mechanism is distinct from previously falsified nearby ideas;
- what observable consequence would falsify the mechanism.

Pure pattern description without causal/economic rationale is insufficient unless explicitly classified as a descriptive-structure study rather than a strategy hypothesis.

### 2. Independence statement
Must identify prior related RND tasks and explain why the new hypothesis is not:
- a rescue of a failed trial;
- a threshold tweak;
- a time-window tweak;
- a pair-selection tweak;
- a sign inversion;
- a nearby lookback/horizon substitution;
- a post-hoc filter derived from prior outcome inspection.

If materially adjacent to a failed trial, the hypothesis is inadmissible unless the mechanism itself is genuinely different and that distinction is documented before testing.

### 3. Exact frozen specification
Must freeze before outcome access:
- instruments;
- time zone and session/event times;
- signal definition;
- direction rule;
- lookback horizon;
- holding/exit horizon;
- eligibility filters;
- gap semantics;
- transaction-cost model;
- slippage assumptions if relevant;
- portfolio aggregation rule;
- missing-data handling;
- one primary evaluation metric;
- any secondary diagnostics.

No implicit defaults may be selected after outcome inspection.

### 4. Degrees-of-freedom declaration
The proposal must enumerate every discretionary design choice considered while formulating the trial, including alternatives rejected before testing.

At minimum declare counts for:
- candidate signal families considered;
- time windows considered;
- lookbacks considered;
- thresholds considered;
- holding horizons considered;
- pair universes considered;
- direction mappings considered;
- filters considered;
- aggregation variants considered.

The declaration is qualitative and quantitative where possible. Hidden search is a methodological failure even if only one final backtest is run.

### 5. Multiplicity family
Every new trial must belong to an explicit hypothesis family with a monotonically increasing `family_trial_index`.

Required fields:
- `hypothesis_family_id`;
- `family_trial_index`;
- `lifetime_related_trial_count`;
- whether prior trials in the family were positive, negative, mixed, or structurally inconclusive;
- whether the current trial was conceived before or after seeing those outcomes.

No reset of the family counter is allowed by renaming the idea.

## Default multiplicity policy
The project does not treat nominal single-trial significance or a positive backtest as independent evidence when many related hypotheses have been explored.

For future work:
- result interpretation must explicitly condition on `lifetime_related_trial_count`;
- advancement cannot be based solely on a p-value, hit rate, Sharpe-like measure, or terminal equity;
- families with repeated nearby trials require stronger cross-time/cross-instrument consistency to advance;
- post-hoc selection among siblings is prohibited;
- the selected trial must be identifiable before its outcome is known.

Where formal statistical tests are used, Holm-style familywise adjustment is the default for a small finite predeclared family. For open-ended sequential research, statistical significance is considered descriptive unless a separately frozen sequential-testing protocol has been approved.

## Transaction-cost realism
Every directional strategy test must incorporate economically appropriate friction from the first development run.

Minimum requirements:
- bid/ask-aware entry and exit where data support it;
- no mid-price fills for executable P&L;
- explicit spread cost;
- gap-aware execution semantics;
- no favourable slippage assumption;
- no synthetic fill across missing intervals;
- no cost-free turnover comparison.

If executable bid/ask evidence is unavailable for a proposed design, the study must be classified as non-trading structure research until an admissible execution-cost model exists.

## Minimum economic effect standard
A result cannot advance merely because aggregate terminal equity exceeds 1.0 or an association is statistically nonzero.

Before testing, each strategy hypothesis must declare a `minimum_economic_effect` appropriate to its metric.

For trading strategies, the default advancement standard requires all of the following unless a task-specific stricter threshold is frozen:
1. aggregate realized net result after modeled costs > 0;
2. terminal normalized portfolio equity > 1.0;
3. maximum drawdown finite and explicitly reported;
4. positive result not concentrated in a single year;
5. positive result not concentrated in a single instrument;
6. leave-one-year-out aggregate result remains directionally positive in every omission, unless a predeclared structural regime exception exists;
7. leave-one-instrument-out aggregate result remains directionally positive in every omission for multi-instrument strategies;
8. gross-to-net degradation is reported and does not eliminate the claimed mechanism;
9. effect size exceeds the predeclared minimum economic effect.

Passing these conditions permits only `ELIGIBLE_FOR_CANDIDATE_REVIEW`, never automatic candidate freeze.

## Cross-time robustness
Default full-development robustness report must include:
- aggregate full-period result;
- annual results for each 2015–2020 year used;
- leave-one-year-out results;
- trade/event counts by year;
- cost contribution by year;
- structural exclusions/gaps by year.

A strategy fails robustness if its entire positive aggregate result depends on one isolated year unless the dependence was explicitly predicted by the frozen mechanism and regime definition before testing.

## Cross-instrument robustness
For multi-instrument research, report:
- result by instrument;
- event/trade count by instrument;
- cost drag by instrument;
- leave-one-instrument-out portfolio result.

No instrument may be dropped after outcome inspection to rescue the portfolio.

A common-mechanism claim requires predeclared evidence that the mechanism has the same directional effect across the intended instrument universe, even if magnitude differs.

## Parameter robustness without parameter search
The first development test is one frozen parameterization.

If it passes the primary trial strongly enough for candidate review, a later separately approved robustness task may test a small predeclared neighbourhood for fragility.

That robustness task must:
- define the neighbourhood before opening outcomes;
- not select the best neighbour;
- treat the frozen primary parameterization as authoritative;
- classify fragility, not optimize performance.

If the primary trial fails, nearby parameter search is prohibited as rescue.

## Falsification rules
A development hypothesis is closed as `DEVELOPMENT_FALSIFIED` when any frozen primary failure criterion is met.

After falsification, prohibited rescue actions include:
- changing threshold;
- changing sign;
- changing session;
- changing horizon;
- dropping weak instruments;
- adding outcome-derived filters;
- redefining success metric;
- reclassifying the same mechanism under a new task ID.

A genuinely new mechanism may be proposed later, but its independence statement must explicitly distinguish it from the falsified task.

## Structural-study classification
Not all research must be a trading strategy.

Allowed non-trading classifications include:
- `REPRODUCIBLE_STRUCTURE_DETECTED`;
- `NO_REPRODUCIBLE_STRUCTURE`;
- `ECONOMIC_CONTEXT_STRUCTURE_DETECTED`;
- `DIRECTIONAL_STRUCTURE_DETECTED`.

A structural study cannot be promoted directly to a strategy. A later task must specify how the structure interacts with an independent directional or execution mechanism.

## Candidate-review admission
A completed development trial may be classified `ELIGIBLE_FOR_CANDIDATE_REVIEW` only if:
- admission record was complete before outcome access;
- exact trial count was respected;
- no prohibited partition was accessed;
- cost model was valid;
- integrity checks passed;
- primary criterion passed;
- minimum economic effect passed;
- cross-time robustness passed;
- cross-instrument robustness passed where applicable;
- multiplicity burden was disclosed;
- no rescue or post-hoc tuning occurred;
- implementation and report are reproducible from immutable inputs.

This status is not a candidate freeze.

A separate HUMAN_ONLY candidate review must decide whether prospective evidence is worth consuming.

## Candidate-review rejection reasons
A positive-looking development result must still be rejected from candidate review if any of the following apply:
- mechanism not economically coherent;
- undeclared degrees of freedom;
- hidden sibling trials;
- selection after comparing multiple variants;
- insufficient transaction-cost realism;
- insufficient event count;
- one-year dependence;
- one-instrument dependence;
- failed leave-one-out robustness;
- minimum economic effect not met;
- prohibited evidence access;
- irreproducible implementation;
- outcome-dependent specification change.

## Minimum sample adequacy
Each task must predeclare a minimum sample adequacy rule suitable to the event frequency.

Default principle:
- a result cannot advance if the effective number of independent decision events is too small to support the breadth of the claim;
- raw M5 row count does not substitute for independent event count;
- clustered events must not be treated as fully independent merely because they occur on separate bars.

No universal event-count threshold is imposed here because mechanisms differ. Each future task must justify and freeze its own threshold before testing.

## Research ledger requirements
Every trial must append an immutable research-ledger record containing at minimum:
- task ID;
- hypothesis family ID;
- family trial index;
- date frozen;
- development data identity;
- code commit;
- parameterization fingerprint;
- primary metric;
- minimum economic effect;
- result classification;
- report identity/hash;
- prohibited-partition flags;
- whether any rescue was attempted;
- advancement decision;
- human gate identity where applicable.

Negative and null results must remain in the ledger permanently.

## Prospective-program firewall
RND-0062 cannot inspect, use, or condition on:
- Q003 prospective strategy outcomes;
- RND-0060Q/R economic confirmation outcomes.

It may know only their governance status and sealed/readout dates already fixed by prior tasks.

No new research hypothesis may be tuned using prospective accumulation behaviour.

## Reserved-final firewall
2023–2024 reserved final remains sealed.

No development success under this standard grants access to reserved final.

Any future reserved-final opening requires a separate explicit human gate and a frozen final-test protocol.

## Authority firewall
Throughout RND-0062 and all research admitted under it unless separately authorized:
- `promotion_authority=FALSE`;
- `broker_write_authority=FALSE`;
- `capital_authority=FALSE`;
- `live_execution_authority=FALSE`;
- `automatic_merge=FALSE`.

## Required implementation
A pure admission-classifier kernel must be built with hostile tests proving at minimum:
1. missing mechanism rejects admission;
2. missing independence statement rejects admission;
3. undeclared parameter field rejects admission;
4. hidden sibling-trial count rejects admission;
5. invalid family trial index rejects admission;
6. prohibited validation access rejects admission;
7. prohibited reserved-final access rejects admission;
8. prospective-outcome contamination rejects admission;
9. missing cost model rejects directional-strategy admission;
10. mid-price executable P&L assumption rejects admission;
11. missing minimum economic effect rejects admission;
12. missing sample adequacy rule rejects admission;
13. complete clean proposal can become ADMISSIBLE_FOR_DEVELOPMENT_TEST;
14. failed primary criterion cannot advance;
15. failed minimum economic effect cannot advance;
16. single-year dependence cannot advance absent frozen exception;
17. single-instrument dependence cannot advance absent frozen exception;
18. failed leave-one-year-out cannot advance;
19. failed leave-one-instrument-out cannot advance where applicable;
20. hidden rescue/tuning attempt cannot advance;
21. clean robust development result may become ELIGIBLE_FOR_CANDIDATE_REVIEW;
22. candidate-review eligibility does not equal candidate freeze;
23. all authority fields remain false;
24. deterministic replay yields identical classification.

## Interpretation boundary
Passing RND-0062 will establish a common methodological bar for future research. It will not establish that any new strategy works, will not consume prospective evidence, and will not authorize promotion or trading.