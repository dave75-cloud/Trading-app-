#!/usr/bin/env python3
"""Bounded launcher for RND-0035.

The repository trial plan is authoritative. While its execution gate is
closed this launcher permits only synthetic fixture self-checks. It refuses
historical evidence paths and refuses all undeclared trials.

This launcher has no broker/network/capital/promotion authority.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rnd0035_adversarial_kernel import RND0035KernelError, run_trial_pair
from rnd0035_trial_plan import RND0035PlanError, load_plan


PLAN_PATH = Path(__file__).parents[1] / "research" / "RND0035_TRIAL_PLAN.json"


class RND0035RunnerError(ValueError):
    pass


def _fixture_rows(count=90, start="2019-01-02T07:00:00Z", gap_after=None):
    dt = datetime.fromisoformat(start[:-1] + "+00:00")
    price = 1.0
    out = []
    for i in range(count):
        if gap_after is not None and i == gap_after:
            dt += timedelta(minutes=10)
        price *= 1.0015 if i % 2 == 0 else 1.0002
        spread = price * 0.0001
        out.append({
            "timestamp_utc": dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": f"{price - spread / 2:.9f}",
            "ask_close": f"{price + spread / 2:.9f}",
            "mid_close": f"{price:.9f}",
        })
        dt += timedelta(minutes=5)
    return out


def fixture_self_check(plan):
    if plan["outcomes_authorized"] or plan["execution_gate"]["new_outcomes_may_run"]:
        raise RND0035RunnerError("fixture launcher requires global outcome gate closed")

    checks = {}
    fixture = _fixture_rows()
    for trial_id in ("R000", "A001", "A017", "C001", "D001", "D004"):
        result = run_trial_pair(trial_id, "AUDUSD", fixture)
        checks[trial_id] = {
            "completed_trade_count": result["completed_trade_count"],
            "broker_writes": result["authority"].get("broker_writes", False),
            "capital_authority": result["authority"].get("capital_authority", False),
            "validation_open": result["authority"].get("validation_open", False),
            "final_test_open": result["authority"].get("final_test_open", False),
        }

    # E/F are intentionally not executable at this stage.
    rejected = []
    for trial_id in ("E001", "E002", "F001", "F004"):
        try:
            run_trial_pair(trial_id, "AUDUSD", fixture)
        except RND0035KernelError:
            rejected.append(trial_id)
        else:
            raise RND0035RunnerError(f"{trial_id}: sensitive family executed before fixture freeze")

    if any(
        value["broker_writes"]
        or value["capital_authority"]
        or value["validation_open"]
        or value["final_test_open"]
        for value in checks.values()
    ):
        raise RND0035RunnerError("authority boundary opened during fixture check")

    return {
        "task_id": "RND-0035",
        "mode": "SYNTHETIC_FIXTURE_ONLY",
        "historical_outcomes_generated": False,
        "global_outcome_gate_open": False,
        "checks": checks,
        "sensitive_trials_rejected": rejected,
        "status": "PASS",
    }


def historical_run_prohibited(plan, evidence_root):
    if not plan["execution_gate"]["new_outcomes_may_run"]:
        raise RND0035RunnerError(
            "historical RND-0035 outcomes prohibited: execution gate remains closed"
        )
    raise RND0035RunnerError(
        "historical runner not implemented in pre-outcome stage"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture-self-check", action="store_true")
    group.add_argument("--evidence-root")
    args = parser.parse_args(argv)

    plan = load_plan(PLAN_PATH)
    if args.fixture_self_check:
        print(json.dumps(fixture_self_check(plan), sort_keys=True, indent=2))
        return 0
    historical_run_prohibited(plan, args.evidence_root)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
