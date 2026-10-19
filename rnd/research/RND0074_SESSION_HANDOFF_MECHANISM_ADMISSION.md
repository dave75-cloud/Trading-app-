# RND-0074 — Session-Handoff Mechanism Admission

Status: DESIGN ONLY — no market outcomes.

## Economic mechanism
A geographic session handoff may involve dealer inventory transfer, hedging and information updating, affecting intraday liquidity, spreads and price discovery. This does not imply a directional trading edge.

## Competing explanations
- Ordinary time-of-day seasonality rather than handoff-specific effects.
- Scheduled macro news clustering.
- Time zone / DST / holiday misclassification.
- Higher transaction costs absorbing any gross effect.
- Feed, liquidity proxy or execution artefacts.

## Predeclarations required before any empirical test
1. Reproducible Tokyo, London and New York session definitions from independent sources with timezone/DST and holiday treatment.
2. Select an estimand in advance: non-directional microstructure effect first; directional predictability requires separate admission.
3. Require timestamped bid/ask or independent liquidity/order-flow proxy; OHLC bars do not prove dealer inventory transfer.
4. Freeze instruments, event windows, controls, effect-size thresholds, negative-control windows and explicit multiplicity budget.
5. Verify feed/source identity, known-at timestamp, legal reuse and data acquisition cost.
6. Specify rejection conditions, execution frictions and no post-hoc rescue.
7. Prohibit use of protected 2021–22 validation, reserved 2023–24 final and sealed Q003/RND0060 prospective outcome data.

## Permitted zero-cost next work
Create synthetic offline session-boundary and DST fixtures, research independently grounded timezone/calendar conventions, and assemble a data-provenance and cost matrix. Then perform an RND-0062 admission review before accessing any FX outcomes.

## Authority
No broker write, trading, capital, live execution, promotion, automatic merge, provider purchase or protected artifact modification. No Trading Economics subscription. This is an independent RND-0061 research agenda path, not a substitute for missing macro consensus evidence.
