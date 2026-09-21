#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"

required = [
    "m006e3_concurrency_excerpt.txt",
    "source_provenance.json",
    "session_disposition_2026-09-17.json",
    "bridge_cycle_20260917T121459Z.json",
    "cycle_20260917T121429Z.log",
]

for name in required:
    if not (INPUTS / name).is_file():
        raise SystemExit(f"missing input: {name}")

disp = json.loads(
    (INPUTS / "session_disposition_2026-09-17.json").read_text()
)

bridge = json.loads(
    (INPUTS / "bridge_cycle_20260917T121459Z.json").read_text()
)

excerpt = (INPUTS / "m006e3_concurrency_excerpt.txt").read_text()
log = (INPUTS / "cycle_20260917T121429Z.log").read_text()

assert "m006c_before_hash" in excerpt
assert "m006c_after_hash" in excerpt
assert "M006c state changed" in excerpt
assert "M006c state changed during bridge run" in log

assert disp["contained_local_concurrency_failures"] == 1
assert disp["integrity"]["trading_order_writes"] == 0

result = {
    "analysis_version": "RND-0004-v1.0",

    "incident": {
        "day": "2026-09-17",
        "classification": "contained local concurrency/state-race failure",
        "fail_closed": True,
        "trading_order_writes": 0,
        "safety_violation": False,
    },

    "mechanism": {
        "m006e3_reads_m006c_hash_before": True,
        "m006e3_reads_m006c_hash_after": True,
        "hash_change_causes_fail_closed": True,
        "concurrent_m006c_writer_present": True,
    },

    "candidates": [
        {
            "name": "scheduler_serialization",
            "prevents_overlap_by_construction": True,
            "requires_bridge_logic_change": False,
            "requires_shared_lock_protocol": False,
            "runtime_drift_sensitive": False,
            "assessment": "preferred post-observation design candidate",
        },
        {
            "name": "shared_lock",
            "prevents_overlap_by_construction": True,
            "requires_bridge_logic_change": True,
            "requires_shared_lock_protocol": True,
            "runtime_drift_sensitive": False,
            "assessment": "strong fallback if centralized sequencing unavailable",
        },
        {
            "name": "schedule_deconfliction",
            "prevents_overlap_by_construction": False,
            "requires_bridge_logic_change": False,
            "requires_shared_lock_protocol": False,
            "runtime_drift_sensitive": True,
            "assessment": "not sufficient as primary long-term control",
        },
        {
            "name": "weaken_hash_integrity_check",
            "prevents_overlap_by_construction": False,
            "requires_bridge_logic_change": True,
            "requires_shared_lock_protocol": False,
            "runtime_drift_sensitive": False,
            "assessment": "reject",
        },
    ],

    "preferred_design": "scheduler_serialization",
    "hash_integrity_check": "PRESERVE",
    "implementation_status": "DESIGN_ONLY_NOT_AUTHORISED",

    "input_sha256": {},
}

for name in required:
    p = INPUTS / name
    result["input_sha256"][name] = hashlib.sha256(
        p.read_bytes()
    ).hexdigest()

(ROOT / "analysis.json").write_text(
    json.dumps(result, indent=2) + "\n"
)

report = """# RND-0004 — M006c/M006e.3 Concurrency-Race Design Analysis

## Finding

The 17 September failure is consistent with a scheduler/concurrency-contract
mismatch.

M006e.3 snapshots the M006c state hash before its processing window and compares
that hash again near the end of the run. During the incident, an independently
scheduled M006c process changed that state. M006e.3 detected the change and
failed closed.

The reviewed incident evidence records zero trading writes and no safety
violation. The fail-close protection therefore operated as intended.

## Candidate controls

### Scheduler serialization — preferred

Place M006c and M006e.3 under one sequencing authority so their state-sensitive
execution windows cannot overlap.

Advantages:

- prevents the observed race by construction;
- preserves the existing M006e.3 integrity check;
- does not require changing M006e.3 decision or safety logic;
- does not rely on estimated runtime or clock spacing.

This is the preferred post-observation design candidate.

### Shared mutual-exclusion lock

Require M006c and M006e.3 to acquire the same lock around state-sensitive
activity.

This also prevents overlap by construction, but both execution paths must
correctly participate and stale-lock handling becomes an additional mechanism
requiring validation.

This is the preferred fallback if centralized sequencing is unavailable.

### Schedule deconfliction

Offset the independent schedules so executions normally occur at different
times.

This reduces collision probability but cannot eliminate the race. Runtime
variation, retries, host load or delayed starts can recreate the overlap.

It should not be the primary long-term control.

### Weaken the hash-integrity check

Rejected.

The before/after hash comparison is the control that detected the unexpected
concurrent state change. Weakening it would remove evidence of the race rather
than fixing the race itself.

## Recommendation

After frozen forward observation is complete, prototype scheduler serialization
outside the accepted stack.

Retain the existing M006e.3 before/after hash comparison as a secondary
fail-closed integrity defence even after serialization is introduced.

## Authority

This is design-only R&D.

It does not authorize modification of M006e, M006c, M005, strategy parameters,
risk sizing, broker execution, promotion, or capital deployment.
"""

(ROOT / "analysis.md").write_text(report)

print("RND-0004 ANALYSIS COMPLETE")
print("incident=CONTAINED_LOCAL_CONCURRENCY")
print("fail_closed=TRUE")
print("safety_violation=FALSE")
print("preferred_design=SCHEDULER_SERIALIZATION")
print("hash_integrity_check=PRESERVE")
print("implementation=DESIGN_ONLY_NOT_AUTHORISED")
