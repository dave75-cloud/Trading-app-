# RND-0065 — Trading Economics Outcome-Blind Acquisition Runbook

## Status
FROZEN OPERATIONAL RUNBOOK — REQUIRES HUMAN-PROVIDED PROVIDER CREDENTIAL / NO FX OUTCOME ACCESS

## Purpose
Define the exact credential-safe procedure for the first Trading Economics point-in-time macro-event pilot acquisition after RND-0065 provider machinery verification.

This runbook does not obtain, activate, purchase, or store a Trading Economics subscription or API credential. It assumes the human user has independently obtained an API key under terms they accept.

## Provider documentation basis
Trading Economics currently documents API authentication through an API key obtained from its developer portal. The key may be sent through an HTTP Authorization header. The provider also documents a point-in-time economic calendar endpoint intended to preserve values as they appeared historically before subsequent revisions.

## Security rules
1. Never paste the API key into ChatGPT, GitHub, commit messages, evidence files, shell history, or repository files.
2. Never place the key in a query string for the governed pilot.
3. Supply the key only through a temporary shell environment variable and send it through the HTTP Authorization header.
4. The acquisition adapter must redact credentials from logs, receipts, exceptions, and request metadata.
5. If a credential appears in stdout/stderr or a persisted artifact, stop and classify the acquisition as structurally invalid until the credential exposure has been remediated.

## Human credential step
The human user must independently obtain a Trading Economics API key from the provider developer portal.

After obtaining it, use a shell prompt that does not echo the value:

```bash
read -s -p "Trading Economics API key: " TE_API_KEY
echo
export TE_API_KEY
```

Do not paste the key into this chat.

## Frozen pilot scope
Use only the exact RND-0065 pilot scope already frozen in the branch. No date, country, indicator, event-family, or provider-field expansion is permitted based on returned values.

The pilot remains structural and outcome-blind:
- macro-event fields only;
- no FX market response;
- no strategy signal;
- no trade simulation;
- no P&L/equity/drawdown;
- no Q003 outcome access;
- no RND-0060Q/R economic outcome access;
- no 2021–2022 validation access;
- no 2023–2024 reserved-final access.

## Acquisition execution
The governed acquisition script must:
1. fail closed if `TE_API_KEY` is absent;
2. authenticate using the Authorization header;
3. request only the frozen pilot scope;
4. preserve the raw response bytes before normalization;
5. record request URL without credential material;
6. record retrieval timestamp, HTTP status, provider identity, response hash, and parser version;
7. normalize through the verified RND-0064 provenance guard;
8. reject prohibited outcome fields, ambiguous timestamps, missing provenance, protected partitions, duplicates, and revision-lineage violations;
9. write evidence only to the governed evidence location defined by the acquisition script;
10. produce a source-pilot classification using the frozen RND-0064 thresholds only.

## Allowed pilot classifications
- `SOURCE_ADMISSIBLE_FOR_STRUCTURAL_NORMALIZATION`
- `SOURCE_ADMISSIBLE_WITH_DOCUMENTED_LIMITATIONS`
- `SOURCE_EVALUATION_INCONCLUSIVE`
- `SOURCE_NOT_ADMISSIBLE_FOR_POINT_IN_TIME_RESEARCH`

No pilot classification is a strategy result.

## Post-acquisition rule
If the provider pilot is structurally admissible, RND-0063 may be revisited for admission review using the newly governed macro-event source.

The macro-event acquisition itself must not be joined to FX returns until RND-0063 has separately passed the RND-0062 admission gate and a new explicit human-approved development task has been opened.

## Authority firewall
Throughout this runbook:
- `promotion_authority=FALSE`
- `broker_write_authority=FALSE`
- `capital_authority=FALSE`
- `live_execution_authority=FALSE`
- `automatic_merge=FALSE`
- `reserved_final_open=FALSE`
