# RND-0047 — Fresh Prospective Evidence Tranche 001 Verified Receipt

Status: **VERIFIED / SEALED / NO STRATEGY EVALUATION**

## Candidate binding

- candidate: `Q003`
- candidate fingerprint: `25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4`

## Prospective evidence window

- start inclusive: `2026-10-05T07:25:00Z`
- end exclusive: `2026-10-05T07:35:00Z`
- timeframe: `M5`
- symbols: `AUDUSD`, `EURUSD`, `GBPUSD`, `USDJPY`
- rows per symbol: `2`
- provider: `OANDA PRACTICE`
- price components: bid / ask / mid
- complete candles only: `TRUE`

Provider timestamps for every symbol were the same two M5 instants, represented by OANDA with nanosecond precision:

- `2026-10-05T07:25:00.000000000Z`
- `2026-10-05T07:30:00.000000000Z`

## Immutable evidence hashes

### AUDUSD

- raw bundle SHA-256: `4a77cdfefdd493121afc6f4e61acafc617b9db6535a3ebd8c3213a9e28caaae3`
- canonical rows SHA-256: `ae39b15c6cd1b60f89a01fc7b22ee1b88b899b8fb6a406cfd2a158d0721cad94`

### EURUSD

- raw bundle SHA-256: `07851f5e397bacf9739fda52d38ebd6b31975eb9b3864177d30715e961220ce3`
- canonical rows SHA-256: `8f32b572aef3da5144816f0219322be505a3e22afb37d15eeca6b90f3915ba71`

### GBPUSD

- raw bundle SHA-256: `e7b4192d49da89516327334c643ed8de0ff337c3e6fa9feb3516819faab3e4f3`
- canonical rows SHA-256: `b02ab718af87681845c10c5eb8ecacb2099793c04ec67babd523aafea27d3a7b`

### USDJPY

- raw bundle SHA-256: `59fb0cd1996a165f9eeefca792ab479c85f2a892d8810fe982d8f1bbe522e3e0`
- canonical rows SHA-256: `10547d609b3be441d478c5a4f963ba716230e84c1775e796b9665549a092dfd7`

## Verification result

`RND0047_FRESH_TRANCHE_VERIFY: PASS`

The verifier confirmed:

- candidate fingerprint matched exactly;
- tranche window matched exactly;
- all four symbols were present;
- exactly two complete M5 rows existed for each symbol;
- normalized provider timestamps matched the two expected M5 instants;
- raw-bundle SHA-256 matched each snapshot manifest;
- canonical-row SHA-256 matched each snapshot manifest;
- structured gap ledgers were complete with no missing or unexpected timestamps;
- acquisition evidence remained immutable.

## Authority and exclusions

- strategy evaluation: **FALSE**
- signal generation: **FALSE**
- trade simulation: **FALSE**
- validation decision: **FALSE**
- parameter selection: **FALSE**
- pair dropping: **FALSE**
- pair weighting: **FALSE**
- reserved-final access: **FALSE**
- broker writes: **FALSE**
- capital authority: **FALSE**
- automatic promotion: **FALSE**

This receipt makes Tranche 001 part of the prospective post-freeze evidence stream. It does not authorize evaluation of Q003 on the tranche or any other prospective evidence.
