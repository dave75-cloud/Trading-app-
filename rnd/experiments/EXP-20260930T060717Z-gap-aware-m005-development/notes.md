# RND-0034 — gap-aware fixed-M005 development reconstruction

Experiment: `EXP-20260930T060717Z-gap-aware-m005-development`

RND-0034 deliberately pivots from historical-data acquisition into quantitative
research. It reconstructs one frozen M005 trial on verified 2015-2019
development-only evidence.

The task does not acquire more history and does not open 2020, validation or
reserved-final-test outcomes.

## Design decisions

- Canonical M005 behavior is taken from the audited OANDA-authoritative path:
  MA20/MA50, vol12 population standard deviation (`ddof=0`), threshold
  0.0005, fixed UTC sessions, one-bar delayed desired signal and three-bar
  minimum hold.
- Signal state uses midpoint closes; execution uses actual OANDA bid/ask.
- Every observed timestamp discontinuity resets indicator and delayed-signal
  continuity.
- A live trade encountering a gap is censored as indeterminate, never assigned
  a synthetic exit.
- Pair-level unit-normalized research is permitted; cross-pair portfolio sizing
  is deliberately deferred because RND-0034 has no authority to invent a new
  allocation convention.
- Every external shard must pass existing integrity verification and match the
  repository-bound RND-0032/RND-0033 identity before strategy evaluation.

Implementation validation and the real local-evidence reconstruction are
pending.
