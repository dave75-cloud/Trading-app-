# KQTRL M007 — OANDA Practice Execution Specification

Status: DESIGN ONLY
Execution capability: NONE
OANDA environment: PRACTICE ONLY
Live capital: PROHIBITED
Order writes: NOT IMPLEMENTED

---

## 1. Purpose

M007 defines the execution architecture required to convert an accepted
M006e dry-run trading decision into an actual OANDA **practice-account**
order.

M007 does not alter the frozen trading strategy.

It does not determine whether a signal should exist.

It does not alter:

- moving-average parameters;
- volatility threshold;
- session hours;
- minimum holding period;
- portfolio allocation rules;
- currency-leg caps;
- gross exposure caps;
- entry-validation rules;
- exit-validation rules.

M007 begins only after the M006e decision architecture has determined that
an execution action is permitted.

---

## 2. Core Principle

Execution must be:

1. deterministic;
2. idempotent;
3. restart-safe;
4. position-aware;
5. fill-aware;
6. reconciliation-driven;
7. fail-closed;
8. practice-only.

No execution request may rely on assumed account state.

The actual OANDA account must be queried immediately before any write.

---

## 3. Authority Hierarchy

Execution authority remains:

1. OANDA — authoritative market/execution venue;
2. Twelve Data — independent validation;
3. Polygon/Massive — delayed reconciliation only.

Polygon/Massive must never veto or authorize real-time execution.

---

## 4. Safety Master Switch

Future order-capable M007 code must require all of:

- `OANDA_ENV=practice`
- valid OANDA practice account;
- explicit execution master switch;
- exact accepted source hash;
- preflight PASS;
- fresh OANDA price;
- verified account state;
- no unresolved execution ambiguity.

Default state must always be:

    ENABLE_DEMO_EXECUTION=NO

Absence of the variable is equivalent to NO.

Any value other than the exact accepted enable value must prevent writes.

No future M007 process may support the OANDA live endpoint.

---

## 5. Event Identity

Every executable action must have a deterministic immutable event ID.

Minimum identity inputs:

- strategy version;
- authoritative provider;
- pair;
- authoritative bar timestamp;
- event type;
- old strategy position;
- new strategy position.

Example conceptual identity:

    M006e|OANDA|EURUSD|2026-09-01T12:40:00Z|entry|flat|long

The identity must survive:

- process restart;
- scheduler restart;
- machine reboot;
- temporary API failure.

The same event ID must never create two independent entry orders.

---

## 6. Idempotency

Before submitting any practice order, M007 must check:

1. local execution ledger;
2. OANDA open trades;
3. OANDA open positions;
4. OANDA pending orders;
5. prior transaction/order identifiers.

If the event has already been executed or materially satisfied:

    NO NEW ORDER

If execution status is ambiguous:

    FAIL CLOSED

Ambiguity must never be resolved by simply resubmitting the order.

---

## 7. Account-State Verification

Immediately before every execution write, obtain fresh OANDA state:

- account summary;
- open positions;
- open trades;
- pending orders;
- current pricing.

Execution must be blocked if:

- account is not the configured practice account;
- unexpected exposure exists;
- the intended pair is in an unexplained state;
- an unresolved pending order exists;
- account state cannot be reconciled with the local execution ledger.

---

## 8. Entry Policy

An entry write may occur only if all M006d.1 / M006e entry gates pass.

Required state:

- authoritative OANDA signal non-zero;
- Twelve direction agrees;
- Twelve volatility eligibility agrees;
- Twelve data fresh;
- OANDA price fresh;
- event age acceptable;
- price divergence below block threshold;
- sizing calculation accepted;
- account exposure compatible with requested entry;
- event not already executed.

Entry writes must never repair unexpected account state automatically.

Unexpected state => fail closed.

---

## 9. Exit Policy

Risk-reducing exits have higher execution priority than entries.

An exit must not be blocked solely because Twelve disagrees with OANDA.

Required:

- authoritative strategy exit;
- fresh OANDA account state;
- fresh execution-side OANDA price;
- actual position available to reduce/close.

If the account is already flat:

