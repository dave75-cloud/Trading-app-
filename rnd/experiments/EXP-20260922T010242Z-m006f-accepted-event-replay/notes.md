# M006f accepted-event replay adapter

## Result

PASS.

The copied accepted corpus contains:

- 3 formally accepted forward-observation sessions;
- 17 authoritative M006e events;
- 18 logical event legs after reversal decomposition;
- 1 bridge-approved complete shadow chain: USDJPY on 17 September 2026.

The adapter independently verifies session acceptance, reconciliation counts,
M006e.2 integrity, zero-write evidence, and human disposition for non-CLEAN
sessions.

Exact historical bid/ask evidence was not persisted in the accepted
reconciliation evidence. The adapter therefore emitted zero M006f simulator
events rather than synthesizing fills.

This is intentional fail-closed behaviour.

## Tests

Five offline tests passed:

- fully evidenced round trip replays;
- missing market evidence suppresses the complete chain;
- ALERT without accepted disposition fails closed;
- nonzero write evidence fails closed;
- authoritative event-count mismatch fails closed.

## Authority

Automatic promotion: false.

Human review remains required.

No frozen M006e component or canonical M005 evidence was modified.
