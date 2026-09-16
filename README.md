# Trading-app — Current System State

This repository contains the current KQTRL trading research, validation,
forward-observation, and governance stack.

The old GBPUSD/FastAPI/Polygon/Eightcap MT5/AWS architecture is historical
and is not the authoritative current trading system.

## Current phase

**FROZEN FORWARD OBSERVATION**

The objective is validation, not optimisation.

Current controls:

- M006e is the accepted frozen decision/validation stack.
- M006e.9 is the forward-observation framework.
- Operation is ZERO_WRITE_DRY_RUN.
- OANDA environment is PRACTICE only.
- Master execution switch: NO.
- OANDA write methods implemented: NONE.
- Order endpoints invoked: FALSE.
- Live capital: NONE.
- Automatic promotion: NONE.

Active M006e.2 validator:

    tools/m006e/m006e2_twelve_validator.py

Accepted SHA-256:

    d9c5b46b26d1cae4f000d5c584b9afa5e3a06805cb204559dae05013c6d2906d

## Forward-observation graduation

Minimum evidence before consideration for shadow promotion:

- 25 completed and accepted trading sessions; and
- 100 authoritative OANDA events.

Both thresholds are required. Meeting them does not automatically promote
the system.

Permitted dispositions:

- PROMOTE TO SHADOW
- EXTEND OBSERVATION
- REJECT / REENGINEER

Promotion means shadow validation only, never live trading.

## Canonical M005

Canonical operational state:

    data/research_runs/M005_FORWARD_SHADOW_20260804T120245Z/

Frozen configuration SHA-256:

    1ff432d515b955b1a2b16d06a0484166e3eea99d4449c8f9d9fab7147387d646

Canonical M005 and its protected operational source must not be modified by
autonomous R&D.

See:

- AUTONOMY_POLICY.md
- AGENT_BRIEF.md
- .github/workflows/agent_guard.yml

## Autonomous R&D

Autonomous work belongs on `agent/rnd-*` branches and is PR-first.

Autonomous agents may perform research, analysis, diagnostics, tests,
documentation, historical analysis, and non-live candidate development.

They may not autonomously:

- modify frozen M006e;
- modify canonical M005;
- change strategy, sizing, or risk authority;
- enable broker writes;
- add live trading authority;
- promote candidates;
- merge their own pull requests.

Execution-adjacent candidates such as M007 require separate human review.

## Legacy components

Historical code remains from earlier development, including FastAPI,
Streamlit, Polygon, MT5, AWS/Terraform, model-training, and backtesting
components.

These are not authoritative descriptions of the current system and must not
be assumed to possess trading authority.

Obsolete scheduled signal and AWS deployment workflows are being removed
from the current governance branch.

`.github/workflows/ci.yml` performs repository-contained validation of frozen
M006e provenance and static control-plane syntax only. It has no broker,
market-data, deployment, or external-write authority.

## Governing rule

During frozen forward observation:

1. preserve accepted M006e;
2. preserve canonical M005;
3. collect prospective evidence;
4. distinguish provider failures from system defects;
5. keep broker-write authority absent;
6. develop candidates outside the accepted stack;
7. require human review before promotion or execution authority.

Research may move quickly.

The accepted trading system must move deliberately.
