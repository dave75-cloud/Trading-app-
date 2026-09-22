# M006f Human Disposition and Cumulative Shadow-Session Ledger

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic disposition: PROHIBITED
Automatic promotion: NONE

## Purpose

This layer sits after the M006f shadow-session review dossier.

Its purposes are:

1. record an explicit human disposition for one exact dossier; and
2. aggregate only cryptographically matched, human-reviewed sessions into a
   cumulative shadow-session ledger.

The software must never infer, recommend, default or silently create the human
disposition.

## Human disposition record

A disposition record is bound to:

- the exact dossier file bytes;
- the dossier-content SHA-256;
- the session ID;
- the session date.

Permitted dispositions are:

- ACCEPTED;
- ACCEPTED_WITH_REVIEW;
- REJECTED.

These describe the human review of a shadow session only.

They do not authorize promotion, execution or capital use.

## Required human inputs

The recorder requires the human to explicitly provide:

- disposition;
- reviewer label;
- review timestamp in UTC.

Notes are optional.

There is no default disposition.

## Integrity

Before recording a disposition, the tool independently verifies the dossier
content hash.

The output records both:

- dossier-content SHA-256;
- exact dossier-file SHA-256.

The disposition record itself also receives a deterministic content SHA-256.

## Cumulative ledger

The cumulative ledger accepts dossier/disposition pairs only when:

- the dossier independently verifies;
- the disposition record independently verifies;
- session identity matches;
- session date matches;
- dossier-content SHA-256 matches;
- dossier-file SHA-256 matches.

A dossier without a valid human disposition is not part of the reviewed cohort.

## Ledger facts

The ledger may aggregate:

- reviewed sessions;
- accepted sessions;
- accepted-with-review sessions;
- rejected sessions;
- replay events;
- market-evidence records;
- suppressed chains;
- review flags;
- sessions ending with open positions;
- realized shadow P&L observations;
- final shadow equity observations.

The ledger reports evidence only.

## No promotion semantics

The ledger must not output:

- PROMOTE;
- GRADUATE;
- LIVE;
- ENABLE;
- READY FOR CAPITAL;

or any equivalent machine decision.

It may report evidence counts and integrity state.

Human promotion authority remains outside this component.

## Safety

This layer:

- has no network capability;
- has no submission capability;
- has no market-data acquisition capability;
- does not alter strategy, risk or sizing;
- does not modify M006e;
- does not modify canonical M005;
- does not create promotion authority.

## Append-only intent

Disposition records are intended to be immutable evidence.

A tool must refuse to overwrite an existing disposition output.

Changing a human decision requires a separately governed superseding record,
not silent mutation of the original.
