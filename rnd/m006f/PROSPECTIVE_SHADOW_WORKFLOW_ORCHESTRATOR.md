# M006f Bounded Prospective Shadow-Workflow Orchestrator

Status: R&D CANDIDATE / OFFLINE ONLY
Task: RND-0019
Automatic disposition: NONE
Automatic promotion: NONE
Human review: REQUIRED

## Purpose

This component moves M006f from single-task invocation toward bounded workflow
autonomy. It discovers already-existing local evidence for one eligible accepted
session, invokes the existing RND-0018 prospective shadow-session pipeline, and
stops when the human-review dossier has been published.

It does not replace the RND-0018 pipeline.

## One-way workflow

accepted-session root
    |
    v
deterministic local discovery
    |
    v
eligibility / ambiguity gate
    |
    v
existing RND-0018 offline pipeline
    |
    v
shadow package + review dossier
    |
    v
HUMAN REVIEW

## Explicit local roots

The CLI requires explicit directories for:

- accepted M006e.9 session records;
- reconciliation records;
- human dispositions;
- exact market-evidence sidecars;
- new shadow-session outputs.

The tool contains no acquisition path for missing evidence.

Accepted-session discovery uses the existing formal filename pattern:
`m006e9a_*.json`.

Exact market evidence uses one deterministic filename:
`market_evidence_<YYYY-MM-DD>.jsonl`.

Published shadow output uses:
`shadow_session_<YYYY-MM-DD>/`.

## Selection rule

Without `--session-date-utc`, exactly one unprocessed eligible session must
exist.

- zero eligible sessions -> NO_ELIGIBLE_SESSION;
- more than one eligible session -> FAIL_CLOSED as ambiguous;
- exactly one eligible session -> invoke RND-0018.

With `--session-date-utc`, only that authoritative session day can be selected.

The orchestrator never ranks, scores, guesses, or chooses among multiple
eligible sessions.

## Eligibility

A session is eligible only when:

- the accepted-session record has an authoritative day;
- its declared reconciliation file exists;
- reconciliation day equals accepted-session day;
- the exact date-named market-evidence sidecar exists;
- if the source verdict is non-CLEAN, a date-matched already-existing accepted
  human disposition exists;
- the deterministic output path does not already exist.

Detailed integrity, safety, event-count and replay validation remains the
responsibility of the existing RND-0018 pipeline and replay adapter.

## Zero-event sessions

The existing market-evidence contract permits an empty JSONL sidecar. Therefore
an accepted zero-event session can remain eligible without inventing price
evidence, provided its exact date-named sidecar exists and all other gates pass.

## Fail-closed boundary

The workflow does not:

- fetch or reconstruct missing market evidence;
- create a human disposition;
- update the human-reviewed shadow ledger;
- update the cumulative shadow-observation monitor;
- modify source observation evidence;
- modify M006e or canonical M005;
- acquire credentials;
- create external connectivity;
- submit anything to a broker;
- promote a candidate;
- authorize capital.

Existing output paths are never overwritten.

## Authority

The returned workflow result records:

- network capability: false;
- submission capability: false;
- automatic disposition: false;
- automatic promotion: false;
- promotion authority: NONE;
- human review required: true.

## Validation status

RND-0019 remains RUNNING until its focused tests, the full M006f regression
suite, the R&D workspace audit, and diff checks have been independently run on
the exact branch head.
