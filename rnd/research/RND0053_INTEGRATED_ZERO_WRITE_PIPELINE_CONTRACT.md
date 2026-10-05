# RND-0053 — Integrated Zero-Write Pipeline Contract

## Purpose

Integrate the independently fixture-verified RND-0049 through RND-0052 kernels on one branch and test their interfaces as a single fail-closed control path.

This task does not open Q003 prospective outcomes, reserved-final evidence, broker writes, capital authority, live authority, or promotion authority.

## Imported verified components

- RND-0049 validation decision classifier.
- RND-0050 prospective weekly acquisition planner.
- RND-0051 fixture-only shadow risk kernel.
- RND-0052 human-gated control-state machine.

The imported kernels are copied unchanged from their verified checkpoint implementations.

## Integrated flow

1. Prospective accumulation remains outcome-blind and is planned from the verified evidence ledger only.
2. Validation readout is impossible before the 180-day evidence boundary and requires an explicit human readout gate.
3. Structural evidence failure must not expose economic metrics and maps only to `VALIDATION_INCONCLUSIVE_STRUCTURAL`.
4. Structurally valid evidence plus an authorized one-time readout is classified by the frozen RND-0049 rule as `VALIDATION_SUPPORTED` or `VALIDATION_REJECTED`.
5. A rejected candidate is terminal for this candidate and may not enter shadow.
6. A supported candidate still requires separately explicit human state transitions before shadow eligibility or shadow activity.
7. Shadow evaluation in RND-0053 is fixture-only. No real Q003 signals are generated or consumed.
8. Risk decisions never construct orders and always return broker writes, capital authority, and execution authority false.
9. Lifecycle state never grants authority by itself.
10. Reserved-final evidence remains closed throughout.

## Human gates

RND-0053 distinguishes two explicit human decisions:

- `validation_readout_authorized`: permits the one-time economic readout only after structural eligibility.
- lifecycle transition authorization: permits only the specific declared RND-0052 state edge.

Neither gate grants broker-write, capital, live, or automatic promotion authority.

## Acceptance criteria

- all imported component invariants remain true;
- premature readout fails closed;
- structural failure cannot accept metrics;
- validation rejection cannot progress to shadow;
- validation support cannot skip human transition gates;
- fixture shadow acceptance remains zero-write;
- kill-switch, stale evidence, duplicates, exposure-limit breaches and authority escalation still reject;
- no function in the RND-0053 coordinator performs network, broker, file, credential, order, or market-data access.

## Express prohibitions

No prospective Q003 performance access now; no reserved-final access; no strategy tuning; no pair dropping or reweighting; no threshold changes; no actual order construction; no OANDA order endpoint; no broker writes; no capital allocation; no live environment authority; no automatic promotion; no merge without human approval.
