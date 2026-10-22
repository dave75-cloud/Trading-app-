# RND-0074 — EURUSD 2019 local structural metadata audit receipt

Status: OPERATOR-REPORTED PASS FOR LIMITED METADATA AND FILE-HASH CHECKS. **SOURCE REMAINS QUARANTINED.**

On 2026-10-22, the operator ran `rnd/tools/rnd0074_development_metadata_audit.py` from the detached tested GitHub commit `df2c63816ea722d86ed9a8c4ed1d59b265228b8d`, with `--root ~/Trading-evidence/rnd0033-development-history-2016-2019 --pair EURUSD --year 2019`.

Reported stdout:

```text
RND0074_METADATA_AUDIT: STRUCTURAL_METADATA_CHECK_PASS
pair=EURUSD
year=2019
rows=73983
missing=1182
unexpected=258
unexpected_at_1700_ny=258
unexpected_elsewhere=0
short_bars=508
intermediate_bars=47
closure_shaped_bars=627
short_runs=442
intermediate_runs=9
closure_shaped_runs=5
missing_near_rollover=467
hashes_checked=True
admitted=False
source_quarantine_unchanged=TRUE
strategy_evaluation=FALSE
calendar_promotion=FALSE
```

Accounting: 508+47+627=1182 missing M5 intervals; 442+9+5=456 gap runs. All 258 unexpected timestamps map to 17:00 America/New_York.

**Scope of verification:** the bounded RND-0074 audit read manifest, standard schedule and discrepancy timestamp lists; checked hashes of five recorded files including canonical rows *as raw bytes only*. It checked record identity and gap-set/count invariants. **It did not** reparse canonical price rows, validate raw page evidence or recompute canonical content digests; it is not a full RND-0030 `verify_existing_shard` pass. No market price, strategy outcome or broker access. Gap classes are run-length patterns, not authenticated historical market closures. All outstanding documentary and evidence admission requirements remain.

Next: cautiously expand same read-only metadata auditor to other 2019 pair-year shards, then earlier development-only years. Human review of any admission remains necessary. No new provider spending, broker writes, source modifications, calendar promotion, or resealing.
