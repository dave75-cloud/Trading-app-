# Predeclared historical window and sealed chronological partition

Experiment: `EXP-20260928T140147Z-historical-window-partition`

## Question

Can the project bind a useful historical horizon and an untouched final-test
period before any M005 outcome is calculated?

## Predeclared rule

The requested horizon is 2015-01-01T00:00:00Z through
2025-01-01T00:00:00Z. Partitions are based on elapsed UTC time at 60/20/20 and
snapped forward to the next M5 boundary.

This produces:

- development ending 2020-12-31T19:15:00Z;
- validation ending 2023-01-01T09:40:00Z;
- reserved final test ending 2025-01-01T00:00:00Z.

All four fixed M005 symbols must satisfy the complete requested horizon or the
evidence gate fails closed. No outcome-dependent common-coverage fallback is
permitted.

## Boundary

The final-test boundary becomes known but remains sealed. Structural identity,
coverage and completeness may be checked; signals, trades, strategy metrics,
parameter selection and ranking remain prohibited.

No OANDA historical request has been made by this experiment. Binding an
acquisition declaration is not execution authority and does not itself fetch
data.

## Independent validation

Exact implementation HEAD: `4ee1561de1ea8bb87ae8740ed7549abf56d5b4b9`

The first independent run on `0ac6d702cd81181cb5fb99b23ad29bcd715ecf2f`
passed all tests and the workspace audit but correctly exposed two trailing-space
defects in this contract through `git diff --check`. The correction changed
only those two Markdown whitespace instances.

The corrected exact implementation HEAD was then independently revalidated in
a clean detached worktree:

- orchestration: 201 tests, OK;
- M006f: 106 tests, OK;
- workspace audit: PASS;
- tasks=29, experiments=28;
- broker_writes=FALSE;
- protected_paths_modified=FALSE;
- promotion_authority=HUMAN_ONLY;
- `git diff --check f342a3b2aa4bca021346df7915f8e9aaed2f5cab...HEAD`: clean.

GitHub safeguards on that same exact implementation HEAD also completed
successfully: Autonomous R&D Guard run 351 and Current System Validation run
350.

No historical data were fetched and no M005 strategy outcome was calculated
during this experiment. The reserved final-test boundary is bound but remains
sealed.

