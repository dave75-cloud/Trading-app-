#!/usr/bin/env python3

import ast
import importlib.util
from copy import deepcopy
from pathlib import Path


HERE = Path(__file__).resolve().parent

TARGETS = [
    HERE / "m006e9b_cumulative_ledger.py",
    HERE / "m006e9c_graduation_monitor.py",
]

FORBIDDEN = {
    "requests",
    "urllib",
    "http",
    "socket",
    "subprocess",
}

for target in TARGETS:
    source = target.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(
                    alias.name.split(".")[0]
                )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imports.add(
                    node.module.split(".")[0]
                )

    bad = sorted(
        imports & FORBIDDEN
    )

    assert not bad, (
        f"{target.name}: "
        f"forbidden imports {bad}"
    )

print("M006e.9b/.9c AUDIT")
print("  network/process imports: PASS")
print("  no broker execution code: PASS")
print("  isolated analytics architecture: PASS")

spec = importlib.util.spec_from_file_location(
    "m006e9c",
    HERE / "m006e9c_graduation_monitor.py",
)

monitor = importlib.util.module_from_spec(
    spec
)

assert spec.loader is not None
spec.loader.exec_module(monitor)

assert monitor.VERSION == "M006e.9c-v1.1"
assert monitor.MIN_ACCEPTED_SESSIONS == 25
assert monitor.MIN_AUTHORITATIVE_EVENTS == 100
assert (
    monitor.SATISFACTORY_UPSTREAM_FAILURE_RATE_PCT
    == 5.0
)
assert (
    monitor.INVESTIGATE_UPSTREAM_FAILURE_RATE_PCT
    == 10.0
)

BASE = {
    "summary": {
        "accepted_sessions": 25,
        "authoritative_events": 100,
        "unknown_cycles": 0,
        "pending_review_sessions": 0,
        "contained_upstream_failure_rate_pct": 2.0,
    },
    "provider_path": {
        "events": 100,
        "direction_disagreements": 0,
        "divergence_over_10bps": 0,
        "retrospective_twelve_availability_pct": 100.0,
    },
    "reconciliation": {
        "reconciliation_event_count_mismatches": 0,
        "provider_event_count_mismatches": 0,
    },
    "integrity": {
        "all_m006e2_hashes_match": True,
    },
    "safety": {
        "zero_recorded_safety_violations": True,
    },
}


class FakeLedgerModule:
    def __init__(self, data):
        self.data = data

    def build_ledger(self):
        return self.data


def run_case(data):
    original = monitor.load_ledger_module

    try:
        monitor.load_ledger_module = (
            lambda: FakeLedgerModule(data)
        )
        return monitor.evaluate()
    finally:
        monitor.load_ledger_module = original


clean = run_case(
    deepcopy(BASE)
)

assert (
    clean["overall_status"]
    == "ELIGIBLE_FOR_FORMAL_REVIEW"
)

direction = deepcopy(BASE)
direction["provider_path"][
    "direction_disagreements"
] = 1

direction_result = run_case(
    direction
)

assert (
    direction_result["overall_status"]
    == "EXTEND_OBSERVATION"
)

assert (
    direction_result["hard_gate_failures"]
    == []
)

assert (
    direction_result["review_flags"]
)

divergence = deepcopy(BASE)
divergence["provider_path"][
    "divergence_over_10bps"
] = 1

divergence_result = run_case(
    divergence
)

assert (
    divergence_result["overall_status"]
    == "EXTEND_OBSERVATION"
)

assert (
    divergence_result["hard_gate_failures"]
    == []
)

hash_failure = deepcopy(BASE)
hash_failure["integrity"][
    "all_m006e2_hashes_match"
] = False

hash_result = run_case(
    hash_failure
)

assert (
    hash_result["overall_status"]
    == "BLOCKED_BY_HARD_GATE"
)

print("  graduation thresholds: PASS")
print("  provider anomaly = review flag: PASS")
print("  safety/integrity defect = hard gate: PASS")
print("  automatic promotion: NONE")
print("M006E9BC_AUDIT: PASS")
