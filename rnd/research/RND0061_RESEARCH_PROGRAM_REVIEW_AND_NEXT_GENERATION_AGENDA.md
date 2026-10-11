# RND-0061 — Research Program Review & Next-Generation Hypothesis Agenda

## Status
SCIENTIFIC REVIEW COMPLETE — NO NEW STRATEGY TRIAL / NO PROSPECTIVE OUTCOME ACCESS / NO TRADING AUTHORITY

## Executive assessment
The project has progressed from an initially promising but methodologically weak intraday FX backtest into a governed research platform with credible controls over data provenance, development/validation separation, gap semantics, transaction costs, prospective evidence, shadow execution, risk, audit, and human promotion gates.

The engineering and governance platform is now substantially more mature than the evidence for a tradable edge.

The strongest defensible scientific conclusion is therefore not that the system has found a proven autonomous trading strategy. It is that the project now has increasingly reliable machinery for discovering, falsifying, prospectively validating, and eventually operating one without silently relaxing the evidentiary standard.

Two prospective programs are currently active and must remain untouched economically until their frozen readout conditions are met:
- Q003 prospective strategy validation;
- RND-0060Q/R independent confirmation of the activity-policy mechanism.

The six-month accumulation period is not idle time. It is the period that converts a development finding into evidence with genuine prospective value. The correct use of the interval is independent research and methodological improvement, not alteration of the frozen programs.

---

## 1. What the project has actually learned

### 1.1 Market-data reconstruction and gap semantics matter materially
RND-0034 established that historical M5 reconstruction cannot safely treat missing bars as ordinary elapsed strategy time. The project now separates market, strategy, and portfolio state across gaps, resets indicator state appropriately, avoids manufactured exits or synthetic missing observations, and preserves open economic exposure through gaps where applicable.

This is a methodological finding with broad importance: apparent strategy performance can be materially distorted by casual handling of missing data, historical trading calendars, warmup, signal delay, or spread-side execution.

Classification: `GOVERNANCE_OR_ENGINEERING_VERIFIED`.

### 1.2 The original M005 / R000 family did not survive stronger development reconstruction
The original .0005 baseline that looked attractive in earlier work deteriorated when evaluated on the reconstructed 2015–2020 development set with governed semantics. Full-development R000 ended below starting equity with negative realised net performance and was falsified.

Classification: `VALIDATED_NEGATIVE / FALSIFIED` for the exact frozen R000 implementation.

Implication: earlier headline backtests were not reliable evidence of durable edge.

### 1.3 A higher-volatility selection mechanism improved the M005 family, but validation rejected the .0006 candidate
RND-0039 found that the predeclared .0006 alternative materially improved development performance relative to .0005. That justified freezing .0006 as the sole RND-0040 validation candidate.

Untouched 2021–2022 validation in RND-0042 rejected that candidate. The validation evidence is now permanently consumed and cannot be reused as fresh evidence for a successor.

Classification:
- development mechanism: `PROMISING_BUT_UNCONFIRMED_STRATEGY` at the time;
- frozen .0006 candidate after RND-0042: `VALIDATED_NEGATIVE / FALSIFIED`.

Implication: no nearby absolute-volatility threshold rescue is scientifically justified. Testing .00055, .00065, .0007, or similar variants would be post-hoc threshold mining around a failed validation result.

### 1.4 Signal-to-friction contains real economic information
RND-0043 showed that volatility relative to spread/friction is more informative than an absolute volatility floor. The mechanism improved performance materially even though the aggregate candidate remained negative.

RND-0044 then tested the predeclared ratio-only Q003 mechanism (`sigma12_mid_return / relative_spread >= 8`) over development evidence. Q003 was positive at the portfolio level but mixed/non-monotonic at the pair level.

RND-0045 showed broad positive Q003-vs-Q000 effects across pairs and years, including positive leave-one-out effects. This supported candidate review without proving future profitability.

RND-0046 froze Q003 for prospective evaluation.

Classification: `PROMISING_BUT_UNCONFIRMED_STRATEGY`.

Implication: friction-aware admissibility is one of the most credible strategy-related lessons in the project, but Q003 must now stand or fall on its untouched prospective evidence.

### 1.5 Many intuitive directional hypotheses failed decisively
The independent RND-0060 research firewall produced a useful body of negative evidence.

Closed negative directional/trading trials include:
- RND-0060A opening-range breakout;
- RND-0060B displacement mean reversion;
- RND-0060C cross-sectional USD relative value;
- RND-0060D three-bar directional persistence;
- RND-0060E volatility contraction-to-expansion;
- RND-0060J signed-dispersion direction;
- RND-0060K close-location directional pressure;
- RND-0060T cross-pair lead-lag direction.

