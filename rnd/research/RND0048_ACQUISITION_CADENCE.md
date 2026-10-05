# RND-0048 — Prospective Acquisition Cadence

Status: FROZEN

## Purpose

Define a fixed, outcome-blind cadence for prospective OANDA PRACTICE evidence accumulation under the frozen Q003 candidate.

## Cadence

- normal tranche duration: 7 calendar days
- tranche boundaries: exact M5 UTC boundaries
- continuity rule: each new tranche starts exactly at the prior tranche end
- first regular accumulation tranche starts: 2026-10-05T07:35:00Z
- first regular accumulation tranche ends: 2026-10-12T07:35:00Z
- subsequent regular tranches advance in contiguous 7-day windows
- final tranche may be shorter solely to terminate at the frozen 180-day readout boundary
- earliest validation-readout boundary remains: 2027-04-03T07:25:00Z

## Acquisition semantics

Every tranche must use the existing RND-0047 GET-only OANDA PRACTICE acquisition and sealing architecture with:

- AUDUSD, EURUSD, GBPUSD, USDJPY
- M5
- bid/ask/mid
- complete candles only
- no synthetic fill
- immutable raw and canonical evidence hashes
- explicit gap ledger
- no overwrite of prior sealed evidence

## Blindness

During accumulation, no tranche may be used to compute or expose:

- Q003 signals
- simulated trades
- returns or PnL
- equity
- drawdown
- win rate
- pair rankings
- strategy comparisons
- parameter-selection evidence

Acquisition frequency may not be changed because of strategy performance, because strategy performance remains unavailable during RND-0048.

## Structural exceptions

A tranche may be repeated or extended only for structural reasons such as transport failure, incomplete or corrupt provider evidence, failed hashes, invalid chronology, or unresolved gaps. Such remediation does not authorize strategy evaluation.

## Authority

- strategy evaluation: FALSE
- reserved-final access: FALSE
- broker writes: FALSE
- capital authority: FALSE
- automatic promotion: FALSE
- human review required: TRUE
