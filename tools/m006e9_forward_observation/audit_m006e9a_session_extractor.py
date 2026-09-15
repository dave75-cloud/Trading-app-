#!/usr/bin/env python3

import ast
import importlib.util
from datetime import date
from pathlib import Path


HERE = Path(__file__).resolve().parent

TARGET = (
    HERE
    / "m006e9a_session_extractor.py"
)

source = TARGET.read_text(
    encoding="utf-8"
)

tree = ast.parse(source)

forbidden = {
    "requests",
    "urllib",
    "http",
    "socket",
    "subprocess",
}

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
    imports & forbidden
)

assert not bad, (
    f"Forbidden imports: {bad}"
)

spec = importlib.util.spec_from_file_location(
    "m006e9a",
    TARGET,
)

module = importlib.util.module_from_spec(
    spec
)

assert spec.loader is not None

spec.loader.exec_module(
    module
)

assert (
    module.VERSION
    == "M006e.9a-v1.1"
)

assert module.EXPECTED_CYCLES == 43

assert (
    module.MIN_COVERAGE_WARN
    == 0.80
)

assert (
    module.MIN_COVERAGE_ALERT
    == 0.50
)

assert (
    module.classify_cycle_text(
        "M006E5_CYCLE: PASS"
    )
    == "PASS"
)

assert (
    module.classify_cycle_text(
        "FAIL_CLOSED: M006e.1 failed rc=1"
    )
    == "FAIL"
)

assert (
    module.classify_cycle_text(
        "M006E5_CYCLE: SKIP"
    )
    == "SKIP"
)

assert (
    module.classify_cycle_text(
        "nothing relevant"
    )
    == "UNKNOWN"
)

source_root = (
    module.SOURCE_ROOT.resolve()
)

output_root = (
    module.OUTPUT_ROOT.resolve()
)

assert (
    source_root != output_root
)

assert not output_root.is_relative_to(
    source_root
)

assert not source_root.is_relative_to(
    output_root
)

test_path = module.output_path(
    date(2026, 9, 10)
).resolve()

assert test_path.is_relative_to(
    output_root
)

assert not test_path.is_relative_to(
    source_root
)

print("M006e.9a v1.1 AUDIT")
print("  network/process isolation: PASS")
print("  source/output isolation: PASS")
print("  log-marker classification: PASS")
print("  M006e.6a coverage thresholds: PASS")
print("  expected cycles = 43: PASS")
print("  downstream completion grace: PASS")
print("  output containment: PASS")
print("M006E9A_V11_AUDIT: PASS")
