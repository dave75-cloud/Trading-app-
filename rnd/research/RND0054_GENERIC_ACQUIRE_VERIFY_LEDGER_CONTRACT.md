# RND-0054 — Generic Prospective Acquisition, Verification, and Ledger Advancement

## Purpose

Replace tranche-specific orchestration with one governed, outcome-blind weekly workflow that:

1. derives the next authorized prospective window from the verified cumulative ledger;
2. refuses to run before that window has fully elapsed;
3. acquires OANDA fxTrade PRACTICE M5 bid/ask/mid complete-candle evidence using GET only;
4. seals raw and canonical evidence immutably;
5. verifies exact candidate identity, symbol universe, timestamps, hashes, completeness, and gap ledger integrity;
6. advances the cumulative prospective ledger only after verification PASS.

No Q003 signal, trade, return, P&L, equity, drawdown, hit rate, pair ranking, threshold tuning, reserved-final access, broker write, capital authority, or automatic promotion is authorized.

## Frozen candidate

- candidate: Q003
- fingerprint: `25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`
- symbols: AUDUSD, EURUSD, GBPUSD, USDJPY
- timeframe: M5
- provider: OANDA
- environment: PRACTICE
- method: GET only
- price components: bid / ask / mid
- complete candles only

## Prospective boundaries

- start: `2026-10-05T07:25:00Z`
- frozen earliest readout: `2027-04-03T07:25:00Z`
- regular tranche cadence: seven calendar days
- final tranche may be clipped only to land exactly on the frozen readout boundary.

## Exact continuity rule

Acquisition-window continuity and provider/market gaps are distinct concepts.

For the cumulative tranche ledger:

- tranche 1 starts exactly at the prospective start;
- every later tranche must start exactly at the previous verified tranche end;
- overlap is prohibited;
- acquisition-window holes are prohibited;
- genuine missing provider candles remain permissible only when explicitly represented inside the tranche gap ledger;
- no synthetic interpolation or silent backfill is permitted.

Thus provider gaps may exist *inside* an acquired interval, but there may be no ungoverned time interval *between* acquired tranches.

## Generic workflow states

`PLANNED -> ACQUIRED_SEALED -> VERIFIED -> LEDGER_ADVANCED`

Any failure stops the workflow. Ledger advancement is prohibited unless verification has passed.

## Authority invariants

Every plan, receipt, verifier result, and ledger record must preserve:

- `strategy_evaluation = false`
- `reserved_final_access = false`
- `broker_writes = false`
- `capital_authority = false`
- `automatic_promotion = false`

Runtime credentials may be read only from the existing OANDA PRACTICE environment variables and must never be committed, logged, or written to evidence.

## Verification requirements

For each symbol, verification must check at minimum:

- provider OANDA;
- M5 timeframe;
- bid/ask/mid components;
- exact planned start and end;
- immutable snapshot;
- complete-candles-only declaration;
- canonical row timestamps strictly inside the planned interval;
- canonical rows complete;
- raw bundle SHA-256 matches manifest;
- canonical-row SHA-256 matches manifest;
- gap ledger is structured and reconciles expected/actual timestamps;
- unexpected timestamps absent;
- any missing timestamps explicitly listed;
- gap ledger completeness consistent with evidence.

A tranche with provider gaps may still be structurally accepted if those gaps are explicitly and correctly ledgered. It may not be silently treated as gap-free.

## Ledger advancement

The verified tranche record must contain exact start/end, fingerprint, symbol universe, raw/canonical hashes, integrity PASS, and all authority invariants.

Advancement must fail closed on:

- fingerprint drift;
- symbol drift;
- start not equal to previous verified end;
- end beyond the frozen readout boundary;
- duplicate evidence hashes;
- malformed or missing hashes;
- any authority escalation;
- verification not PASS.

The cumulative state becomes `READOUT_ELIGIBLE_PENDING_HUMAN_GATE` only after the cumulative verified end reaches the frozen boundary. This does not itself open Q003 outcomes.

## Safety

Research evidence infrastructure only. No broker writes, order endpoints, live environment, capital allocation, strategy promotion, or final-test opening. Human authority remains mandatory for any later validation readout or lifecycle transition.