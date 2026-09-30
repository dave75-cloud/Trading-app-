# RND-0034 — gap-aware fixed-M005 development reconstruction

Status: R&D CANDIDATE / NON-OPERATIONAL  
Task: RND-0034  
Base: `f67575408ca47ace4196a966f51acfa2b613def1`

## Purpose

RND-0034 is the first quantitative reconstruction step after the governed
historical-data acquisition work. It evaluates one already-frozen M005
configuration on real OANDA bid/ask/mid M5 evidence from 2015-2019 only.

The four-pair 2015 run is the controlled integration pilot. Only after its technical gates pass may the identical frozen engine proceed to the full 2015-2019 reconstruction. This It is not a completed evaluation of the
full predeclared development partition because the 2020 development slice is
not authorized here. It is not validation, final-test evidence, promotion
evidence or trading authority.

## Frozen strategy

There is exactly one trial and no search space:

- pairs: AUDUSD, EURUSD, GBPUSD, USDJPY;
- timeframe: M5;
- fast MA: 20 midpoint closes;
- slow MA: 50 midpoint closes;
- volatility: 12 midpoint-close returns, population standard deviation
  (`ddof=0`);
- volatility threshold: 0.0005;
- UTC sessions: AUDUSD 11:00-14:00; EURUSD/GBPUSD/USDJPY 11:00-13:00;
- raw signal: +1 when fast > slow, -1 when fast < slow, otherwise 0, only
  while in-session and volatility-qualified;
- desired position: one-bar delayed raw signal;
- minimum hold: three observed consecutive bars before exit/reversal.

The audited OANDA-authoritative M005 observer is the behavioral reference.
Older convenience helpers do not override this contract.

## Evidence identity gate

Every evaluated shard must first pass the existing immutable quarantine
verification and must match the canonical identity bound by the RND-0032
(2015) or RND-0033 (2016-2019) repository evidence record.

Returned provider data cannot rewrite historical calendar authority.

## Gap semantics

A historical gap is evidence loss, never a candle.

No interpolation, forward fill, synthetic candle, synthetic price, assumed
signal or assumed execution is permitted.

For reconstruction, consecutive observations must be exactly 300 seconds
apart. Any larger discontinuity:

1. terminates the current contiguous indicator episode;
2. clears MA, return-volatility and delayed-signal history;
3. requires a fresh real-observation warm-up before a new signal can exist;
4. does **not** erase an existing economic position.

Market state, strategy state and portfolio state are distinct. If a position
is open at a discontinuity, the position survives economically. There is no
invented mark or exit inside the missing interval. The first genuine post-gap
bid/ask observation may revalue the surviving position, while strategy
indicators and delayed-signal state remain unavailable until freshly warmed
from contiguous real observations. The gap exposure and elapsed wall time are
recorded explicitly. Missing nominal bars never count toward minimum hold.

An open trade at the authorized sample end is similarly
`RIGHT_CENSORED_END_OF_SAMPLE` and is not force-closed.

## Execution semantics

Signal calculations use midpoint closes. Execution never does.

- long entry: ask close;
- long exit: bid close;
- short entry: bid close;
- short exit: ask close;
- reversal: close the old side and open the new side at the same observed bar
  using the corresponding real bid/ask closes.

Gross return is the same trade measured midpoint-to-midpoint. Net return is
measured from executable bid/ask prices. Execution-cost drag is gross minus
net. No synthetic spread and no lower-tail clipping are allowed.

## Quantitative outputs

Permitted 2015-2019 development-only outputs include per pair:

- completed and end-censored trade counts;
- explicit chronological gap/state/signal/trade/mark events;
- gap-exposed versus non-gap-exposed trades;
- entry/exit timestamps and sides;
- gross and net unit-normalized returns;
- execution-cost drag;
- holding bars;
- hit rate;
- completed-trade compounded equity index and drawdown;
- year attribution;
- contiguous-episode/gap counts and censoring rate.

These are descriptive research observations. RND-0034 also requires
concurrent unit-normalized portfolio/mark-to-market evidence sufficient to
reconcile simultaneous positions; this is accounting evidence, not optimized
sizing or capital allocation. RND-0034 does not introduce cross-pair capital
allocation, account-currency optimization or portfolio ranking.

## Sealed boundary

RND-0034 must reject strategy evaluation for 2020 or later. Validation and
reserved-final-test strategy outcomes remain sealed. Structural identity
verification outside the authorized years does not grant outcome access.

## Authority

No strategy selection, parameter change, Champion-filter evaluation, broker
write, capital authority, calendar promotion, automatic promotion or automatic
merge is granted. Human review remains required.
