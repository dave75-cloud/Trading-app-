#!/usr/bin/env python3
"""Pure generic veto-only activity-admissibility contract for RND-0060N."""
from __future__ import annotations

import math
from copy import deepcopy

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
POLICIES = ("ADMIT", "VETO", "DEFER")


class RND0060NError(ValueError):
    pass


def _require(ok, message):
    if not ok:
        raise RND0060NError(message)


def _finite_positive(value, role):
    _require(not isinstance(value, bool), f"{role}: positive finite number required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060NError(f"{role}: positive finite number required") from exc
    _require(math.isfinite(x) and x > 0.0, f"{role}: positive finite number required")
    return x


def _direction(value):
    _require(not isinstance(value, bool), "direction must be exactly -1, 0, or 1")
    try:
        x = int(value)
    except (TypeError, ValueError) as exc:
        raise RND0060NError("direction must be exactly -1, 0, or 1") from exc
    _require(x in (-1, 0, 1) and float(value) == float(x), "direction must be exactly -1, 0, or 1")
    return x


def evaluate_admissibility(*, symbol, direction, activity_state, activity_policy_decision, direction_source_id, signal_metadata=None):
    _require(symbol in SYMBOLS, "unsupported symbol")
    d = _direction(direction)
    state = _finite_positive(activity_state, "activity_state")
    _require(activity_policy_decision in POLICIES, "activity_policy_decision must be ADMIT, VETO, or DEFER")
    _require(isinstance(direction_source_id, str) and direction_source_id.strip(), "direction_source_id required")
    _require("0060H" not in direction_source_id.upper() and "0060L" not in direction_source_id.upper(), "direction source must remain independent of activity research")
    if signal_metadata is None:
        signal_metadata = {}
    _require(isinstance(signal_metadata, dict), "signal_metadata must be mapping")

    if d == 0:
        effective = 0
        deferred = None
    elif activity_policy_decision == "ADMIT":
        effective = d
        deferred = None
    elif activity_policy_decision == "VETO":
        effective = 0
        deferred = None
    else:
        effective = 0
        deferred = d

    return {
        "contract_version": "RND0060N-v1",
        "symbol": symbol,
        "input_direction": d,
        "direction_source_id": direction_source_id,
        "activity_state": state,
        "activity_policy_decision": activity_policy_decision,
        "effective_direction_now": effective,
        "deferred_direction": deferred,
        "signal_metadata": deepcopy(signal_metadata),
        "direction_created_by_activity": False,
        "direction_reversed_by_activity": False,
        "quantity_assigned": False,
        "position_sizing": False,
        "threshold_selected": False,
        "threshold_search": False,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "prospective_candidate_outcomes_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
    }
