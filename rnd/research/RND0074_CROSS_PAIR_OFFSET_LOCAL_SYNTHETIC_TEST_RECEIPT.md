# RND-0074 — Cross-pair offset and affected-date synthetic test receipt

**Operator-reported results: SIX OF SIX PASS; historical archive NOT opened in this test.**

The operator fetched and checked out detached commit `0eab1f2e72b3b21193b7091612ebcd01801ba02b`, correcting the prior Tokyo-close synthetic fixture failure. From `rnd/tools`, they executed `python3 -m unittest -v test_rnd0074_cross_pair_offset_dates.py`.

Six tests reported `ok`: `test_affected_dates`, `test_bad_root_stops`, `test_exact_pair_membership`, `test_holiday_sensitivity_separate`, `test_reconciliation_mismatch_stops`, `test_symlink_pair_stops`. Final result: `Ran 6 tests in 0.413s; OK`.

**Verification limits:** Tests rely on mocked/synthetic ledger sets and are not a substitute for independent original-source provenance verification. In particular, `test_symlink_pair_stops` currently exercises invalid metadata schema under mocking rather than creating an actual symlink; do **not** construe that test name as proof of complete symlink-path traversal coverage. Actual source SHA/ledger checks occur in the implementation's `verified_sets` on archive execution, but the full RND-0030 raw-page/canonical semantic verifier has not been rerun. No real historical overlap outputs are claimed by this receipt.

Next gate: a controlled development-only 2019 run of the cross-pair report with a concise stdout-only display of AUDUSD NY CLOSE +15/+20 affected-date and membership results. Reconcile to previously operator-reported 75 missing pair-offsets, 68 affected dates combined, and 70/5 pair membership. **Caveat:** per-offset affected-date counts cannot be added to get a distinct-date union; calculate the union separately if needed. The existing report supplies per-offset dates but not their union.

Source remains `QUARANTINED_UNRESOLVED_DISCREPANCIES`, seal_allowed=false. No price parsing, strategy testing, calendar promotion, broker writes, protected-year access, code merges or provider spend authorised.
