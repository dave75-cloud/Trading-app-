# M006f Offline Prospective Shadow-Session Pipeline

Status: R&D CANDIDATE / OFFLINE ONLY

`prospective_shadow_session_pipeline.py` composes the existing evidence contract,
accepted-event adapter, shadow simulator, immutable packager, and review-dossier
builder. It does not replace any of those components.

## One-way boundary

The pipeline accepts explicit paths to one accepted session record, its referenced
reconciliation, an optional human disposition needed by a non-clean source session,
and exact market evidence. It validates every source before publishing output, then
performs this one-way sequence:

1. exact market-evidence contract validation;
2. accepted-source integrity and safety validation;
3. accepted-event replay and replay-audit creation;
4. deterministic offline simulation;
5. immutable shadow-session package creation;
6. JSON and Markdown review-dossier creation;
7. stop for human review.

All work occurs in a temporary sibling directory. Any failure removes that directory,
and only a fully completed session is atomically renamed to the requested output path.
An existing output path is always rejected.

## Deterministic output

The output directory contains:

- `replay_audit.json`
- `replay_events.jsonl`
- `shadow_result.json`
- `shadow_session_package.json`
- `review_dossier.json`
- `review_dossier.md`
- `pipeline_manifest.json`

The manifest records SHA-256 digests of every explicit source and generated artifact.
Given byte-identical inputs and the same numerical simulation arguments, artifact
bytes and hashes are deterministic.

## Safety and authority

The pipeline has no network, broker-transport, credential, order-construction,
submission, execution, automatic-disposition, promotion, or capital authority.
It leaves `human_disposition` unset, records `automatic_promotion = false`, and records
`promotion_authority = NONE`. It neither invokes nor updates the human-reviewed
session ledger or cumulative observation monitor.

## Invocation

```text
python3 rnd/m006f/prospective_shadow_session_pipeline.py \
  --session-id SESSION_ID \
  --session-date-utc YYYY-MM-DD \
  --accepted-session /local/session.json \
  --reconciliation /local/reconciliation.json \
  --market-evidence /local/exact_market_evidence.jsonl \
  --output-dir /local/new-session-output
```

For an accepted non-clean source session, also pass its already-existing explicit
human disposition using `--disposition`. Inputs are read-only and are never changed.
