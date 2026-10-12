# Trading Project Cost Ledger

**Created:** 2026-10-12 (Australia/Brisbane)

## Purpose

Track incremental external costs attributable to the Trading R&D project, with explicit separation between approved spend, incurred spend, and recurring exposure.

This ledger does **not** treat an existing general-purpose subscription (for example, an already-held ChatGPT plan) as an incremental Trading-project cost unless it is later designated as such.

## Control rules

1. No provider purchase or trial activation is authorized unless explicitly approved by the human owner.
2. Planned or candidate costs remain **NOT APPROVED / NOT INCURRED** until explicit approval is given.
3. Any recurring subscription exposure must be recorded separately from the one-off or trial cost.
4. Where a trial auto-renews, the auto-renew amount must be shown as an exposure even if cancellation is intended.
5. Currency is recorded in the provider's billing currency; AUD equivalents may be added at the time of payment if useful.

## Current ledger

| Date | Service / source | Purpose | Status | Approved | Incurred | Recurring exposure | Notes |
|---|---|---|---|---:|---:|---:|---|
| 2026-10-12 | FRED / ALFRED | Official macro values, vintages and revisions | ACTIVE / FREE | US$0 | US$0 | US$0 | RND-0067 live structural pilot completed successfully. |
| 2026-10-12 | U.S. Bureau of Labor Statistics | Historical official release timing | ACTIVE / FREE | US$0 | US$0 | US$0 | RND-0069 timing adapter verified; no paid timing source required for US CPI pilot. |
| 2026-10-12 | Trading Economics Standard API trial | Historical point-in-time survey consensus provenance pilot | CANDIDATE — NOT APPROVED | US$0 | US$0 | US$0 currently | If later approved, expected trial cost is US$49 for one week. Current documented post-trial Standard subscription exposure is US$199/month if not cancelled. Planned pilot cap: 10 API requests. |
| 2026-10-12 | FMP | Alternative consensus/calendar source | REJECTED FOR CURRENT PURPOSE | US$0 | US$0 | US$0 | Cheap/free access does not currently prove preserved historical pre-release point-in-time consensus. |
| 2026-10-12 | Finnhub | Alternative consensus/calendar source | NOT SELECTED | US$0 | US$0 | US$0 | Historical/provenance fit not presently sufficient for the frozen 2015–2020 requirement. |
| 2026-10-12 | EODHD | Alternative economic-events source | NOT SELECTED | US$0 | US$0 | US$0 | Documented history begins too late for the 2015–2020 development requirement. |

## Totals

- **Approved incremental spend to date:** US$0
- **Incurred incremental spend to date:** US$0
- **Authorized recurring project cost:** US$0/month
- **Unapproved candidate spend:** Trading Economics trial US$49 one-off, with US$199/month auto-renew exposure if later activated and not cancelled.

## Update convention

When a new cost decision is made, append a new row rather than silently overwriting the original decision history. If a candidate becomes approved, record the approval date and approved ceiling. If payment occurs, record the actual charge and, where useful, the AUD amount appearing on the user's statement.