- classify the event as ALREADY_SATISFIED;
- do not create a new order.

If position size differs from expected:

- do not silently assume the local ledger is correct;
- reconcile;
- close only under explicitly defined safe reconciliation rules.

---

## 10. Reversal Policy

A reversal is never one opaque operation.

It is:

    LEG 1 — EXIT EXISTING POSITION
    LEG 2 — VERIFY EXIT RESULT
    LEG 3 — RE-RUN ENTRY GATES
    LEG 4 — NEW ENTRY

The entry leg must never be submitted until the exit leg is confirmed.

If the exit fails or remains uncertain:

    REVERSAL STOPS

No new opposite-side entry may occur.

---

## 11. Sizing

M007 must use the exact accepted M006d.2 allocation logic.

Constraints:

- maximum 1x per trade;
- maximum 4x nominal gross;
- maximum 3x gross currency-leg;
- simultaneous entries allocated pro-rata;
- AUD account base;
- units derived from current NAV and conversion rates.

The execution implementation must not introduce a new sizing model.

Before submission, record:

- NAV;
- relevant conversion price;
- desired allocation;
- accepted alpha;
- final units;
- cap responsible for any resize.

---

## 12. Order Type

Initial M007 practice execution should use the simplest deterministic order
type compatible with the research model.

Preferred initial implementation:

    MARKET order

Reason:

The frozen research model conceptually executes on the next-bar close and
does not currently contain limit-order or stop-entry logic.

Adding limit-order logic would introduce a new execution strategy rather
than simply implementing the existing one.

---

## 13. Fill Verification

A successful HTTP response is not sufficient evidence of execution.

After every submitted practice order, retrieve and record:

- OANDA order ID;
- transaction ID;
- fill transaction ID;
- fill price;
- requested units;
- filled units;
- resulting position;
- transaction timestamp.

The resulting account position must then be independently queried.

Only after that reconciliation may the local execution ledger classify the
event as:

    EXECUTED_CONFIRMED

---

## 14. Partial Fills

If OANDA reports fewer filled units than requested:

    PARTIAL_FILL

M007 must not blindly submit the missing balance.

Instead:

1. record the actual fill;
2. retrieve actual account state;
3. calculate residual difference;
4. classify the event for reconciliation;
5. require explicitly defined residual-execution logic before another write.

Initial implementation should preferably fail closed on partial fills rather
than auto-completing them.

---

## 15. Slippage

For every executed practice order record:

    slippage_bps =
        (fill_price / reference_price - 1) * 10000

with direction-aware interpretation.

Record:

- authoritative bar close;
- latest OANDA executable/reference price;
- submitted reference price;
- actual fill price;
- absolute slippage;
- signed slippage;
- execution latency.

No slippage threshold should modify the frozen strategy without separate
research approval.

---

## 16. Execution Ledger

M007 requires a separate append-only execution ledger.

Minimum record:

- event_id;
- pair;
- strategy event;
- intended side;
- intended allocation;
- intended units;
- pre-write account position;
- validation result;
- order submission timestamp;
- OANDA order ID;
- transaction ID;
- fill ID;
- filled units;
- fill price;
- post-write position;
- result status;
- reconciliation status;
- error category.

Execution ledger must remain separate from:

- M005 canonical records;
- M006e observer state;
- M006e dry-run bridge state.

---

## 17. State Machine

Recommended event states:

    NEW
    VALIDATED
    READY_TO_EXECUTE
    WRITE_ATTEMPTED
    EXECUTED_CONFIRMED
    ALREADY_SATISFIED
    BLOCKED
    RETRY_PENDING_READ_ONLY
    AMBIGUOUS_WRITE_RESULT
    RECONCILIATION_REQUIRED
    PARTIAL_FILL
    FAILED_CLOSED

A write-attempted event must never return to NEW.

---

## 18. Ambiguous Network Failure

Critical case:

The client submits a request but loses network connectivity before learning
whether OANDA accepted it.

This must be treated as:

    AMBIGUOUS_WRITE_RESULT

The system must NOT resend the order.

Required recovery sequence:

