# RND-0074 — Offline Session-Clock Rehearsal Protocol

## Status
IMPLEMENTED / LOCAL HOSTILE TESTS PENDING

## Economic hypothesis
See RND0074_SESSION_HANDOFF_MECHANISM_ADMISSION.md. Handoff inventory transfer is a hypothesis, not an observed fact. Session clock coincidences are not proof of microstructure causality or profitability.

## Freeze
- Clock test year: 2019 only, development partition.
- Clock conventions (illustrative, not official opening hours): Tokyo Asia/Tokyo 09:00–17:00; London Europe/London 08:00–16:00; New York America/New_York 08:00–16:00.
- Each convention is local wall-clock time, converted by IANA timezone rules to UTC.
- Weekends rejected; weekday public holidays are **not** certified and do not imply a trading day.
- No clock overrides, no ambiguous/nonexistent DST wall-clock time, no input market outcome fields.
- The test set includes UK/US daylight-saving divergence in March, Tokyo/London overlap changes, and negative-overlap cases.
- All claims in output explicitly mark market data, dealer handoffs, holiday-calendar validation, and predictive edge as NOT VERIFIED.

## Required external-data admission matrix (not yet satisfied)
| Layer | Required evidence | Existing/possible source | Status | Cost |
| --- | --- | --- | --- | --- |
| Time zone conversion | IANA historical TZ database and documented version | Python zoneinfo with available tzdata | Offline fixture only; independent rule provenance and version pinning TBD | No incremental spend |
| Session convention | Published, reproducible definition for each chosen market/session; holidays & exceptional trading days | Exchange / central bank / venue calendars, independently reviewed | Convention selected; historical calendar not certified | No incremental spend |
| Bid-ask or liquidity proxy | Timestamped, feed-specific data, quote availability and legal reuse | Existing licensed data must be inventoried first | NOT ADMITTED | Unknown; no purchase |
| Order flow / inventory proxy | Independently sourced observable proxy for proposed dealer transfer mechanism | No admissible source identified | NOT ADMITTED | Unknown; no purchase |
| Events/confounders | Official announcement schedule and blackout logic at appropriate fidelity | BLS timing adapter exists for a separate CPI test only | Not yet integrated for handoff | No incremental spend |
| Trading frictions | Spread, commission, latency/slippage and executable quotes | Requires provenance of bid/ask and venue | NOT ADMITTED | Unknown; no purchase |

## Admission decision
**NO EMPIRICAL SESSION-HANDOFF TEST ADMITTED YET.**
Before reading FX prices, returns or any outcome, independently establish market session calendar provenance and available microstructure inputs, explicitly choose a non-directional estimand, and predeclare controls, adverse tests, effect sizes and multiplicity budget under RND-0062. Do not use old champion strategy selection as evidence.

## Firewall
No Trading Economics trial or other provider spend. No broker or capital writes. No changes to protected M005/M006e state. Do not inspect validation 2021–22, reserved final 2023–24, or sealed Q003 / RND0060QR prospective outcomes. No automatic merge or promotion.

## Validation
Run `python3 -m unittest test_rnd0074_session_clock_rehearsal.py` from `rnd/orchestration`. Twenty-four offline synthetic/hostile cases are provided. Record a human-verified receipt only after inspecting terminal output.
