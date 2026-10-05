#!/usr/bin/env python3
"""Pure outcome-blind operational status/recovery kernel for RND-0055."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "rnd" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from rnd0054_weekly_cli import recompute_ledger  # noqa: E402
from rnd0054_weekly_workflow import plan_next


def assess_operations(document, now_utc, *, sealed_target_exists=False, stage_target_exists=False):
    records, state = recompute_ledger(document)
    plan = plan_next(state, now_utc)

    if sealed_target_exists:
        recovery = "HUMAN_REVIEW_EXISTING_SEALED_TARGET"
        runnable = False
    elif stage_target_exists:
        recovery = "ABANDON_PARTIAL_STAGE_DO_NOT_ADVANCE_LEDGER"
        runnable = False
    elif plan["status"] == "NOT_YET_RUNNABLE":
        recovery = "WAIT_FOR_WINDOW_CLOSE"
        runnable = False
    elif plan["status"] == "ACCUMULATION_COMPLETE":
        recovery = "READOUT_PENDING_HUMAN_GATE"
        runnable = False
    else:
        recovery = "READY_FOR_GET_ONLY_ACQUISITION"
        runnable = True

    return {
        "tranche_count": state["tranche_count"],
        "cumulative_end_utc": state["cumulative_end_utc"],
        "state": state["state"],
        "plan": plan,
        "runnable": runnable,
        "recovery_action": recovery,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "records_checked": len(records),
    }