1. query OANDA transactions;
2. query pending orders;
3. query open trades;
4. query current positions;
5. match using instrument, units, timing and client identifiers;
6. determine whether the original request executed.

Only reconciliation may resolve ambiguity.

---

## 19. Client Extensions / Idempotency Metadata

Where supported by OANDA, practice orders should carry deterministic client
metadata derived from the event ID.

Example conceptual fields:

    clientExtensions.id
    clientExtensions.tag

The exact permitted format and length must be verified against the OANDA API
before implementation.

This metadata should assist restart and duplicate-order reconciliation.

---

## 20. Restart Recovery

On process startup:

1. load local execution ledger;
2. retrieve current OANDA account state;
3. inspect all non-terminal execution events;
4. reconcile any WRITE_ATTEMPTED or AMBIGUOUS_WRITE_RESULT state;
5. refuse new writes until reconciliation completes.

Machine restart must never cause automatic event replay.

---

## 21. Scheduler Behaviour

M007 should initially run downstream of the accepted M006e decision path.

Conceptual order:

    M006e.1 authoritative observer
        ↓
    M006e.2 validator
        ↓
    M006e.3 / accepted execution decision
        ↓
    M007 execution preflight
        ↓
    M007 practice order
        ↓
    M007 fill reconciliation
        ↓
    M007 execution ledger

The M006e observer must never depend on M007 succeeding.

---

## 22. Emergency Fail-Closed Conditions

Immediately prohibit new entry writes if any of the following occurs:

- OANDA environment not practice;
- master execution switch invalid;
- source hash mismatch;
- stale OANDA pricing;
- unexplained OANDA account position;
- unresolved ambiguous write;
- unresolved partial fill;
- pending order not represented in local ledger;
- account ID mismatch;
- malformed sizing result;
- negative/future price age;
- duplicated event identity;
- reconciliation failure;
- execution ledger unavailable.

Risk-reducing exit handling must be separately defined so that safety logic
does not accidentally prevent closure of an existing practice position.

---

## 23. Emergency Stop

Future execution implementation must support an immediate local kill switch.

Minimum behaviour:

    NEW ENTRIES DISABLED

A stronger emergency mode may also:

    CANCEL PENDING PRACTICE ORDERS

but must not automatically liquidate positions unless explicitly designed
and tested.

Emergency liquidation must never be an accidental consequence of disabling
the system.

---

## 24. Audit Requirements Before First Practice Order

No actual practice order may be enabled until all of the following exist and
PASS:

1. source static safety audit;
2. no-live-endpoint audit;
3. exact sizing equivalence audit;
4. duplicate-event/idempotency audit;
5. restart recovery audit;
6. ambiguous-write simulation;
7. partial-fill simulation;
8. reversal sequencing audit;
9. unexpected-position fail-closed audit;
10. account-ID mismatch audit;
11. stale-price audit;
12. execution-ledger persistence audit;
13. zero-write integration regression;
14. explicit human promotion step.

---

## 25. Promotion Stages

Recommended progression:

### M007a
Execution specification only.

No order code.

### M007b
Order-request construction only.

No POST.

### M007c
Mock transport execution engine.

Synthetic responses only.

### M007d
Failure-injection and restart reconciliation.

No OANDA write.

### M007e
OANDA practice execution candidate.

Writes disabled by default.

### M007f
Single controlled OANDA practice order.

Manual supervised test.

### M007g
Limited prospective practice execution.

Automated but practice-only.

### M007h
Extended practice validation.

No live capital.

Any consideration of live capital is outside M007 and requires a completely
new approval phase.

---

## 26. Non-Goals

M007 is NOT:

- strategy optimization;
- signal modification;
- discretionary trading;
- stop-loss research;
- leverage increase;
- live trading;
- broker switching;
- threshold tuning.

---

## 27. Frozen Safety Declaration

As of this specification:

    ORDER WRITES IMPLEMENTED: FALSE
    OANDA LIVE SUPPORT: FALSE
    LIVE CAPITAL: FALSE
    CANONICAL M005 MODIFIED: FALSE
    ACTIVE M006e MODIFIED: FALSE
    PRACTICE EXECUTION ENABLED: FALSE
