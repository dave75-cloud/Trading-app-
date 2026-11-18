#!/usr/bin/env python3
"""Review cumulative PR changes against the existing protected-path policy.

Read-only. No broker access, source modification, or promotion authority.
The protected regex is taken from the frozen Autonomous R&D Guard workflow;
we deliberately do not define a second, divergent list.
"""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / ".github/workflows/agent_guard.yml"


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    ).stdout


def main():
    base = os.environ.get("PR_BASE_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise SystemExit("CUMULATIVE_PATH_GUARD: FAIL (missing/invalid PR base SHA)")

    guard_text = GUARD.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*PROTECTED_RE='([^']+)'\s*$", guard_text)
    if not match:
        raise SystemExit("CUMULATIVE_PATH_GUARD: FAIL (cannot read frozen path policy)")
    protected = re.compile(match.group(1))

    subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"],
                   cwd=ROOT, check=True)
    # --no-renames ensures both sides of a moved protected file are checked.
    paths = [p for p in git("diff", "--no-renames", "--name-only",
                           f"{base}...HEAD").splitlines() if p]
    violations = [p for p in paths if protected.search(p)]
    print(f"CUMULATIVE_PATH_GUARD: reviewed {len(paths)} changed paths")
    if violations:
        print("CUMULATIVE_PATH_GUARD: FAIL")
        for path in violations:
            print("PROTECTED:", path)
        raise SystemExit(1)
    print("CUMULATIVE_PATH_GUARD: PASS")
    print("Scope: complete PR diff from provided base SHA; not a trading authority check")


if __name__ == "__main__":
    main()
