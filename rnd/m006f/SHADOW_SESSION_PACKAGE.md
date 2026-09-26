# M006f Immutable Shadow-Session Package

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic promotion: NONE
Human review: REQUIRED

## Purpose

A shadow-session package binds the evidence and outputs for one prospective
M006f shadow session into a single deterministic, reviewable manifest.

The packager consumes local R&D artifacts only.

It does not:

- acquire market data;
- generate trading signals;
- alter accepted events;
- alter M006e or canonical M005;
- provide network capability;
- provide submission capability;
- authorize promotion or capital use.

## Required components

Each package contains references and SHA-256 hashes for:

1. accepted-session evidence;
2. sealed market evidence;
3. accepted-event replay audit;
4. M006f replay events;
5. M006f shadow-simulator result.

The original component files remain authoritative evidence. The package
manifest binds their exact bytes together.

## Manifest

The manifest records:

- package version;
- session ID;
- UTC session date;
- component path labels;
- component sizes;
- component SHA-256 hashes;
- market-evidence record count;
- replay-event count;
- replay-audit record count;
- suppressed-chain count;
- final shadow positions;
- realized shadow P&L;
- final shadow equity;
- explicit safety capability flags;
- aggregate package-content SHA-256.

## Integrity rules

Packaging fails closed if:

- any required component is missing;
- an input path is not a regular file;
- replay acceptance gate is not true;
- replay output count differs from the replay audit;
- simulator event count differs from replay output count;
- replay audit reports network capability;
- simulator reports network capability;
- simulator reports submission capability;
- replay audit reports automatic promotion;
- replay audit does not require human review.

The packager does not silently repair inconsistent evidence.

## Aggregate hash

The package-content SHA-256 is computed over a canonical JSON representation
of the complete manifest payload before the aggregate hash field is added.

This hash identifies the package contents and component hashes. It is not
defined as the SHA-256 of the final manifest file itself.

## Immutability

The packager refuses to overwrite an existing output file.

A changed source artifact therefore requires a newly generated package
manifest with a new aggregate package-content hash.

## Governance

This design is prospective and R&D-only.

Any operational integration requires a separate human decision after the
current frozen observation phase.

No automatic promotion is permitted.