RND-0060F spread-state structure and RND-0060G volatility-state persistence found weak/non-reproducible structure insufficient for candidate formation.

Classification: `VALIDATED_NEGATIVE / FALSIFIED` for the exact predeclared hypotheses; `INCONCLUSIVE / STRUCTURALLY LIMITED` only where the task itself was explicitly structural rather than trading.

Scientific implication: simple price-pattern directionality in this M5 universe has repeatedly failed when subjected to predeclared, full-development tests. The next program should therefore demand a stronger economic source of directional information than “price moved, therefore it should continue/reverse.”

### 1.6 Cross-sectional dispersion is a real activity-state variable
RND-0060H produced one of the strongest non-directional findings in the research program. Cross-sectional dispersion of USD-oriented 30-minute returns at the frozen observation time showed broad, stable association with subsequent market activity.

The relationship was positive across all six development years and all four symbols. High-dispersion observations were followed by materially higher next-window realised movement than low-dispersion observations.

Classification: `ROBUST_POSITIVE_STRUCTURE`.

Important boundary: this is an activity/magnitude result, not a directional edge.

### 1.7 Activity state also predicts movement relative to friction
RND-0060L tested the economic usefulness of the RND-0060H state by relating it to subsequent movement/friction. The result was positive across all six years and all four symbols, with materially better movement/friction in the high-activity regime.

Classification: `ROBUST_POSITIVE_STRUCTURE`.

Implication: the project has credible evidence that some market states are economically more admissible for trading than others, even though the state does not supply direction.

### 1.8 Activity-state admissibility has been converted into a governed policy, not a strategy
RND-0060M–P transformed the H/L finding into a veto-context architecture. The frozen empirical median cutpoint is `0.0003990789273159821`.

The policy is deliberately constrained to `ADMIT`, `VETO`, or `DEFER`. It may not create a signal, change direction, enlarge exposure, or substitute for a strategy.

RND-0060Q/R then froze and started an independent prospective confirmation program. Its outcome remains sealed.

Classification:
- development mechanism: `ROBUST_POSITIVE_STRUCTURE`;
- prospective confirmation: `UNRESOLVED / ACCUMULATING`.

### 1.9 The project has not found a second independent directional strategy
RND-0060A–K and T make this conclusion important. The project has found evidence about activity and economic tradability, but it has not yet found a separately reproducible directional mechanism that survives governed full-development falsification.

This is not a failure of the research process. It is precisely the kind of conclusion a strong research process should be able to reach.

### 1.10 The execution and governance platform is now ahead of the strategy evidence
RND-0051 through RND-0060Y established, among other things:
- shadow/risk architecture;
- control/API schemas;
- realistic shadow execution semantics;
- reconciliation and kill precedence;
- research firewalling;
- prospective evidence accumulation and provenance protection;
- end-to-end shadow integration;
- prospective readout/promotion firewalling;
- non-economic accumulation-health monitoring.

Recent verified milestones include RND-0060U, V, W, X, and Y.

Classification: `GOVERNANCE_OR_ENGINEERING_VERIFIED`.

Project-level implication: the major constraint is now scientific edge and prospective confirmation, not missing execution plumbing.

---

## 2. Hypothesis-space map

### Closed / do not rescue
The following regions should be considered scientifically closed unless a future hypothesis is genuinely different in causal mechanism rather than a parameter variation:
- nearby absolute volatility thresholds around the failed .0006 candidate;
- simple opening-range breakout;
- simple displacement mean reversion;
- simple cross-sectional USD relative-value reversal;
- short-horizon raw directional persistence;
- simple contraction-to-expansion trade rules;
- signed cross-sectional dispersion as a direction predictor;
- close-location pressure as a direction predictor;
- simple cross-pair lead-lag direction;
- post-hoc pair dropping or selection from these results;
- sign inversion of failed trials;
- time/lookback/threshold searches intended to rescue a failed exact hypothesis.

### Supported but non-directional
- cross-sectional dispersion as a market-activity state;
- activity state as a predictor of subsequent movement relative to spread/friction;
- signal-to-friction as an economically meaningful admissibility concept.

These may later be used as independently governed context for an already-supported strategy, but should not be mined for direction after the fact.

### Supported but prospectively unresolved
- Q003 ratio-only candidate;
- RND-0060P activity-admissibility policy mechanism.

