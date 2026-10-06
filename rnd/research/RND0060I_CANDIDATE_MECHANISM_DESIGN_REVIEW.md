# RND-0060I — Cross-Sectional Activity Candidate-Mechanism Design Review

Status: FROZEN DESIGN REVIEW
Authority: DEVELOPMENT-ONLY RESEARCH; HUMAN-ONLY PROMOTION
Parent finding: RND-0060H CROSS_SECTIONAL_STRUCTURE_DETECTED

## Purpose
Determine whether the RND-0060H cross-sectional dispersion state can legitimately support a standalone trading candidate without post-hoc threshold, pair, direction, session, horizon, or sizing selection.

## Fixed inherited finding
At 11:30 UTC, the population standard deviation of the four USD-oriented 30-minute returns across AUDUSD, EURUSD, GBPUSD, and USDJPY is positively associated with greater market-wide realized movement over the following 30 minutes.

RND-0060H did **not** establish directional predictability.

## Candidate admissibility rules
A standalone candidate is admissible only if all of the following are true:

1. Direction is logically implied by the frozen RND-0060H finding itself, rather than selected after observing development outcomes.
2. Pair selection is not based on post-hoc ranking from RND-0060H.
3. No new threshold is chosen from the observed dispersion distribution.
4. No alternative observation time, lookback, forward horizon, hold period, weighting rule, or session is selected from RND-0060H outcomes.
5. No previously falsified RND-0060A through RND-0060E rule is revived merely by conditioning on the RND-0060H state.
6. No Q003 logic is imported.
7. Validation 2021–2022 and reserved final 2023–2024 remain closed.
8. No broker writes, live authority, capital authority, automatic promotion, or automatic merge is permitted.

## Review
RND-0060H is an activity/magnitude state variable. It indicates when subsequent movement is more likely to be larger, but it does not identify:

- long versus short direction;
- which one of the four pairs should be traded;
- convergence versus continuation;
- breakout versus mean reversion;
- an economically justified entry threshold;
- a position size or portfolio allocation.

Any attempt to create a complete trading rule directly from RND-0060H therefore requires at least one additional directional or selection assumption that was not established by RND-0060H. Selecting such an assumption after observing the RND-0060H development result would constitute a new hypothesis, not a direct candidate freeze.

## Decision
**NO_STANDALONE_DIRECTIONAL_CANDIDATE_FROM_RND0060H**

RND-0060H is retained as a validated development-only context variable: `CROSS_SECTIONAL_ACTIVITY_STATE`.

It may be used only in a future separately predeclared task that introduces one independent directional mechanism and tests whether the fixed H-state has incremental value. That future task must define the directional mechanism and any gating rule before outcome access and must not tune the H-state threshold from RND-0060H diagnostics.

## Recommended next task
RND-0060J — Directional Information Conditional on Cross-Sectional Activity State.

The task should remain non-trading initially and ask a narrow structural question: whether one independently specified directional statistic at 11:30 UTC has reproducible association with the sign of subsequent 30-minute USD-oriented returns, while the RND-0060H dispersion measure is treated only as a fixed contextual variable rather than a mined threshold.

## Prohibitions
Do not:

- choose GBPUSD because it looked strongest elsewhere;
- select top-quartile or another dispersion threshold because RND-0060H quartiles separated well;
- revive opening-range breakout, displacement mean reversion, relative-value convergence, three-bar persistence, or contraction-expansion rules merely under high dispersion;
- optimize direction, threshold, pair, hold, session, weighting, or sizing;
- inspect validation or reserved-final evidence;
- create strategy-candidate, broker, capital, promotion, or merge authority from this review.

## Governance flags
- development_only: TRUE
- parameter_search: FALSE
- trade_simulation: FALSE
- pnl: FALSE
- strategy_candidate: FALSE
- validation_open: FALSE
- final_test_open: FALSE
- reserved_final_access: FALSE
- broker_writes: FALSE
- capital_authority: FALSE
- automatic_promotion: FALSE
- automatic_merge: FALSE
