# RND-0060D Postmortem — Three-Bar Directional Persistence

## Status

**CLOSED — DEVELOPMENT_FALSIFIED**

RND-0060D tested a single predeclared short-horizon directional-persistence mechanism over admitted DEVELOPMENT_2015_2020 evidence only.

Frozen mechanism:
- three consecutive contiguous non-zero M5 mid-close returns of the same sign;
- same-direction entry on the next contiguous eligible M5 bar;
- entry remained inside the frozen symbol session;
- exactly three subsequent genuine observed bars held;
- maximum one trade per symbol/day;
- RND-0034 gap semantics;
- no parameter search, inverse variant, magnitude threshold, pair selection, session alteration, weighting, or validation access.

## Structural integrity

- verified_2015_2019: 20/20
- verified_2020: 4/4
- pair_years: 24/24
- trial_count: 1
- parameter_search: FALSE
- integrity reconciliation: PASS
- validation_open: FALSE
- final_test_open: FALSE
- reserved_final_access: FALSE
- broker_writes: FALSE
- capital_authority: FALSE

Development report:
`/Users/davidkerr/Trading-evidence/rnd0060d-three-bar-directional-persistence-full-development-2015-2020-20261005.json`

Report SHA-256:
`8cbfdf7d021c73937a365fa5d314532c1b1c05ea2ce9017e060676e4371b4cf9`

## Frozen falsification result

Classification: **DEVELOPMENT_FALSIFIED**

Criteria:
- at_least_3_of_4_pair_terminal_equities_gte_1: FALSE
- at_least_4_of_6_positive_development_years: FALSE
- every_leave_one_pair_out_realized_net_sum_gt_0: FALSE
- integrity_reconciliation_pass: TRUE
- portfolio_max_drawdown_gte_minus_0_10: FALSE
- portfolio_realized_net_sum_gt_0: FALSE
- portfolio_terminal_net_equity_gt_1: FALSE

Portfolio:
- final equal-unit normalized equity: 0.848931428433964
- realized completed-trade net return sum: -0.6042742862641439
- equal-unit normalized max drawdown: -0.15122976253412423

Per symbol:
- AUDUSD: 1546 trades; terminal net equity 0.7718313338864656; realized net sum -0.25861962258732885; max DD -0.23139179327142412; execution cost drag 0.20272929127191078
- EURUSD: 1510 trades; terminal net equity 0.8963847587045174; realized net sum -0.10911972800888015; max DD -0.11066560055981678; execution cost drag 0.09740869007321859
- GBPUSD: 1523 trades; terminal net equity 0.8951321181225476; realized net sum -0.11038199221969863; max DD -0.10800220758435886; execution cost drag 0.17100416079650219
- USDJPY: 1506 trades; terminal net equity 0.8813159321590439; realized net sum -0.12615294344823652; max DD -0.11928748383074073; execution cost drag 0.10933968782351314

Annual aggregate realized net:
- 2015: -0.14062973416774305
- 2016: -0.0953894979868726
- 2017: -0.0905601441615554
- 2018: -0.10673598513941336
- 2019: -0.10298360383261423
- 2020: -0.0679753209759453

Leave-one-pair-out realized net sums:
- exclude AUDUSD: -0.3456546636768153
- exclude EURUSD: -0.495154558255264
- exclude GBPUSD: -0.4938922940444455
- exclude USDJPY: -0.4781213428159076

## Interpretation

This is a decisive mechanism-level failure, not a near miss and not a concentration accident. All four pair buckets lost; all six development years lost; every leave-one-pair-out portfolio remained materially negative; and integrity passed. Unlike RND-0060A through RND-0060C, even the portfolio drawdown criterion failed.

The very high trade count means transaction friction compounded heavily, but the result is not to be reframed as merely a cost problem. The predeclared persistence mechanism did not produce transferable positive net expectancy under its fixed rules.

## Prohibited rescue work

RND-0060D is closed. Do not use its result to justify:
- testing 2-bar, 4-bar, or other streak lengths;
- reversing the direction after a failed persistence result;
- adding magnitude, volatility, spread, or time-of-day filters;
- dropping or weighting pairs;
- changing the three-bar hold;
- cherry-picking years or sessions;
- consuming validation or reserved-final evidence.

Any future research must begin as a separately predeclared, genuinely independent hypothesis family under the RND-0060 firewall.