Both must remain frozen during accumulation.

### Materially unexplored
The project has not yet adequately tested directional mechanisms rooted in external information arrival, session inventory transfer, dynamic liquidity/price interaction, or independent macro/cross-asset information.

Those areas have stronger causal/economic motivation than another local price-pattern permutation.

---

## 3. Major methodological lessons

1. **Development improvement is not validation.** RND-0039 and RND-0042 demonstrated this directly.
2. **Costs must enter the hypothesis, not be appended cosmetically.** Signal-to-friction was more informative than absolute volatility alone.
3. **Non-directional structure can be real and useful without being a strategy.** H/L are the clearest examples.
4. **Negative trials are valuable when they close hypothesis space.** A–K and T materially reduce the temptation to recycle familiar technical-pattern ideas.
5. **One declared trial is superior to broad search when the aim is scientific learning.** The RND-0060 firewall should remain the default model.
6. **Future hypotheses should have a causal/economic source of direction.** Purely endogenous short-horizon price patterns have had a poor record in governed testing.
7. **Prospective time is part of the experiment.** It should not be shortened by peeking or altered by candidate modification.
8. **Infrastructure should now be built only where it removes a specific scientific or future-operational bottleneck.** More architecture for its own sake has diminishing value.

---

## 4. Ranked next-generation research agenda

### Rank 1 — Scheduled macro-information shock response
**Question:** Do major scheduled macroeconomic information releases create a reproducible, cost-surviving post-release directional response in one or more of the four FX pairs under a single predeclared reaction rule?

**Why this ranks first**
Direction would come from new information entering the market, not from a generic technical pattern. The economic mechanism is clear: prices reprice to information surprises, and incomplete/heterogeneous interpretation can create short post-release continuation or correction.

**Required work before any trial**
- acquire and seal an authoritative event calendar and, if feasible, consensus/actual surprise data;
- define one event class or one economically coherent event basket before opening returns;
- define a fixed event-time alignment and one response horizon;
- specify treatment of widened spreads and missing/irregular quotes;
- avoid event-by-event, pair-by-pair, or horizon search.

**Primary risk**
High degrees of freedom if event classes, surprise definitions, pairs, windows, or directions are mined.

**Expected information gain**
High. A negative result would close an economically important class rather than merely another chart pattern.

### Rank 2 — Session-handoff inventory / information-transfer mechanism
**Question:** Does a fixed, economically motivated transfer between major trading sessions produce reproducible continuation or correction conditional on the direction and magnitude of the prior session move?

Examples of economically motivated handoffs include Asia-to-Europe or Europe-to-North-America. The research design must choose one handoff and one fixed prior-session state before outcome testing.

**Why this ranks second**
FX is a 24-hour market with changing dealer/client populations and liquidity. Inventory transfer and information assimilation across session boundaries provide a plausible directional mechanism distinct from the failed generic opening-range breakout.

**Independence requirement**
The hypothesis must not become “RND-0060A with a different clock time.” It should be formulated around prior-session inventory/information transfer, with fixed state and response definitions.

**Primary risk**
Time-window mining and hidden similarity to previously failed breakout/reversal trials.

**Expected information gain**
High if the trial is frozen narrowly.

### Rank 3 — Dynamic liquidity/price-interaction asymmetry
**Question:** Does the *change and asymmetry* of executable spread/liquidity conditions around a price move contain directional information about the next interval?

This is distinct from RND-0060F, which examined spread state rather than a predeclared joint price-liquidity transition mechanism.

A possible scientific form would ask whether an identically sized move accompanied by liquidity withdrawal versus liquidity normalization has systematically different subsequent direction.

**Why this ranks third**
The project already knows friction matters. A joint transition hypothesis has a plausible microstructure basis: price movement under worsening liquidity may represent different order-flow conditions from movement under improving liquidity.

**Primary risk**
Top-of-book bid/ask data are only a limited proxy for liquidity; no volume/order-book depth is available in the current core dataset.

**Expected information gain**
Medium-high, especially because a negative result would clarify the limits of spread-only microstructure data.

### Rank 4 — Independent rates / macro cross-asset context
**Question:** Can independently sourced intraday rates or macro-risk information provide reproducible directional context for FX that is absent from price-only features?

Candidate information families include short-rate expectations, liquid rate futures, or other genuinely external macro state variables. The exact source must be governed before testing.

**Why this ranks fourth**
FX is fundamentally a relative-price market linked to interest-rate expectations and macro risk. Adding independent information may offer a more credible source of direction than extracting increasingly complex features from the same four FX price series.

