# RND-0074 — Session-offset coverage local synthetic test receipt

**Operator-reported local result: 10/10 PASS; actual archive not opened in this test.**

The operator fetched the research branch and checked out detached commit `5ba19cc1e6a6d809008e7bd27d35974ccf1ec9ae` in `~/Projects/Trading-rnd`, then ran from `rnd/tools`:

`python3 -m unittest -v test_rnd0074_session_offset_coverage.py`

Result: **Ran 10 tests in 5.091s; OK**. Passing tests: `test_bad_timestamp_lists`, `test_denominator_failure`, `test_expected_missing`, `test_hash_gate_fail`, `test_london_dst`, `test_primary_vs_sensitivity`, `test_six_boundaries`, `test_twelve_offsets`, `test_unexpected_separate`, `test_year_and_pair_fail`.

This is a synthetic/mocked test run, not a full archive or canonical-price verification. The complete RND-0030 verifier has not been rerun. Source shards remain `QUARANTINED_UNRESOLVED_DISCREPANCIES`, seal_allowed=false. No historical data admission, price/strategy analysis, protected-period opening, trading authority, calendar promotion or new provider expense follows.

**Next controlled check:** run the committed auditor read-only on development EURUSD/2019, displaying only reconciled six-window summaries rather than the complete verbose JSON. Review before other pairs.
