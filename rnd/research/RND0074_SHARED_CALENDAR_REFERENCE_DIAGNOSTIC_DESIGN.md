# RND-0074 — Shared 2019 schedule reference: controlled metadata diagnostic

**Status: implementation and synthetic tests committed, operator tests pending. No source-file restoration or economic admission.**

Operator verified that the existing `AUDUSD/2019/standard_schedule.json` is **1,947,585 bytes**, SHA-256 `d3bd447bc9d8757bc11f3fe57c9e872e1f661a0447eba541dd199a02aadaf66b`. All four existing 2019 manifests declare that same `standard_schedule_file_sha256` and `standard_schedule_sha256` `0468425260217156731d17f429ac3757c8a112573d0eae3171f13d016e7a5a72`. Original schedules are missing in EURUSD, GBPUSD, USDJPY in 2019; overall 12 of 16 schedules are absent across 2016-2019.

New *separate* diagnostic `rnd/tools/rnd0074_shared_schedule_diagnostic.py` reads the intact AUDUSD 2019 shared schedule and: (a) runs the unchanged strict metadata auditor on the AUDUSD reference; (b) checks every pair's declared file/content hashes against the surviving schedule and reference manifest; (c) validates each original 2019 manifest identity and quarantine status, checksums original non-schedule files as opaque bytes, and validates original ledgers against the shared schedule; (d) independently compares session-boundary offset counts and AUDUSD baseline against the unchanged strict auditor; (e) reports the *union* of distinct local affected dates across NY CLOSE +15 and +20 offsets and membership of those AUDUSD missing timestamps across all four original ledgers. It never writes to the evidence root or parses price rows.

Results explicitly label which schedules are missing, `original_source_restored=false`, `full_original_provenance_verified=false`, `admitted=false`, and no trading/expenditure authority. Source status remains `QUARANTINED_UNRESOLVED_DISCREPANCIES`, `seal_allowed=false`. Exact historical OANDA closures and original missing-file cause remain unresolved.

**Verification order:** operator-run new synthetic tests; fix any failures; only then run the bounded 2019 archive diagnostic. Reconciliation targets previously observed: AUDUSD NY CLOSE +15/+20 Jan1/Dec25-excluded 75 missing timestamp-offsets, 68 distinct local dates, 70 missing only from AUDUSD, five additionally missing in one other pair. Do not silently normalize any discrepancies to these targets.

**Caution:** shared-reference hashes establish the declared common schedule bytes, not independent historical calendar accuracy or the completeness of missing original source files. This is a DIAGNOSTIC workaround, not an evidence repair or admission upgrade.
