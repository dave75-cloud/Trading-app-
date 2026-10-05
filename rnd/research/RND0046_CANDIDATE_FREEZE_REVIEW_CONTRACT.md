# RND-0046 — Q003 Candidate-Freeze Review

Status: **FORMAL REVIEW / NO CANDIDATE FROZEN YET**

## Purpose

RND-0046 is a governance review, not a new parameter study and not a validation run.

It asks whether the already-defined RND-0044 Q003 mechanism is sufficiently specified, economically plausible, structurally coherent, and development-complete to be frozen unchanged as the next candidate for genuinely fresh validation evidence.

Candidate freeze is not promotion, shadow authority, broker authority, or capital authority. It is a commitment to stop development tuning of the candidate before obtaining new validation evidence.

## Candidate under review

Candidate identifier: `Q003_RATIO_ONLY_8_0_FOUR_PAIR`

Frozen mechanics if approved:

- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY;
- timeframe: M5;
- fast MA: 20;
- slow MA: 50;
- volatility window: 12;
- population standard deviation (`ddof=0`);
- entry volatility/friction rule: `signal_to_friction >= 8.0`;
- no absolute volatility floor;
- one-observation signal delay;
- minimum hold: 3 observed bars;
- frozen UTC sessions unchanged;
- mid-price signals;
- long execution: ask entry / bid exit;
- short execution: bid entry / ask exit;
- frozen RND-0034 gap semantics;
- four-pair universe unchanged;
- no pair weights or pair-specific parameters.

## Evidence permitted for this review

Already-consumed development evidence only:

1. RND-0044 authoritative ratio-only development report:
   - path: `~/Trading-evidence/rnd0044-ratio-only-development-20261005.json`
   - SHA-256: `8f30a8a12e13786bc1dc730d1468197e3b246c8141be4cee410bf3178547fc7b`
   - classification: `RATIO_ONLY_MIXED_OR_NON_MONOTONIC` under the RND-0044 automatic classification rule.

2. RND-0045 authoritative cross-pair heterogeneity report:
   - path: `~/Trading-evidence/rnd0045-cross-pair-heterogeneity-20261005.json`
   - SHA-256: `c951fa6cd2febc79400c1578386df4a05ad4bc7827920cc52171fca318225716`
   - classification: `COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW`.

No validation, reserved-final, post-2020, or other newly acquired outcome evidence may be used in this decision.

## Known supporting evidence

RND-0044 Q003 showed:

- positive four-pair completed-trade net-return sum;
- four-pair equal-unit terminal normalized equity above 1.0;
- concurrent drawdown well inside the frozen -10% ceiling;
- positive leave-one-year-out improvement versus Q000 for all six excluded years;
- positive leave-one-pair-out improvement versus Q000 for all four excluded pairs;
- positive aggregate development years in 2015, 2016, and 2020;
- no single positive development year above the frozen 70% concentration limit.

RND-0045 showed:

- Q003-vs-Q000 full-period treatment effect positive for all 4 pairs;
- aggregate treatment effect positive in 5 of 6 years;
- at least 3 of 4 pairs positive in 5 of 6 years;
- all leave-one-pair-out aggregate treatment effects positive;
- maximum positive pair treatment-effect share 0.6865762292175398, inside the predeclared 0.70 cap.

## Known weaknesses

The review must not conceal the following:

- RND-0044 Q003 did not satisfy its automatic candidate-freeze-review rule because only EURUSD and GBPUSD had net equity >= 1.0; USDJPY was close to flat and AUDUSD remained materially negative in absolute Q003 economics;
- RND-0045 demonstrates common improvement versus Q000, not unseen profitability;
- pair-effect concentration is close to the 70% ceiling;
- all evidence considered here is development evidence and therefore cannot establish out-of-sample transferability.

## Review questions

A freeze recommendation requires affirmative answers to all:

1. Is the candidate completely specified with no unresolved trading-rule choice?
2. Has parameter exploration for this mechanism stopped at a defensible predeclared point rather than an outcome-selected nearby value?
3. Is aggregate net development economics positive after executable spread costs?
4. Is drawdown controlled under the frozen development diagnostics?
5. Is there evidence that improvement is not solely attributable to one pair or one year?
6. Has cross-pair transferability reached the predeclared RND-0045 candidate-review gate?
7. Can the next meaningful question only be answered with genuinely fresh evidence rather than more development tuning?
8. Are validation, reserved-final, broker, sizing, promotion, and capital authorities still closed?

## Allowed decision

Exactly one of:

- `RECOMMEND_FREEZE_Q003_FOR_FRESH_VALIDATION`
- `EXTEND_DEVELOPMENT_BEFORE_FREEZE`
- `REJECT_Q003_CANDIDATE`

A recommendation does not itself freeze the candidate. Final candidate freeze requires explicit human approval after reviewing the RND-0046 assessment.

## Governance

- new thresholds: **FALSE**
- pair dropping: **FALSE**
- pair-specific rules: **FALSE**
- pair weighting: **FALSE**
- development rerun for selection: **FALSE**
- validation access: **FALSE**
- reserved final open: **FALSE**
- shadow authority: **FALSE**
- portfolio sizing: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**
- automatic candidate freeze: **FALSE**
- automatic merge: **FALSE**
- human freeze decision required: **TRUE**
