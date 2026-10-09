"""Pure RND-0060R prospective confirmation accumulator/provenance kernel.

No broker access, historical acquisition, strategy simulation, P&L, or threshold search.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import math
from typing import Any, Iterable

CUTPOINT = 0.0003990789273159821
POLICY_VERSION = "RND0060P-calibration-v1"
ADMIT = "ADMIT"
VETO = "VETO"
DEFER = "DEFER"
ALLOWED_DECISIONS = {ADMIT, VETO, DEFER}
FORBIDDEN_SOURCE_KINDS = {
    "HISTORICAL_BACKFILL",
    "VALIDATION_2021_2022",
    "RESERVED_FINAL_2023_2024",
    "Q003_PROSPECTIVE_OUTCOME",
}
MIN_CALENDAR_DAYS = 180
MIN_NON_DEFER = 100
FORWARD_WINDOW = timedelta(minutes=30)


class RND0060RAccumulatorError(ValueError):
    pass


def _req(ok: bool, message: str) -> None:
    if not ok:
        raise RND0060RAccumulatorError(message)


def _utc(value: Any, name: str) -> datetime:
    _req(isinstance(value, str) and value.endswith("Z"), f"{name}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060RAccumulatorError(f"{name}: invalid timestamp") from exc
    _req(dt.tzinfo is not None and dt.utcoffset() == timedelta(0), f"{name}: UTC required")
    return dt


def _finite(value: Any, name: str, nonnegative: bool = False) -> float:
    _req(not isinstance(value, bool) and isinstance(value, (int, float)), f"{name}: finite number required")
    out = float(value)
    _req(math.isfinite(out), f"{name}: finite number required")
    if nonnegative:
        _req(out >= 0.0, f"{name}: non-negative number required")
    return out


def frozen_decision(activity_state: float | None, cutpoint: float = CUTPOINT) -> str:
    cp = _finite(cutpoint, "cutpoint")
    _req(cp == CUTPOINT, "frozen cutpoint mismatch")
    if activity_state is None:
        return DEFER
    state = _finite(activity_state, "activity_state", nonnegative=True)
    return ADMIT if state >= cp else VETO


def validate_observation(record: dict[str, Any], prospective_start_utc: str) -> dict[str, Any]:
    _req(isinstance(record, dict), "record: mapping required")
    required = {
        "observation_utc", "available_at_utc", "source_kind", "source_id",
        "policy_version", "activity_cutpoint", "activity_state", "decision",
        "market_wide_movement_to_friction", "per_symbol_movement_to_friction",
    }
    _req(required.issubset(record), "record: required fields missing")

    start = _utc(prospective_start_utc, "prospective_start_utc")
    obs = _utc(record["observation_utc"], "observation_utc")
    avail = _utc(record["available_at_utc"], "available_at_utc")
    _req(obs >= start, "pre-start observation prohibited")
    _req(avail >= obs + FORWARD_WINDOW, "observation available before forward window complete")

    source_kind = record["source_kind"]
    _req(isinstance(source_kind, str) and source_kind, "source_kind: non-empty string required")
    _req(source_kind not in FORBIDDEN_SOURCE_KINDS, "forbidden source kind")
    _req(isinstance(record["source_id"], str) and record["source_id"], "source_id: non-empty string required")
    _req(record["policy_version"] == POLICY_VERSION, "policy version mismatch")
    cp = _finite(record["activity_cutpoint"], "activity_cutpoint")
    _req(cp == CUTPOINT, "activity cutpoint mismatch")

    state_raw = record["activity_state"]
    expected = frozen_decision(state_raw, cp)
    _req(record["decision"] in ALLOWED_DECISIONS, "invalid decision")
    _req(record["decision"] == expected, "decision inconsistent with frozen policy")

    market = _finite(record["market_wide_movement_to_friction"], "market_wide_movement_to_friction", nonnegative=True)
    per_symbol = record["per_symbol_movement_to_friction"]
    _req(isinstance(per_symbol, dict) and set(per_symbol) == {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}, "exact four-symbol response required")
    checked_symbol = {s: _finite(v, f"{s}_movement_to_friction", nonnegative=True) for s, v in per_symbol.items()}

    return {
        "observation_utc": obs.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "available_at_utc": avail.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_kind": source_kind,
        "source_id": record["source_id"],
        "policy_version": POLICY_VERSION,
        "activity_cutpoint": CUTPOINT,
        "activity_state": None if state_raw is None else float(state_raw),
        "decision": expected,
        "market_wide_movement_to_friction": market,
        "per_symbol_movement_to_friction": checked_symbol,
    }


def accumulate(records: Iterable[dict[str, Any]], prospective_start_utc: str) -> dict[str, Any]:
    start = _utc(prospective_start_utc, "prospective_start_utc")
    validated = [validate_observation(r, prospective_start_utc) for r in records]
    timestamps = [r["observation_utc"] for r in validated]
    _req(timestamps == sorted(timestamps), "observations must be ordered")
    _req(len(timestamps) == len(set(timestamps)), "duplicate observation timestamp")
    non_defer = sum(r["decision"] != DEFER for r in validated)
    latest_available = max((_utc(r["available_at_utc"], "available_at_utc") for r in validated), default=start)
    elapsed_days = (latest_available - start).total_seconds() / 86400.0
    eligible = elapsed_days >= MIN_CALENDAR_DAYS and non_defer >= MIN_NON_DEFER
    return {
        "contract_version": "RND0060R-accumulator-v1",
        "prospective_start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "record_count": len(validated),
        "non_defer_count": non_defer,
        "elapsed_calendar_days": elapsed_days,
        "readout_eligible": eligible,
        "minimum_calendar_days": MIN_CALENDAR_DAYS,
        "minimum_non_defer_observations": MIN_NON_DEFER,
        "records": validated,
        "economic_group_summary_exposed": False,
        "trade_simulation": False,
        "pnl": False,
        "strategy_interaction": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "q003_prospective_outcomes_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
