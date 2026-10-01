# RND-0035 — Adversarial M005 Development Robustness Contract

Status: R&D CANDIDATE / NON-OPERATIONAL
Issue: #39
Foundation: `ee163e375dfc2403b34f41f83a962267b23bda69`

## Research question

Which, if any, parts of frozen M005 behaviour survive predeclared hostile robustness tests on authorized 2015–2019 development evidence without outcome-driven rescue?

The purpose is falsification and robustness measurement, not optimization.

## Evidence boundary

Authorized: governed AUDUSD, EURUSD, GBPUSD and USDJPY M5 evidence for 2015–2019 only.

Unauthorized: validation outcomes, reserved final-test outcomes, ungoverned 2020 evidence, Champion reconstruction, operational M006e evidence changes.

RND-0035 is not full-development validation and is not out-of-sample confirmation.

## Immutable reference

RND-0034 is reference trial R000:

- fast MA 20
- slow MA 50
- volatility window 12
- population volatility (`ddof=0`)
- volatility threshold 0.0005
- signal delay 1 observed contiguous bar
- minimum hold 3 observed bars
- AUDUSD UTC session [11,14)
- EURUSD UTC session [11,13)
- GBPUSD UTC session [11,13)
- USDJPY UTC session [11,13)

Reference reconstruction evidence is never rewritten.

## Known-outcome disclosure

Before RND-0035, RND-0034 revealed adverse AUDUSD behaviour, 2015-concentrated EURUSD net performance, consistently gross-positive but net-negative GBPUSD, near-flat gross/net-negative USDJPY, and declining trade counts over time.

Accordingly, GBPUSD-specific, cost-specific, temporal-concentration and trade-density investigations are outcome-informed. They remain legitimate falsification analyses but are not untouched confirmation.

## Frozen attack families

A. Local parameter perturbation — bounded neighbourhood only; measure cliff-edge dependence; no best-variant selection.

B. Temporal/cross-pair concentration — pair, year, pair×year, early/late period, trade-density and contribution concentration; no dropping adverse evidence.

C. Session sensitivity — symmetric local boundary perturbations only; no broad hour search and no Champion reconstruction.

D. Cost/slippage stress — observed bid/ask baseline plus adverse predeclared execution-cost increments only.

E. Gap-policy sensitivity — conservative alternatives only; no synthetic prices, silent bridging or documentary calendar claims.

F. Conservative execution variants — equal or less favourable than reference; no mid execution, favourable path ordering, hindsight exits or manufactured fills.

G. Dependence-aware resampling — stationary/block bootstrap with frozen seeds/configuration/statistics; IID bootstrap may be secondary only.

## Trial accounting

Before outcomes for a family are generated, its exact candidate universe must be persisted in a machine-readable append-preserving trial plan. Each trial requires:

- immutable trial ID;
- attack family;
- exact configuration;
- classification (`REFERENCE`, `PREDECLARED_ADVERSARIAL`, `OUTCOME_INFORMED`, or later `POST_HOC`);
- authorized symbols/years;
- seed/configuration where applicable;
- lifecycle status;
- result/evidence identity after execution.

Structurally invalid, failed, adverse and null trials remain counted. Declared and executed trial counts must both be reported. Later exploratory trials may be appended only as `POST_HOC` or `OUTCOME_INFORMED`; they cannot be backdated into the predeclared family.

## Outcome-blind implementation gate

Before running new robustness outcomes:

1. freeze exact family grids/configurations and trial IDs;
2. fixture-test parameterization and prohibitions;
3. reproduce RND-0034 reference behaviour unchanged;
4. verify authorized evidence identity;
5. verify validation/final-test access remains false;
6. verify broker writes, capital authority and promotion authority remain false.

No family result may be used to modify that same family’s frozen grid and still be described as predeclared.

## Falsification questions

1. Are results stable under nearby specifications or cliff-edge dependent?
2. Are positive effects concentrated by pair, year, subperiod or a small set of trades?
3. Do effects survive actual bid/ask costs and modest adverse cost/slippage stress?
4. Are conclusions stable to local session-boundary perturbation?
5. Are conclusions materially dependent on gap semantics or optimistic execution?
6. Are outcomes stable under dependence-aware resampling?
7. Is there sufficient robust development evidence merely to justify proposing a separately governed validation design?

## Interpretation categories

- `ROBUSTNESS_NOT_DEMONSTRATED`
- `MIXED_OR_CONCENTRATED_DEVELOPMENT_EVIDENCE`
- `DEVELOPMENT_ROBUSTNESS_WARRANTS_SEPARATE_VALIDATION_DESIGN`

These are descriptive research dispositions, not promotion states. None opens validation automatically.

## Acceptance of RND-0035

RND-0035 succeeds as a research task when its predeclaration, trial accounting, deterministic execution, evidence identity, adverse-result preservation and safety gates are correct. M005 economic failure is a valid successful research result.

## Prohibitions

No validation/final-test outcomes; no Champion reconstruction; no broad optimization; no selecting a new champion from perturbations; no deletion of failed/adverse trials; no synthetic/interpolated/backfilled candles; no favourable cost/execution/path assumptions; no empirical calendar promotion; no portfolio/capital optimization; no strategy/risk promotion; no broker writes/order endpoints; no operational M006e modification; no automatic merge.

Human approval remains mandatory for merge, promotion, authority changes and anything involving execution or capital.

## Boundary

RND-0035 ends with the frozen 2015–2019 adversarial matrix and evidence package. RND-0036 scope is selected only afterward; RND-0035 does not silently expand into 2020 acquisition, validation, Champion reconstruction or autonomous strategy discovery.
