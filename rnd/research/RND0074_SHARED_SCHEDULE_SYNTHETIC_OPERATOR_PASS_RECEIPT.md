# RND-0074 — Shared-schedule diagnostic synthetic verification receipt

Operator reported detached checkout at commit `8e3132e398dd7b266f11e669ef9143127d443613` and executed from `rnd/tools`:

`python3 -m unittest -v test_rnd0074_shared_schedule_diagnostic.py`

Results: `test_bad_root_rejected`, `test_cross_pair_membership`, `test_missing_schedule_digest_rejected`, `test_provenance_not_admitted`, and `test_strict_reconciliation_rejects` all `ok`. Final output: **Ran 5 tests in 0.342s; OK**.

Scope: Synthetic/mocked testing only, not verification of original 2019 source bytes or full RND-0030 provenance; no historical performance calculations. Earlier distinct six-test cross-pair suite also passed on its corrected commit. Next operation is operator-run read-only 2019 shared-reference diagnostic, with outputs reconciled to previously reported 75 missing AUDUSD NY-close +15/+20 observations across 68 local dates, 70 single-pair and 5 two-pair missing occurrences; these targets are not assumed to be observed.

All 2016–2019 source files remain `QUARANTINED_UNRESOLVED_DISCREPANCIES`; 12 original standard schedule files are missing. No evidence file restore, source seal, price parsing, protected year access, broker write, merge or provider spend is authorized.
