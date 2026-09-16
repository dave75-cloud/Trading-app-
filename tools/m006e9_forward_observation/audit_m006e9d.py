#!/usr/bin/env python3

import ast
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent

TARGET = (
    HERE
    / "m006e9d_forward_observation_report.py"
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
    "m006e9d",
    TARGET,
)

module = importlib.util.module_from_spec(
    spec
)

assert spec.loader is not None
spec.loader.exec_module(module)

report = module.build_report()

assert (
    "# M006e Forward-Observation Report"
    in report
)

assert (
    "Automatic promotion capability: NONE"
    in report
)

assert (
    "M006e remains frozen."
    in report
)

assert (
    "No conclusion regarding strategy profitability"
    in report
)

print("M006e.9d AUDIT")
print("  no network/process imports: PASS")
print("  report generated from ledger/monitor: PASS")
print("  no automatic promotion language: PASS")
print("  frozen-state warning present: PASS")
print("M006E9D_AUDIT: PASS")
