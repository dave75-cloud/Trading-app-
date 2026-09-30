# M006f prospective market-evidence contract

## Result

PASS.

A strict prospective evidence contract was defined for M006f shadow replay.

Required evidence includes exact bid/ask, UTC timestamps, event identity,
event leg, pair, explicit AUD conversion factor, provider provenance and
source-artifact SHA-256.

The contract prohibits reconstruction of bid/ask from midpoint, bar close,
assumed spread, later prices or another provider.

## Full-chain proof

A synthetic accepted USDJPY round trip passed through:

market-evidence contract -> accepted-event replay adapter -> M006f simulator.

Result:

- accepted sessions: 1
- source events: 2
- replay events: 2
- suppressed chains: 0
- realized shadow P&L: AUD 96.156074
- final equity: AUD 100096.156074
- final positions: flat
- network capability: false
- submission capability: false

## Governance

This experiment is R&D-only.

No frozen M006e component was modified.
Canonical M005 was not modified.
No execution or capital authority was created.
Automatic promotion remains false.
Human review remains required.

## Automated regression

The completed implementation passed:

- 7 market-evidence contract tests;
- 5 accepted-event replay adapter tests;
- 7 M006f shadow simulator tests.

Total: 19/19 tests passed.

The full contract -> adapter -> simulator regression reproduces the synthetic
USDJPY result of AUD 96.156074 realized P&L and finishes flat.

The initial regression fixture used a different quote-to-AUD conversion factor
than the manual integration fixture. The fixture was aligned to the recorded
0.00965 synthetic factor; no adapter, contract, or simulator logic change was
required.
