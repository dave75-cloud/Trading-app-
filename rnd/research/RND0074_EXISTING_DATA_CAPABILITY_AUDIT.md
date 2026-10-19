# RND-0074 — Existing Data Capability Audit (Metadata Only)

Status: REPOSITORY DOCUMENTATION REVIEWED; DATA/LICENCE VALIDATION PENDING; NO MARKET OUTCOMES OPENED.

## Documents consulted
- `rnd/research/OANDA_HISTORICAL_ACQUISITION_CONTRACT.md` (RND-0028)
- `rnd/research/RND0036_2020_DEVELOPMENT_ACQUISITION_CONTRACT.md`
- `rnd/research/HISTORICAL_DATA_ACQUISITION_PLAN.json` (older RND-0027 plan; its MISSING statuses are **historical**, not current proof of absence)
- `rnd/research/RND0062_RESEARCH_ADMISSION_MULTIPLE_HYPOTHESIS_STANDARD.md`
- RND-0061 research agenda; RND-0074 admission and synthetic clock protocol

## Verified documentary capabilities, not yet direct dataset verification
The governed OANDA practice acquisition architecture specifies GET-only M5 complete bid/ask/mid candles; raw response hashing, canonical identities, strict UTC ordering, gap accounting and protected partitioning. RND-0036 predeclares four-pair development acquisition through the exact 2020 boundary. This documents a plausible **quote-based spread/quote-quality research input** already within the project's existing data architecture.

It does NOT establish:
- live, executable quote depth or bid/ask order-book dynamics;
- broker inventory, dealer order flow, market-wide volume or direct handoff evidence;
- independent consolidated market quotes;
- that every required 2015–2020 snapshot is currently present in the user's local evidence store;
- an unrestricted licence to republish provider data;
- the freshness, missing-data profile or economic quality of the actual snapshot without inspecting evidence.

The older RND-0027 plan's MISSING flags must not override later RND-0031–0036 work. Avoid re-acquisition or provider expenditure until existing evidence seals and manifests have been checked **using metadata only**.

## No-cost next checks, in order
1. Inspect existing non-economic snapshot manifests, per-pair hashes, acquisition date ranges, origin and gap ledgers only. Never print candle values, computed spreads or outcomes during the audit.
2. Review original quote-feed licence and whether offline research reuse is permitted; record `UNKNOWN` instead of assuming approval.
3. Determine whether the 2015–2020 quote dataset supports *descriptive bid–ask spread seasonality*, which is weaker than inventory-transfer causality.
4. Only after RND-0062 review and explicit separate freeze, define one estimand and event/control window using the precommitted RND-0074 session conventions.
5. If market-wide inventory/order-flow measurement remains unavailable, retain `CAUSAL_INVENTORY_TRANSFER_NOT_TESTABLE`. Do not relabel price patterns as inventory flow.
6. Reject attempts to search sessions, pairs, days or horizons for profitable opportunities. Directional entry/exit remains unadmitted.

## Cost conclusion
No acquisition purchase is needed for this metadata audit. Existing OANDA architecture may already suffice for a **limited** non-directional liquidity descriptive test, pending provenance and licence checks. Trading Economics is NOT a dependency of this session-handoff research; its deferred purpose is macro survey-consensus history only.

## Governance
Protected 2021–22 consumed validation and 2023–24 reserved final remain inaccessible. Q003 and RND-0060Q/R prospective economic outcomes sealed. No broker writes, provider purchase, automatic merge or live strategy authority. RND-0074's 24 local hostile tests remain PENDING until terminal evidence is supplied.
