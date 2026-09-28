#!/usr/bin/env python3
"""Pure local contract checks for governed quantitative research declarations."""

from __future__ import annotations

import copy
import re
from datetime import datetime
from math import prod


VERSION = "RND-quant-research-v0.1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

TOP_FIELDS = {
    "contract_version", "experiment_id", "objective", "strategy_family",
    "data_snapshots", "windows", "search_space", "declared_trial_count",
    "metrics", "simulator", "validation", "authority",
}
SNAPSHOT_FIELDS = {
    "snapshot_id", "sha256", "provider", "symbol", "timeframe",
    "price_components", "start_utc", "end_utc", "complete", "provenance",
}
WINDOW_FIELDS = {"start_utc", "end_utc"}
SIMULATOR = {
    "event_driven": True,
    "explicit_entries_exits": True,
    "bid_ask_costs": True,
    "overlapping_positions": True,
    "mark_to_market": True,
    "currency_exposure": True,
    "synthetic_return_clipping": False,
    "future_bar_access": False,
}
VALIDATION = {
    "chronological_oos": True,
    "parameter_perturbation": True,
    "subperiod_regime_analysis": True,
    "multiple_testing_accounting": True,
    "dependence_aware_resampling": True,
    "pbo_ready": True,
    "dsr_ready": True,
}
AUTHORITY = {
    "strategy_selection": False,
    "broker_writes": False,
    "automatic_merge": False,
    "automatic_promotion": False,
    "capital_authority": False,
    "human_review_required": True,
}


class QuantResearchContractError(ValueError):
    pass


def _exact_fields(value, expected, role):
    if not isinstance(value, dict):
        raise QuantResearchContractError(f"{role}: expected object")
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise QuantResearchContractError(
            f"{role}: field mismatch missing={missing} extra={extra}"
        )


def _text(value, role):
    if not isinstance(value, str) or not value.strip():
        raise QuantResearchContractError(f"{role}: expected non-empty string")
    return value.strip()


def _utc(value, role):
    value = _text(value, role)
    if not value.endswith("Z"):
        raise QuantResearchContractError(f"{role}: UTC timestamp must end in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise QuantResearchContractError(f"{role}: invalid UTC timestamp") from exc


def _window(value, role):
    _exact_fields(value, WINDOW_FIELDS, role)
    start = _utc(value["start_utc"], role + ".start_utc")
    end = _utc(value["end_utc"], role + ".end_utc")
    if start >= end:
        raise QuantResearchContractError(f"{role}: start must precede end")
    return start, end


def _snapshot(value, index):
    role = f"data_snapshots[{index}]"
    _exact_fields(value, SNAPSHOT_FIELDS, role)
    _text(value["snapshot_id"], role + ".snapshot_id")
    digest = value["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise QuantResearchContractError(f"{role}.sha256: invalid SHA-256")
    for field in ("provider", "symbol", "timeframe", "provenance"):
        _text(value[field], role + "." + field)
    components = value["price_components"]
    if (
        not isinstance(components, list)
        or not components
        or len(set(components)) != len(components)
        or not all(x in {"bid", "ask", "mid"} for x in components)
    ):
        raise QuantResearchContractError(
            f"{role}.price_components: expected unique bid/ask/mid values"
        )
    if not {"bid", "ask"}.issubset(set(components)):
        raise QuantResearchContractError(
            f"{role}: execution-grade baseline requires bid and ask"
        )
    if value["complete"] is not True:
        raise QuantResearchContractError(f"{role}: snapshot must be complete")
    start = _utc(value["start_utc"], role + ".start_utc")
    end = _utc(value["end_utc"], role + ".end_utc")
    if start >= end:
        raise QuantResearchContractError(f"{role}: start must precede end")
    return start, end


def validate_research_declaration(value):
    """Validate a pre-result research declaration; grant no trading authority."""
    _exact_fields(value, TOP_FIELDS, "research declaration")
    if value["contract_version"] != VERSION:
        raise QuantResearchContractError("unsupported contract_version")
    _text(value["experiment_id"], "experiment_id")
    _text(value["objective"], "objective")
    _text(value["strategy_family"], "strategy_family")

    snapshots = value["data_snapshots"]
    if not isinstance(snapshots, list) or not snapshots:
        raise QuantResearchContractError("data_snapshots: expected non-empty list")
    snapshot_ranges = []
    for index, snapshot in enumerate(snapshots):
        snapshot_ranges.append(_snapshot(snapshot, index))
    ids = [x["snapshot_id"] for x in snapshots]
    if len(set(ids)) != len(ids):
        raise QuantResearchContractError("data_snapshots: duplicate snapshot_id")

    windows = value["windows"]
    if not isinstance(windows, dict) or set(windows) != {
        "development", "validation", "test"
    }:
        raise QuantResearchContractError(
            "windows: require development, validation and test"
        )
    dev = _window(windows["development"], "windows.development")
    val = _window(windows["validation"], "windows.validation")
    test = _window(windows["test"], "windows.test")
    if dev[1] > val[0] or val[1] > test[0]:
        raise QuantResearchContractError(
            "windows: chronological partitions overlap or are out of order"
        )
    for index, (start, end) in enumerate(snapshot_ranges):
        if start > dev[0] or end < test[1]:
            raise QuantResearchContractError(
                f"data_snapshots[{index}]: snapshot does not cover declared windows"
            )

    search = value["search_space"]
    if not isinstance(search, dict):
        raise QuantResearchContractError("search_space: expected object")
    sizes = []
    for name, choices in search.items():
        _text(name, "search_space parameter")
        if not isinstance(choices, list) or not choices:
            raise QuantResearchContractError(
                f"search_space.{name}: expected non-empty choice list"
            )
        try:
            canonical_choices = [
                json.dumps(choice, sort_keys=True, separators=(",", ":"))
                for choice in choices
            ]
        except (TypeError, ValueError) as exc:
            raise QuantResearchContractError(
                f"search_space.{name}: choices must be JSON values"
            ) from exc
        if len(set(canonical_choices)) != len(canonical_choices):
            raise QuantResearchContractError(
                f"search_space.{name}: duplicate choices are not distinct trials"
            )
        sizes.append(len(choices))
    expected_trials = prod(sizes) if sizes else 1
    trials = value["declared_trial_count"]
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1:
        raise QuantResearchContractError("declared_trial_count: invalid")
    if trials != expected_trials:
        raise QuantResearchContractError(
            "declared_trial_count does not match declared search space"
        )

    metrics = value["metrics"]
    if (
        not isinstance(metrics, list)
        or not metrics
        or len(set(metrics)) != len(metrics)
        or not all(isinstance(x, str) and x.strip() for x in metrics)
    ):
        raise QuantResearchContractError("metrics: expected unique non-empty strings")

    if value["simulator"] != SIMULATOR:
        raise QuantResearchContractError(
            "simulator: fail-closed baseline semantics mismatch"
        )
    if value["validation"] != VALIDATION:
        raise QuantResearchContractError(
            "validation: required validation plan mismatch"
        )
    if value["authority"] != AUTHORITY:
        raise QuantResearchContractError(
            "authority: research declaration cannot expand authority"
        )

    return copy.deepcopy(value)
