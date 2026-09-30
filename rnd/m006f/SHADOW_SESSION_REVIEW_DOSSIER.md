# M006f Shadow-Session Human Review Dossier

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic promotion: NONE
Human disposition: REQUIRED

## Purpose

The review dossier is the human-facing layer above an immutable M006f
shadow-session package.

It consumes one completed shadow-session package manifest and produces a
concise review artifact containing:

1. verified machine facts;
2. non-decisional review flags;
3. an explicitly unset human disposition.

The dossier never promotes, accepts, rejects or remediates a session.

## Source authority

The immutable shadow-session package remains the source of machine evidence.

Before producing a dossier, the generator independently recomputes the
package-content SHA-256. A hash mismatch fails closed.

The dossier also records the SHA-256 of the exact package-manifest file bytes.

## Machine facts

The dossier reports:

- session ID;
- UTC session date;
- source package-content SHA-256;
- source manifest-file SHA-256;
- market-evidence record count;
- replay-event count;
- replay-audit record count;
- suppressed-chain count;
- final shadow positions;
- realized shadow P&L;
- final shadow equity;
- network capability;
- submission capability;
- automatic-promotion capability;
- human-review requirement.

These are descriptive facts, not a disposition.

## Review flags

The generator may raise review flags for facts requiring human attention.

Initial flags are:

- ZERO_REPLAY_EVENTS;
- SUPPRESSED_CHAINS_PRESENT;
- OPEN_POSITIONS_AT_SESSION_END;
- MARKET_EVIDENCE_SHORTFALL.

A review flag is not an automatic failure or rejection.

Negative or positive P&L is not itself treated as an integrity anomaly.

## Fail-closed conditions

Dossier generation fails if:

- the source package is malformed;
- the package-content SHA-256 does not verify;
- required safety capability fields are inconsistent;
- required counts are missing or invalid;
- final positions are malformed;
- P&L or equity is non-finite.

The dossier does not repair source evidence.

## Human disposition

The generated dossier always contains:

- human_disposition: null;
- human_notes: null;
- automatic_promotion: false;
- promotion_authority: NONE.

A later human-review workflow may record a disposition separately.

The dossier generator itself cannot fill it in.

## Determinism

The machine dossier contains no runtime timestamp.

For identical source-package bytes it produces identical JSON content and an
identical dossier-content SHA-256.

## Governance

This component is local, offline and R&D-only.

It does not modify M006e or canonical M005.
It does not acquire market data.
It does not generate trading decisions.
It does not provide network or submission capability.
It does not alter strategy, risk, sizing, promotion or capital authority.
