# RND-0026 historical evidence reconstruction and falsification report

Status: R&D CANDIDATE / NON-OPERATIONAL
Base: `2a493bd0b09f4bd357a8696405d88cd8ab3dc28f`

## Result so far

The surviving repository supports a stronger conclusion about **behavioural
reproducibility** than about historical profitability.

The Champion construction recipe survives, but its three sized input trade logs
and final Champion portfolio CSV are absent from the governed foundation.
Accordingly, the remembered headline Champion result is not reproducible from
Git alone.

M005 is different. Independent audit and observer implementations preserve its
fixed signal/state semantics: MA20/MA50, 12-bar return volatility with ddof=0,
threshold 0.0005, pair-specific UTC sessions, one-bar signal delay, minimum
three-bar hold, and explicit entry/exit/reversal state transitions. This is
valuable reconstruction evidence, but it is not a performance result.

## Falsification findings

### One-sided return clipping

`cli/apply_position_sizing.py` multiplies a completed `net_return` by
notional and then applies a lower-only clip. The RND-0026 pure-local tooling
demonstrates on synthetic returns that this transformation can mechanically
increase terminal equity whenever a scaled loss crosses the floor. It is
therefore unsuitable as evidence that an executable stop-loss would have
produced the same result.

This finding does **not** prove that the missing Champion sized logs were made
with that script. Their provenance is missing, so that linkage remains
unverified.

### Selection contamination

The surviving sweep ranks parameter combinations on the same supplied history.
That is exploratory research, not independent OOS evidence. RND-0026 rejects
overlapping development/validation/test declarations and treats a historical
winner selected from the evaluated history as contaminated unless a separate
untouched test period was reserved in advance.

### Portfolio accounting

The Champion portfolio helper sorts completed trades by entry timestamp and
sequentially compounds `capped_return`. It does not maintain a simultaneous
position ledger or mark open positions to market. If trade intervals overlap,
sequential completed-trade compounding cannot establish the path of portfolio
equity or shared-currency exposure required by RND-0025.

### Ambiguous intrabar execution

The generic legacy simulator explicitly assumes O→H→L→C when both TP and SL
are touched in one bar. That resolves a data ambiguity by assumption and can
produce direction-dependent outcomes. Such bars require conservative treatment,
higher-resolution evidence, or explicit sensitivity analysis in later
performance work.

## M005 performance declaration

RND-0026 does not issue an RND-0025 performance declaration for M005. The
machine-readable gap report records why: no immutable bid/ask historical
snapshot is presently bound to the reconstruction, no untouched final test
window is established from the historical selection lineage, the historical
trial count is incomplete, and no accepted event-driven mark-to-market
reconstruction exists.

The OANDA M006e.1 observer explicitly requests completed M5 **midpoint**
candles. That is strong evidence for prospective behavioural equivalence, but
midpoint bars alone do not satisfy the RND-0025 execution-grade bid/ask
requirement.

## Next controlled stage

The next stage should acquire or identify immutable historical source snapshots
and freeze their provenance before inspecting a reserved final-test period.
Fixed M005 semantics can then be reconstructed without tuning. Only after the
reconstruction implementation and validation protocol are frozen should the
reserved test be opened.

No new strategy search belongs in RND-0026.
