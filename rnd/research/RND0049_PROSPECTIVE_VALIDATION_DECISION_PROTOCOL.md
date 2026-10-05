# RND-0049 — Prospective Validation Decision Protocol

Status: PREDECLARED / OUTCOMES CLOSED

## Purpose

Freeze the decision rule that will be applied to the already-frozen Q003 candidate after the RND-0048 prospective accumulation horizon is complete. This protocol is written before any prospective Q003 signal, trade, return, equity, drawdown, pair contribution, month contribution, or validation classification is opened.

Candidate ID: `Q003_RATIO_ONLY_8_0_FOUR_PAIR`

Candidate fingerprint: `25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`

Prospective evidence start: `2026-10-05T07:25:00Z`

Earliest ordinary validation readout boundary: `2027-04-03T07:25:00Z`

Reserved 2023–2024 final evidence remains sealed and is not part of this protocol.

## Governing principle

The decision rule is frozen before outcomes so that the result cannot be rescued by threshold changes, pair removal, pair weighting, horizon extension, or selective interpretation after prospective evidence is visible.

A structurally valid economic failure is a rejection, not an invitation to extend observation because the result was close.

## Stage 0 — evidence admissibility gate

No Q003 outcome calculation is permitted unless every condition below passes:

1. elapsed prospective horizon is at least 180 calendar days from `2026-10-05T07:25:00Z`;
2. all admitted evidence begins at or after the frozen prospective boundary;
3. all admitted tranches are immutable and SHA-bound;
4. tranche chronology is non-overlapping and contiguous except for explicitly recorded genuine market gaps;
5. all four frozen symbols are represented: AUDUSD, EURUSD, GBPUSD, USDJPY;
6. timeframe is M5 and evidence contains bid/ask/mid complete candles only;
7. no synthetic/interpolated/backfilled candle or price is admitted;
8. every structural integrity verifier passes or every failure is explicitly resolved without changing market evidence;
9. Q003 candidate fingerprint matches exactly;
10. no candidate parameter, pair universe, session, delay, hold, execution, cost, or gap semantic has changed after freeze;
11. reserved-final evidence remains unopened;
12. no broker writes, capital authority, automatic promotion, or live authority has been granted.

If any admissibility item fails at the scheduled boundary, classification is `VALIDATION_INCONCLUSIVE_STRUCTURAL` and the evidence window may be extended only long enough to repair or replace missing/invalid prospective coverage. Economic results must remain unopened until the structural defect is resolved.

## Stage 1 — one-time prospective economic evaluation

After a separate explicit human open gate, run Q003 exactly once against the complete admitted prospective evidence package.

Permitted outputs:

- completed trade ledger;
- pair-level gross and net returns;
- observed bid/ask transaction-cost drag;
- pair-level terminal unit-normalized equity;
- pair-level maximum drawdown;
- concurrent four-pair unit-normalized portfolio equity;
- concurrent portfolio maximum drawdown;
- realized portfolio net-return sum;
- calendar-month attribution;
- pair contribution attribution;
- trade-count and holding-time diagnostics;
- gap-exposure diagnostics;
- integrity/reconciliation diagnostics.

No comparator strategy, nearby ratio, old absolute threshold, pair-specific variant, pair dropping, weighting search, session variant, hold variant, or rescue configuration is permitted.

## Primary validation support rule

Classification is `VALIDATION_SUPPORTED` only if all of the following pass:

1. concurrent four-pair terminal normalized equity is strictly greater than `1.0`;
2. realized four-pair net-return sum is strictly greater than `0.0`;
3. at least three of four pairs have terminal net unit-normalized equity greater than or equal to `1.0`;
4. concurrent portfolio maximum drawdown is no worse than `-0.10`;
5. no single pair contributes more than `70%` of total positive pair contribution magnitude;
6. no single calendar month contributes more than `60%` of total positive monthly contribution magnitude;
7. positive contribution is observed in at least two distinct calendar months;
8. all reconciliation and integrity checks pass;
9. the result is obtained with observed bid/ask execution costs and the frozen Q003 mechanics, with no favourable execution substitutions.

If positive-contribution denominator is zero, the corresponding concentration condition fails.

## Rejection rule

If Stage 0 passes but any Primary Validation Support Rule item fails, classification is `VALIDATION_REJECTED`.

There is no economic `NEAR_PASS`, `WATCH`, or discretionary extension category.

## Structural inconclusive rule

`VALIDATION_INCONCLUSIVE_STRUCTURAL` is allowed only for evidence integrity/coverage failure that prevents a valid one-time evaluation. It may not be used because returns, pair breadth, concentration, drawdown, or other economic results are disappointing or close to threshold.

## Post-result prohibitions

After prospective outcomes are visible:

- no nearby ratio thresholds;
- no return to absolute-volatility thresholds;
- no pair dropping;
- no pair-specific thresholds or sessions;
- no pair weighting selected from prospective outcomes;
- no extending the same validation merely because the candidate nearly passed;
- no rerunning the same evidence under modified transaction costs or execution rules to rescue the result;
- no treating 2023–2024 reserved-final evidence as a rescue validation set;
- no automatic shadow/live promotion;
- no capital allocation;
- no broker writes;
- no automatic merge.

A rejected Q003 is closed as a candidate on this evidence. Any successor must be a new candidate with a new identity and separately governed development path.

## Meaning of support

`VALIDATION_SUPPORTED` means only that Q003 has passed its predeclared 180-day prospective validation rule. It does not authorize live trading, broker writes, capital allocation, sizing, reserved-final opening, or automatic promotion. Any later shadow/risk/execution transition requires separate human-approved governance.

## Human gates

Human approval remains mandatory for:

1. opening prospective economic outcomes after Stage 0 passes;
2. accepting the classification report;
3. any later shadow-stage candidate admission;
4. any risk allocation;
5. any broker-write capability;
6. any live/capital authority.