**Primary risk**
New data provenance, licensing, timestamp alignment, survivorship/revision issues, and a large potential search space.

**Expected information gain**
High, but implementation cost and data-governance burden are materially larger than ranks 1–3.

### Rank 5 — Multi-horizon path-efficiency / exhaustion mechanism
**Question:** Does the geometry of a fixed longer-horizon move distinguish continuation from exhaustion better than raw short-horizon directional persistence?

A defensible trial would predeclare one path-efficiency statistic, one lookback, one direction rule, and one forward horizon.

**Why this ranks fifth**
There is a plausible distinction between a smooth directional auction and a noisy path that arrives at the same endpoint. However, this remains closer to the price-pattern family already weakened by RND-0060D/K than the first four directions.

**Primary risk**
High overlap with failed persistence/pressure ideas and therefore a substantial danger of disguised rescue research.

**Expected information gain**
Medium. Pursue only after the higher-ranked economically grounded directions.

---

## 5. Ideas not worth pursuing now

Do not spend the prospective waiting period on:
- .00055/.00065/etc. threshold refinement;
- pair-specific Q003 tuning;
- dropping AUDUSD or another weak pair based on prior outcomes;
- rerunning consumed 2021–2022 validation;
- opening 2023–2024 reserved final;
- optimizing RND-0060P's cutpoint;
- finding a direction inside RND-0060H after the fact;
- trying the opposite sign of A–K or T;
- mining many session hours and selecting the best;
- broad indicator libraries or automated genetic/grid search without a new scientific admission standard;
- additional execution architecture with no identified missing operational requirement.

These would increase degrees of freedom without proportionate scientific information.

---

## 6. Recommended next research sequence

### Step 1 — Research Admission & Multiple-Hypothesis Standard
Before testing the first new direction, freeze a common admission standard for the next generation of experiments. It should require:
- explicit economic mechanism;
- exact data inputs;
- one declared primary statistic/outcome;
- fixed direction/sign logic;
- fixed lookback/horizon;
- transaction-cost treatment;
- minimum effect criterion;
- annual/pair robustness requirements;
- leave-one-year or comparable stability check where appropriate;
- experiment-family registry so multiple testing is visible;
- rule for when a failed trial closes a hypothesis family;
- rule for when a positive development result is strong enough to justify candidate review.

This should be the immediate next task.

### Step 2 — Data-readiness study for Rank 1
Inventory what authoritative macro-event data can be acquired and sealed without touching prospective streams. The first study should be data/provenance only, not outcome testing.

### Step 3 — Freeze one Rank-1 hypothesis
Only after the data is sealed should one event-response hypothesis be selected and frozen.

### Step 4 — Run one governed development trial
Use only permitted development evidence. No validation/final/prospective contamination.

### Step 5 — Close or advance without rescue
If falsified, close the exact family and move to Rank 2. If strongly supported under the admission standard, proceed to a separate candidate-review task rather than immediately tuning or validating.

---

## 7. What remains blocked pending prospective evidence

Until the frozen prospective gates mature and a human readout is explicitly authorised, the project must not:
- inspect Q003 prospective trades, returns, P&L, equity, drawdown, win rate, pair rankings, or other economic outcomes;
- inspect RND-0060Q/R prospective ADMIT-vs-VETO economic comparisons;
- claim prospective confirmation of either mechanism;
- promote Q003;
- promote the activity policy into a directional strategy;
- open reserved final;
- allocate capital;
- enable broker writes or live execution.

The earliest time-based Q003 readout remains 2027-04-03T07:25:00Z, subject to its structural gate and explicit human readout approval.

The RND-0060Q/R time gate remains 2027-04-07T02:33:50Z and additionally requires at least 100 eligible non-DEFER observations, structural integrity, and explicit human readout approval.

---

## 8. Project-level conclusion

The project should no longer be described primarily as an attempt to refine one historical backtest. It is now a governed experimental program for discovering whether a robust intraday FX edge exists and, if one is earned, carrying it safely from research through prospective evidence, shadow execution, risk control, and eventual human-authorised deployment.

The most important scientific transition is this:

**Earlier work searched largely inside price patterns. The next generation should search for economically grounded sources of directional information.**

The recommended immediate successor to RND-0061 is therefore a methodological task: freeze the Research Admission & Multiple-Hypothesis Standard before opening the first next-generation hypothesis.

No prospective outcome was opened in this review. No validation or reserved-final evidence was consumed. No promotion, capital, broker-write, or live-execution authority was granted.
