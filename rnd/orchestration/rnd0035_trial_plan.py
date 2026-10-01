#!/usr/bin/env python3
"""Fail-closed validator for the pre-outcome RND-0035 trial plan.

This module validates research authority and the frozen numerical matrix only.
It does not load market evidence or execute strategy outcomes.
"""

from __future__ import annotations

import json
from pathlib import Path

EXPECTED_FOUNDATION = "ee163e375dfc2403b34f41f83a962267b23bda69"
EXPECTED_YEARS = [2015, 2016, 2017, 2018, 2019]
EXPECTED_SYMBOLS = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]
EXPECTED_FAMILIES = {
    "A_LOCAL_PARAMETER",
    "B_CONCENTRATION",
    "C_SESSION",
    "D_COST_SLIPPAGE",
    "E_GAP_POLICY",
    "F_EXECUTION",
    "G_DEPENDENCE_RESAMPLING",
}
EXPECTED_VARIANT_COUNTS = {
    "reference": 1,
    "family_A": 21,
    "family_C": 4,
    "family_D": 4,
    "family_E": 2,
    "family_F": 4,
    "total_including_reference": 36,
}


class RND0035PlanError(ValueError):
    pass


def load_plan(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RND0035PlanError("trial plan unreadable or invalid JSON") from exc
    return validate_plan(plan)


def _require(condition, message):
    if not condition:
        raise RND0035PlanError(message)


def validate_plan(plan):
    _require(isinstance(plan, dict), "plan must be a mapping")
    _require(plan.get("task_id") == "RND-0035", "wrong task id")
    _require(plan.get("foundation_sha") == EXPECTED_FOUNDATION, "wrong foundation")
    _require(plan.get("plan_status") == "NUMERICAL_MATRIX_FROZEN_IMPLEMENTATION_PENDING", "wrong plan status")
    _require(plan.get("authorized_years") == EXPECTED_YEARS, "authorized years changed")
    _require(plan.get("authorized_symbols") == EXPECTED_SYMBOLS, "authorized symbols changed")

    # Pre-outcome authority must fail closed.
    for key in ("outcomes_authorized", "validation_open", "final_test_open", "strategy_selection", "broker_writes", "capital_authority"):
        _require(plan.get(key) is False, f"{key} must be false")
    _require(plan.get("promotion_authority") == "HUMAN_ONLY", "promotion authority changed")

    principles = plan.get("design_principles", {})
    _require(principles.get("parameter_method") == "ONE_FACTOR_AT_A_TIME_AROUND_R000", "parameter method changed")
    _require(principles.get("no_cartesian_parameter_grid") is True, "cartesian parameter search prohibited")
    _require(principles.get("no_best_variant_selection") is True, "variant selection prohibited")
    _require(principles.get("all_declared_trials_count") is True, "trial accounting weakened")

    families = plan.get("families", {})
    _require(set(families) == EXPECTED_FAMILIES, "attack-family set changed")
    for name, family in families.items():
        _require(family.get("grid_frozen") is True, f"{name}: grid not frozen")
        _require(family.get("outcomes_authorized") is False, f"{name}: outcomes must remain closed")

    # Trial IDs must be globally unique across strategy-variant families.
    ids = ["R000"]
    for name in ("A_LOCAL_PARAMETER", "C_SESSION", "D_COST_SLIPPAGE", "E_GAP_POLICY", "F_EXECUTION"):
        ids.extend(x.get("trial_id") for x in families[name].get("trials", []))
    _require(None not in ids, "trial id missing")
    _require(len(ids) == len(set(ids)), "duplicate trial id")

    counts = plan.get("declared_strategy_variant_trials")
    _require(counts == EXPECTED_VARIANT_COUNTS, "declared variant counts changed")
    actual = 1 + sum(len(families[name].get("trials", [])) for name in (
        "A_LOCAL_PARAMETER", "C_SESSION", "D_COST_SLIPPAGE", "E_GAP_POLICY", "F_EXECUTION"
    ))
    _require(actual == EXPECTED_VARIANT_COUNTS["total_including_reference"], "variant count mismatch")

    bootstrap = families["G_DEPENDENCE_RESAMPLING"]
    _require(bootstrap.get("primary_method") == "STATIONARY_BOOTSTRAP", "primary resampler changed")
    _require(bootstrap.get("replications_per_configuration") == 10000, "bootstrap replication count changed")
    _require(bootstrap.get("seeds") == [1729, 271828, 314159], "bootstrap seeds changed")
    _require(bootstrap.get("expected_block_lengths_trades") == [10, 20, 40], "bootstrap blocks changed")
    _require(bootstrap.get("configuration_count") == 9, "bootstrap configuration count changed")
    _require(plan.get("declared_resampling_configurations") == 9, "declared resampling count changed")

    gate = plan.get("execution_gate", {})
    _require(gate.get("new_outcomes_may_run") is False, "outcome gate opened prematurely")
    _require(len(gate.get("requirements_before_opening", [])) >= 7, "outcome gate requirements incomplete")
    return plan
