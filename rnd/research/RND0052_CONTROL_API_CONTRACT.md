# RND-0052 — Control / API State Contract

Status: ARCHITECTURE / NO EXTERNAL SERVER / NO EXECUTION AUTHORITY

## Purpose

Define the state and authority model for the future autonomous trading control plane before any live execution capability exists.

This task creates no network server, broker integration, credential path, order endpoint, capital allocation, or automatic promotion.

## Candidate lifecycle states

- `RESEARCH_FROZEN`
- `PROSPECTIVE_ACCUMULATING`
- `VALIDATION_INCONCLUSIVE_STRUCTURAL`
- `VALIDATION_REJECTED`
- `VALIDATION_SUPPORTED`
- `SHADOW_ELIGIBLE`
- `SHADOW_ACTIVE`
- `RISK_REVIEW_REQUIRED`
- `EXECUTION_ELIGIBLE`

`EXECUTION_ELIGIBLE` is an administrative state only. It does not itself grant broker-write authority.

## Human-only transitions

The following transitions require an explicit human authorization record:

- `RESEARCH_FROZEN` -> `PROSPECTIVE_ACCUMULATING`
- `PROSPECTIVE_ACCUMULATING` -> any validation result state
- `VALIDATION_SUPPORTED` -> `SHADOW_ELIGIBLE`
- `SHADOW_ELIGIBLE` -> `SHADOW_ACTIVE`
- `SHADOW_ACTIVE` -> `RISK_REVIEW_REQUIRED`
- `RISK_REVIEW_REQUIRED` -> `EXECUTION_ELIGIBLE`

There is no automatic transition from a validation result to shadow, risk, execution, broker writes, or capital authority.

## Terminal/closed semantics

`VALIDATION_REJECTED` is terminal for that candidate identity.

`VALIDATION_INCONCLUSIVE_STRUCTURAL` may return to `PROSPECTIVE_ACCUMULATING` only to repair/extend structural evidence under the frozen RND-0049 rule; it may not be used for an economic near-pass.

Any change to candidate parameters creates a new candidate identity and cannot reuse an old candidate's state progression.

## Authority dimensions

The control plane tracks these independently:

- `strategy_evaluation_authorized`
- `shadow_authorized`
- `risk_policy_authorized`
- `broker_writes_authorized`
- `capital_authority`
- `live_environment_authorized`

State alone must never imply an authority bit.

## Fail-closed rule

If state and authority disagree, the more restrictive interpretation wins. Missing authority fields mean false. Unknown state or transition means reject.

## Current project authority

For the current Q003 project state:

strategy_evaluation_authorized=FALSE during RND-0048 accumulation
shadow_authorized=FALSE
risk_policy_authorized=FALSE
broker_writes_authorized=FALSE
capital_authority=FALSE
live_environment_authorized=FALSE

## Explicit prohibitions

No broker credentials, order methods, live endpoints, capital sizing, automatic promotion, automatic merge, or Q003 prospective outcome access are introduced by RND-0052.
