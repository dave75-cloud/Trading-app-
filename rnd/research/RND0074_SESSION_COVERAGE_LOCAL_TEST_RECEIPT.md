# RND-0074 — Session coverage synthetic local test receipt

**Operator-reported result, 2026-10-28 (Australia/Brisbane), no actual development archive accessed in this test.**

The operator fetched the research branch, checked out detached commit `01088f9ac3eba6b11b9041549e3520bd065bc36f` in `~/Projects/Trading-rnd`, then ran:

```sh
cd rnd/tools
python3 -m unittest -v test_rnd0074_session_coverage_audit.py
```

Six tests reported **ok**, overall `Ran 6 tests in 1.174s — OK`:
- test_missing_eligible_timestamp_reduces_coverage
- test_only_2019_accepted
- test_reconciles_and_no_synthetic_prices
- test_six_predeclared_windows
- test_unapproved_instrument_rejected
- test_unexpected_timestamp_is_counted_separately

**Limits:** unit tests use synthetic/mocked metadata and do not verify the live archive or full source semantics. This receipt does not authorize price inspection, performance research, calendar promotion, evidence sealing, trading, broker writes, protected-period access, or paid subscriptions. Original evidence remains quarantined.

**Next controlled step:** run the unchanged auditor read-only on EURUSD/2019 in the development-only RND-0033 archive, inspect six aggregate coverage rows, and review caveats before expanding to other pairs.
