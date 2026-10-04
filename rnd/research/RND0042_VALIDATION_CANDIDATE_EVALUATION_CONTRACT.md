# RND-0042 — Validation Candidate Evaluation Contract

Status: **PREDECLARED / OUTCOMES NOT AUTHORIZED**

## Purpose

RND-0042 is the outcome stage for the sole candidate frozen by RND-0040. It may evaluate only the fixed M005 higher-volatility candidate with volatility eligibility threshold `0.0006` on the structurally sealed RND-0041 validation evidence.

This task is confirmatory/falsification-only. It is not a parameter-search, model-selection, portfolio-construction, promotion, final-test, or execution task.

## Governing protocol

The scientific decision rule is inherited unchanged from:

- `rnd/research/RND0040_VALIDATION_CANDIDATE_PROTOCOL.md`
- predeclaration commit: `e7f101948c57d9d527f5b1118696cd24f692ddc1`

No RND-0040 criterion may be relaxed, reinterpreted, added, removed, or reweighted after validation outcomes become visible.

## Evidence binding

RND-0042 may use only the RND-0041 validation evidence structurally sealed before outcome evaluation:

- validation interval start inclusive: `2020-12-31T19:15:00Z`
- validation interval end exclusive: `2023-01-01T09:40:00Z`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- timeframe: M5
- provider/environment: OANDA PRACTICE historical evidence
- structural seal report: `~/Trading-evidence/rnd0041-validation-structural-seal-20261004.json`
- structural seal SHA-256: `b2b9a48e204910d3e87ed7af18ad4b47a35ae33681b1d7c5d1e75a15d22af35c`
- repository seal receipt: `rnd/research/RND0041_VALIDATION_STRUCTURAL_SEAL_RECEIPT.json`
- receipt commit: `9160435e9344078230077f81e5d15d2e400b4a7a`

Reserved-final evidence begins at `2023-01-01T09:40:00Z` and remains closed.

## Candidate identity

Only the following candidate may be evaluated:

- fast MA: 20
- slow MA: 50
- volatility window: 12
- volatility standard deviation: population (`ddof=0`)
- volatility eligibility threshold: `0.0006`
- signal delay: 1 eligible observed bar
- minimum hold: 3 observed bars
- sessions: frozen M005 sessions
- execution: frozen bid/ask semantics
- gap semantics: frozen gap-aware semantics
- universe: all four frozen symbols

No R000 `0.0005` validation rerun is authorized. No alternate threshold or strategy arm is authorized.

## Warm-up

At most 50 genuine M5 observations immediately preceding the validation boundary may initialize state only.

Warm-up observations:

- must come from the development partition;
- may not generate validation trades;
- may not contribute returns, P&L, equity, drawdown, or concentration statistics;
- may not influence parameters or candidate identity;
- must be explicitly identified in the output evidence.

## Frozen primary decision rule

Classification must follow RND-0040 exactly.

`VALIDATION_SUPPORTED` requires all seven conditions:

1. observed four-pair equal-unit normalized terminal equity index > `1.000000`;
2. realized completed-trade net-return sum across four pairs > `0`;
3. at least 3 of 4 pairs have completed-trade net equity index >= `1.000000`;
4. no single pair contributes >70% of positive aggregate completed-trade net-return sum;
5. no single calendar year contributes >70% of positive aggregate completed-trade net-return sum;
6. four-pair equal-unit normalized maximum drawdown >= `-0.10`;
7. no evidence-identity, boundary, leakage, or warm-up violation.

If any of criteria 1, 2, 6, or 7 fail: `VALIDATION_REJECTED`.

If criteria 1, 2, 6, and 7 pass but one or more of criteria 3–5 fail: `VALIDATION_INCONCLUSIVE_CONCENTRATED`.

No post-hoc override is permitted.

## Required outputs

If separately authorized, the evaluation must produce:

- exact evidence identity and seal-SHA verification;
- explicit warm-up provenance and exclusion proof;
- per-pair trade count, hit rate, gross equity, net equity, max drawdown, and execution-cost drag;
- per-calendar-year and pair×year concentration;
- pair contribution shares;
- year contribution shares;
- additional round-trip cost break-even diagnostics by pair;
- frozen stationary-bootstrap diagnostics using the previously declared RND-0035 bootstrap configuration family;
- observed four-pair equal-unit concurrent reference statistics;
- each of the seven primary criteria as PASS/FAIL;
- one mechanically derived final classification from the frozen rule.

## Prohibited actions

RND-0042 may not:

- run any alternate threshold;
- rerun `0.0005` as a validation comparator;
- remove or reweight a pair;
- change sessions, MAs, delay, hold, latency, gap semantics, or cost assumptions;
- inspect or use reserved-final evidence;
- tune from validation outcomes;
- promote the candidate automatically;
- allocate capital;
- perform broker writes;
- merge automatically.

## Authority

- RND-0042 validation outcomes: **FALSE pending separate human authorization**
- candidate identity: fixed `0.0006` only
- parameter search: **FALSE**
- strategy selection: **FALSE**
- reserved final test open: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic merge: **FALSE**
- human review required: **TRUE**
