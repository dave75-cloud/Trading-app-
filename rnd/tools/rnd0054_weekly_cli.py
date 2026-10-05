#!/usr/bin/env python3
"""One-command outcome-blind prospective weekly workflow for RND-0054.

Sequence: recompute full ledger -> plan exact next window -> GET-only OANDA Practice
acquisition -> structural verification -> append hash-bound record -> full re-audit ->
write a new ledger file. Existing ledgers and sealed evidence are never overwritten.
No strategy evaluation, validation readout, reserved-final access, broker writes,
automatic promotion, or capital authority.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
TOOLS = ROOT / "rnd" / "tools"
sys.path.insert(0, str(ORCH))
sys.path.insert(0, str(TOOLS))

from rnd0054_generic_acquire import acquire_window  # noqa: E402
from rnd0054_ledger import audit_and_advance  # noqa: E402
from rnd0054_weekly_workflow import plan_next, verify_and_advance  # noqa: E402

LEDGER_VERSION = "RND-0054-prospective-ledger-v0.1"


class RND0054CLIError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0054CLIError(message)


def _load(path):
    return json.loads(Path(path).expanduser().read_text())


def _write_new(path, value):
    path = Path(path).expanduser().resolve()
    _req(not path.exists(), "new ledger target already exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    return path


def recompute_ledger(document):
    _req(isinstance(document, dict), "ledger document mapping required")
    _req(document.get("contract_version") == LEDGER_VERSION, "ledger contract version mismatch")
    records = document.get("records")
    _req(isinstance(records, list) and records, "ledger records required")
    state = audit_and_advance(records)
    return records, state


def execute(document, now_utc, tranche_output, repo_root=ROOT):
    records, state = recompute_ledger(document)
    plan = plan_next(state, now_utc)
    _req(plan.get("status") == "RUNNABLE", f"next tranche is not runnable: {plan.get('status')}")
    window = plan["window"]
    target = acquire_window(
        window["start_utc"], window["end_utc"], tranche_output, repo_root
    )
    advanced = verify_and_advance(
        records, target, window["start_utc"], window["end_utc"]
    )
    return {
        "contract_version": LEDGER_VERSION,
        "records": advanced["records"],
        "state": advanced["ledger_state"],
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--tranche-output", required=True)
    parser.add_argument("--new-ledger", required=True)
    parser.add_argument("--now-utc")
    args = parser.parse_args()

    now_utc = args.now_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current = _load(args.ledger)
    updated = execute(current, now_utc, args.tranche_output, ROOT)
    ledger_path = _write_new(args.new_ledger, updated)

    state = updated["state"]
    print("RND0054_WEEKLY_WORKFLOW: PASS")
    print(f"tranche_count={state['tranche_count']}")
    print(f"cumulative_end_utc={state['cumulative_end_utc']}")
    print(f"state={state['state']}")
    print("strategy_evaluation=FALSE")
    print("reserved_final_access=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print("automatic_promotion=FALSE")
    print(f"new_ledger={ledger_path}")


if __name__ == "__main__":
    main()
