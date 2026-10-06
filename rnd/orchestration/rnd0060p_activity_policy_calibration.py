"""Pure RND-0060P activity-policy calibration primitives.

This module intentionally contains no historical-data loading, strategy simulation,
P&L, broker access, or threshold search. It implements only the frozen empirical
median calibration and veto-only policy semantics.
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Any


class RND0060PCalibrationError(ValueError):
    pass


ADMIT = "ADMIT"
VETO = "VETO"
DEFER = "DEFER"


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RND0060PCalibrationError(f"{name} must be numeric")
    x = float(value)
    if not math.isfinite(x):
        raise RND0060PCalibrationError(f"{name} must be finite")
    return x


def empirical_median(activity_states: Iterable[float]) -> float:
    """Return the deterministic empirical median of a non-empty finite sample."""
    values = [_finite_number(v, "activity_state") for v in activity_states]
    if not values:
        raise RND0060PCalibrationError("calibration sample must be non-empty")
    values.sort()
    n = len(values)
    mid = n // 2
    if n % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def calibrate(activity_states: Iterable[float]) -> Mapping[str, Any]:
    """Calibrate exactly one cut-point; accepts no outcome/objective arguments."""
    values = list(activity_states)
    cutpoint = empirical_median(values)
    return {
        "contract_version": "RND0060P-calibration-v1",
        "calibration_method": "EMPIRICAL_MEDIAN",
        "eligible_observation_count": len(values),
        "activity_cutpoint": cutpoint,
        "admit_operator": ">=",
        "veto_operator": "<",
        "threshold_search": False,
        "parameter_search": False,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def decide(activity_state: float | None, activity_cutpoint: float) -> str:
    """Apply the frozen veto-only policy semantics.

    Missing state fails closed to DEFER. Invalid finite values are rejected.
    """
    cutpoint = _finite_number(activity_cutpoint, "activity_cutpoint")
    if activity_state is None:
        return DEFER
    state = _finite_number(activity_state, "activity_state")
    return ADMIT if state >= cutpoint else VETO
