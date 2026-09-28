# Legacy research reconstruction audit

Status: R&D CANDIDATE / NON-OPERATIONAL
Task: RND-0025
Base reviewed: `1c6fd4641f275b70519b167a2493d7908ad1c1bc`

## Scope

This audit records what the repository can establish about the historical
research path. It deliberately does not rerun parameter searches, rank
strategies or alter canonical M005/M006e.

## Champion lineage

`cli/build_champion_fx_portfolio.sh` identifies a three-leg Champion
construction using sized GBPUSD, USDJPY and AUDUSD trade logs and applies
hour/direction/minimum-bars filters before portfolio aggregation.

The referenced sized input logs and resulting Champion equity file are not
tracked at this foundation. The historical headline result therefore cannot be
reproduced from the governed repository alone. It remains a useful research
lead, not established performance evidence.

## Synthetic loss-clipping hazard

`cli/apply_position_sizing.py` multiplies `net_return` by a notional factor
and then applies `clip(lower=-max_loss)`. This truncates sufficiently large
losses after the completed return is known while leaving gains uncapped.

The surviving repository does not prove that the missing Champion sized logs
were produced by this script, so RND-0025 does not make that claim. It does
establish that any performance series produced by this synthetic one-sided
clipping method is unsuitable as evidence of an executable stop-loss strategy.
Later tooling independently labels clipped runs as legacy diagnostics that do
not override frozen M004/M005.

## Selection and walk-forward limitations

`cli/sweep_simple_backtest.py` is useful exploratory tooling, but parameter
combinations are evaluated and ranked on the history being searched. It does
not by itself establish out-of-sample performance.

The generic `monthly_walkforward()` path evaluates later monthly slices but
does not implement an independent per-fold parameter-training/selection
process. It should not be treated as sufficient protection from strategy
selection bias.

## Data-pipeline inconsistency

The generic storage helper named `append_day_parquet()` writes `data.csv`,
while the generic `cli/backtest.py` loader searches recursively for
`*.parquet`. The historical research components therefore do not yet form one
coherent end-to-end reproducible data/backtest pipeline.

## Portfolio limitations

Legacy portfolio aggregation sequentially compounds completed trade returns.
That is not equivalent to a portfolio ledger with simultaneous open positions,
mark-to-market equity, shared-currency exposure and time-varying transaction
costs.

The IID Monte Carlo tool resamples completed trade returns independently. It is
a diagnostic, not a dependence-preserving stress model.

## What is reproducible

The frozen M005/M006e strategy semantics are much stronger than the legacy
performance path. Repository audits independently encode MA20/MA50, 12-bar
volatility, the 0.0005 threshold, session eligibility, delayed signals,
minimum-hold behaviour and state transitions, and compare those semantics
against the operational observer.

That establishes behavioural reproducibility. It does not by itself establish
positive expected value.

## Required reconstruction

A later task may reconstruct Champion and M005 only after the RND-0025 research
contract is accepted. Reconstruction must start from immutable source snapshots,
declare all searched choices/trials, use explicit event-driven execution, and
keep a final chronological test partition untouched until the candidate is
frozen.
