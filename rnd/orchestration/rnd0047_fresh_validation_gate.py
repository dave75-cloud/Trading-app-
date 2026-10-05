#!/usr/bin/env python3
"""RND-0047 prospective fresh-validation acquisition gate.

Pure governance/validation code. It does not call OANDA, evaluate Q003, or
open reserved-final evidence. Actual market-data acquisition requires a later
human authorization that changes the declaration state.
"""
from __future__ import annotations

from datetime import datetime, timezone

CANDIDATE_ID = "Q003"
CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
FRESH_START_UTC = "2026-10-05T07:25:00Z"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
TIMEFRAME = "M5"
PRICE_COMPONENTS = ("bid", "ask", "mid")
IMPLEMENTATION_STATE = "IMPLEMENTATION_ONLY"
ACQUISITION_STATE = "ACQUISITION_AUTHORIZED"


class RND0047GateError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0047GateError(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0047GateError(f"{role}: invalid timestamp") from exc
    _req(dt.tzinfo is not None, f"{role}: timezone required")
    _req(int(dt.timestamp()) % 300 == 0, f"{role}: M5 boundary required")
    return dt.astimezone(timezone.utc)


def validate_declaration(value, *, require_acquisition_authority=False):
    _req(isinstance(value, dict), "declaration: mapping required")
    _req(value.get("task_id") == "RND-0047", "task_id mismatch")
    _req(value.get("candidate_id") == CANDIDATE_ID, "candidate id mismatch")
    _req(value.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(value.get("timeframe") == TIMEFRAME, "timeframe changed")
    _req(tuple(value.get("symbols", ())) == SYMBOLS, "symbol universe changed")
    _req(tuple(value.get("price_components", ())) == PRICE_COMPONENTS, "price components changed")
    _req(value.get("complete_candles_only") is True, "incomplete candles prohibited")
    _req(value.get("synthetic_fill") is False, "synthetic fill prohibited")
    _req(value.get("strategy_evaluation") is False, "strategy evaluation prohibited in RND-0047")
    _req(value.get("reserved_final_access") is False, "reserved-final access prohibited")
    _req(value.get("broker_writes") is False, "broker writes prohibited")
    _req(value.get("capital_authority") is False, "capital authority prohibited")

    state = value.get("state")
    _req(state in (IMPLEMENTATION_STATE, ACQUISITION_STATE), "invalid declaration state")
    if require_acquisition_authority:
        _req(state == ACQUISITION_STATE, "actual acquisition not human-authorized")
    else:
        _req(state == IMPLEMENTATION_STATE, "implementation declaration unexpectedly opened")

    window = value.get("acquisition_window")
    _req(isinstance(window, dict), "acquisition_window required")
    start = _utc(window.get("start_utc"), "start_utc")
    end = _utc(window.get("end_utc"), "end_utc")
    fresh = _utc(FRESH_START_UTC, "fresh_start")
    _req(start >= fresh, "pre-freeze evidence prohibited")
    _req(end > start, "end must be after start")

    # Reserved-final evidence is entirely before the prospective fresh boundary;
    # this explicit check guards against accidental window substitution.
    _req(start.year >= 2026, "reserved-final/historical window prohibited")
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "start_utc": window["start_utc"],
        "end_utc": window["end_utc"],
        "state": state,
    }


def build_implementation_declaration(end_utc):
    end = _utc(end_utc, "end_utc")
    fresh = _utc(FRESH_START_UTC, "fresh_start")
    _req(end > fresh, "end must be after fresh start")
    return {
        "task_id": "RND-0047",
        "state": IMPLEMENTATION_STATE,
        "candidate_id": CANDIDATE_ID,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "timeframe": TIMEFRAME,
        "price_components": list(PRICE_COMPONENTS),
        "complete_candles_only": True,
        "synthetic_fill": False,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "acquisition_window": {
            "start_utc": FRESH_START_UTC,
            "end_utc": end_utc,
        },
    }
