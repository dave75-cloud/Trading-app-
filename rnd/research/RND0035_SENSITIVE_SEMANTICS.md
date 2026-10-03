# RND-0035 — Frozen Sensitive-Family Semantics

Status: PRE-OUTCOME / SYNTHETIC-FIXTURE STAGE

This document freezes the exact semantics for RND-0035 families E and F before any historical robustness outcomes are generated. It does not open the outcome gate.

## Common invariants

All variants retain the RND-0034 rules unless a rule below explicitly makes execution more conservative:

- no synthetic, interpolated or backfilled observations;
- bid/ask execution only;
- indicator state resets on every observation discontinuity;
- pending delayed signals are cancelled on discontinuity;
- an already-open economic position survives a gap and is revalued only on genuine post-gap bid/ask evidence;
- missing nominal bars never count toward indicator warm-up, signal delay, minimum hold, cooldown, or execution latency;
- no future information may be used;
- validation/final-test access remains closed;
- broker writes, capital authority, automatic promotion and automatic merge remain false.

## E001 — POST_GAP_COOLDOWN_1_COMPLETE_SESSION

Purpose: test whether conclusions depend on allowing fresh entries immediately after a discontinuity.

Exact rule:

1. A gap activates an entry-suppression state. Existing positions are unaffected by the suppression state.
2. Strategy indicators still reset exactly as in RND-0034 and may warm normally on genuine post-gap observations.
3. Signals may be computed and delayed normally during suppression, but **no new position may be opened** while suppression is active.
4. Suppression ends only after one entire reference UTC trading session for that symbol has been observed without any discontinuity inside that session.
5. A qualifying session is the symbol's frozen R000 session: AUDUSD [11,14), EURUSD/GBPUSD/USDJPY [11,13), Monday-Friday UTC.
6. If the gap occurs before that day's session and every nominal M5 observation from session open through the final in-session observation is genuinely present, that same day's session may satisfy the cooldown.
7. If the gap occurs at or after session open, that session cannot satisfy the cooldown because it was not observed in full after the gap; the earliest qualifying session is a later weekday session.
8. Any discontinuity during a candidate cooldown session invalidates that candidate and restarts the search for a later complete session.
9. Entry eligibility resumes only on the first genuine observation **after** the qualifying session has ended. No signal generated before eligibility resumes is carried forward for entry; normal signal-delay state at that point governs future entries.
10. No forced exit is created by this policy.

## E002 — POST_GAP_REQUIRE_100_CONTIGUOUS_OBSERVED_BARS_BEFORE_NEW_ENTRY

Purpose: impose a stronger post-gap evidence rebuild before accepting new exposure.

Exact rule:

1. A gap activates entry suppression. Existing positions remain economically open exactly as in RND-0034.
2. The first genuine post-gap observation counts as contiguous bar 1.
3. Only genuine consecutive M5 observations increment the counter.
4. Any subsequent discontinuity resets the counter; its first genuine post-gap observation becomes bar 1 of a new sequence.
5. No new position may be opened on bars 1 through 99.
6. After bar 100 has been fully observed and processed, entry eligibility begins on the **next** genuine contiguous observation (bar 101 or later).
7. Signals generated during bars 1-100 do not create deferred entry authority. Signal calculation/delay state follows ordinary RND-0034 semantics, but an entry requires an otherwise-valid delayed signal arriving when eligibility is already open.
8. No forced exit is created by this policy.

## F001 — ADDITIONAL_1_OBSERVED_BAR_ENTRY_LATENCY

Purpose: degrade entry execution without using future information.

Exact rule:

1. When RND-0034 would open a new position on observation T, create a pending entry instruction instead.
2. Execute that pending entry on the next genuine contiguous M5 observation T+1 using that observation's executable bid/ask price.
3. A discontinuity between T and T+1 cancels the pending entry; it is not carried across the gap.
4. If a fresh strategy instruction at T+1 would contradict or neutralize the pending direction before execution, cancel the pending entry rather than execute stale exposure.
5. A pending entry that reaches end-of-sample without a next eligible observation is cancelled and recorded, not synthetically filled.
6. Once executed, minimum-hold accounting starts at the delayed actual entry observation.

## F002 — ADDITIONAL_1_OBSERVED_BAR_EXIT_LATENCY

Purpose: degrade exits conservatively.

Exact rule:

1. When RND-0034 would close an open position on observation T, create a pending exit instruction instead of closing immediately.
2. Execute that exit on the next genuine contiguous M5 observation T+1 using that observation's executable bid/ask price.
3. A discontinuity does **not** manufacture a fill. The economic position survives the gap; the pending exit is executed only on the first genuine post-gap observation, using that observation's executable bid/ask price. The event is marked gap-exposed.
4. While an exit is pending, no reversal/new entry is permitted.
5. A pending exit at end-of-sample leaves the position right-censored rather than synthetically closed.

## F003 — ADDITIONAL_1_OBSERVED_BAR_ENTRY_AND_EXIT_LATENCY

Apply F001 and F002 simultaneously. Entry latency is applied before a position exists; exit latency governs closure once a position exists. No same-observation reversal is possible under this variant.

## F004 — NO_SAME_OBSERVATION_EXIT_AND_REENTRY

Purpose: remove instantaneous reversal at one executable observation.

Exact rule:

1. If a delayed strategy signal on observation T requires closing the current position and reversing direction, close the current position at T using normal RND-0034 bid/ask execution.
2. Do **not** open the opposite position on T.
3. After the close, the system is flat. A later entry requires a newly eligible delayed strategy signal under normal delay semantics on a later genuine observation.
4. The reversal instruction that caused the exit does not itself create a carried pending entry.
5. Ordinary flat-to-position entries and ordinary exits remain otherwise unchanged.

## Evidence and accounting requirements

For every E/F trial, the event ledger must make suppressed/cancelled/delayed actions observable with explicit reasons. At minimum the implementation must distinguish:

- `ENTRY_SUPPRESSED_POST_GAP`;
- `POST_GAP_ELIGIBILITY_RESTORED`;
- `PENDING_ENTRY_CREATED` / `PENDING_ENTRY_CANCELLED` / `DELAYED_ENTRY_EXECUTED`;
- `PENDING_EXIT_CREATED` / `DELAYED_EXIT_EXECUTED`;
- `REVERSAL_REENTRY_SUPPRESSED`.

Synthetic fixture tests must prove these semantics before any E/F historical outcome is authorized.
