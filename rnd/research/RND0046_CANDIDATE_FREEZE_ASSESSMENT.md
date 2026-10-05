# RND-0046 — Q003 Candidate-Freeze Assessment

Status: **REVIEW COMPLETE / HUMAN FREEZE DECISION REQUIRED**

Decision recommendation: **`RECOMMEND_FREEZE_Q003_FOR_FRESH_VALIDATION`**

## Executive conclusion

Q003 should now be frozen unchanged as the next candidate for genuinely fresh validation evidence.

This recommendation is deliberately narrower than promotion. It does not assert that Q003 has a proven out-of-sample edge. It asserts that development research has reached the point where the scientifically useful next action is to stop tuning and expose a fixed candidate to new evidence.

Further adjustment of the ratio threshold, pair universe, pair weights, sessions, MA windows, delay, hold time, or volatility construction using 2015-2020 outcomes would now increase data-snooping risk more than it would improve the credibility of the candidate.

## Candidate

`Q003_RATIO_ONLY_8_0_FOUR_PAIR`

- AUDUSD, EURUSD, GBPUSD, USDJPY;
- M5;
- MA20 / MA50;
- 12-return population volatility;
- signal-to-friction ratio >= 8.0 for entry eligibility;
- no legacy 0.0005 absolute volatility floor;
- one-observation delay;
- minimum hold 3 observed bars;
- frozen sessions;
- mid-price signals and bid/ask executable prices;
- frozen gap semantics;
- no pair-specific parameters or weights.

## Review findings

### 1. Complete specification — PASS

There is no unresolved strategy-rule choice inside Q003. The candidate can be fingerprinted without further parameter selection.

### 2. Defensible stopping point — PASS

The ratio values 3.0, 5.0, and 8.0 were predeclared before the RND-0044 outcomes. Q003 uses the existing 8.0 arm; RND-0046 does not introduce a nearby threshold or extend the grid. The project has explicitly rejected post-outcome nudging of the ratio.

### 3. Positive executable development economics — PASS

RND-0044 Q003 produced a positive four-pair completed-trade net-return sum and terminal equal-unit normalized equity above 1.0 after executable bid/ask spread costs.

### 4. Controlled development drawdown — PASS

Q003 concurrent four-pair drawdown remained well inside the predeclared -10% ceiling.

### 5. Concentration / robustness — PASS WITH CAUTION

Q003 improvement versus Q000 survived every leave-one-year-out and leave-one-pair-out comparison used in RND-0044.

RND-0045 strengthened this result: all four pairs had positive full-period Q003-vs-Q000 treatment effects; five of six years had positive aggregate treatment effect; five of six years had at least three positive pairs; and all leave-one-pair-out aggregate treatment effects remained positive.

The maximum positive pair treatment-effect share was 0.6865762292175398, inside but close to the predeclared 0.70 concentration ceiling. This is a material caution for later validation interpretation, not a reason for more development tuning.

### 6. Cross-pair candidate-review gate — PASS

RND-0045 classified the frozen mechanism as `COMMON_MECHANISM_SUPPORTED_FOR_CANDIDATE_REVIEW`.

This result matters because RND-0044 Q003 had only two pairs with absolute net equity >= 1.0. RND-0045 did not erase that weakness; instead it answered the structural question of whether Q003's improvement was common across pairs. The answer was positive for all four pairs relative to the frozen Q000 baseline.

### 7. Need for fresh evidence — PASS

The remaining central uncertainty is unseen transferability. That cannot be resolved credibly by further manipulation of the consumed 2015-2020 development evidence.

The next scientifically meaningful test therefore requires a frozen candidate and genuinely fresh evidence acquired and sealed after the freeze decision.

### 8. Governance closure — PASS

This review does not open:

- consumed 2021-2022 validation evidence for reuse;
- reserved-final 2023-2024 evidence;
- pair dropping;
- pair-specific thresholds or weights;
- sizing or capital allocation;
- shadow or broker authority;
- automatic promotion or merge.

## Important weaknesses carried forward

A freeze must preserve, not hide, these facts:

1. RND-0044 Q003 did not satisfy the old automatic 3-of-4 absolute-positive-pair condition: EURUSD and GBPUSD were above 1.0 net equity; USDJPY was near flat; AUDUSD remained below 1.0.
2. The RND-0045 concentration statistic is close to its 70% limit.
3. Development evidence is fully consumed for this mechanism. It cannot be presented later as independent confirmation.
4. A validation failure must not trigger immediate nearby-threshold rescue work on the same validation evidence.

## Recommendation

**`RECOMMEND_FREEZE_Q003_FOR_FRESH_VALIDATION`**

If the human freeze decision is YES, the next governed task should:

1. create an immutable candidate manifest/fingerprint for Q003;
2. bind code/configuration hashes and the exact four-pair universe;
3. explicitly mark 2015-2020 as development-consumed and 2021-2022 as validation-consumed for prior candidates;
4. keep 2023-2024 reserved-final evidence sealed and unavailable;
5. define a fresh prospective validation evidence window, ideally beginning after the candidate freeze and acquired/sealed without strategy evaluation;
6. predeclare the validation decision rule before any new candidate outcomes are opened.

No candidate freeze has been enacted by this assessment. Explicit human approval is required.
