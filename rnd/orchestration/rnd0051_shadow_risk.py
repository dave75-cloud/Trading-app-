#!/usr/bin/env python3
"""Pure fixture-only shadow risk decision kernel for RND-0051.

No broker calls, credentials, order construction, capital allocation, strategy
execution, or market-data access.
"""
from datetime import datetime, timezone

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
SIDES = ("LONG", "SHORT", "FLAT")


def _utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("UTC Z timestamp required")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def evaluate_shadow_intent(intent, policy, seen_intent_ids=()):
    """Return a deterministic shadow-only decision and reason list."""
    reasons = []
    if not isinstance(intent, dict) or not isinstance(policy, dict):
        return {"decision": "SHADOW_REJECT", "reasons": ["INVALID_INPUT"]}

    if intent.get("candidate_fingerprint") != CANDIDATE_FINGERPRINT:
        reasons.append("CANDIDATE_MISMATCH")
    if intent.get("symbol") not in SYMBOLS:
        reasons.append("SYMBOL_NOT_ALLOWED")
    if intent.get("side") not in SIDES:
        reasons.append("SIDE_NOT_ALLOWED")
    if intent.get("source_state") != "SHADOW_FIXTURE":
        reasons.append("SOURCE_STATE_NOT_SHADOW_FIXTURE")
    if intent.get("broker_writes") is not False:
        reasons.append("BROKER_WRITES_NOT_FALSE")
    if intent.get("capital_authority") is not False:
        reasons.append("CAPITAL_AUTHORITY_NOT_FALSE")
    if policy.get("kill_switch") is True:
        reasons.append("KILL_SWITCH_ACTIVE")

    intent_id = intent.get("intent_id")
    if not isinstance(intent_id, str) or not intent_id:
        reasons.append("INTENT_ID_INVALID")
    elif intent_id in set(seen_intent_ids):
        reasons.append("DUPLICATE_INTENT")

    try:
        evidence_time = _utc(intent.get("evidence_time_utc"))
        decision_time = _utc(intent.get("decision_time_utc"))
        if decision_time < evidence_time:
            reasons.append("DECISION_PRECEDES_EVIDENCE")
        max_age = int(policy.get("max_evidence_age_seconds"))
        if max_age < 0 or (decision_time - evidence_time).total_seconds() > max_age:
            reasons.append("STALE_EVIDENCE")
    except Exception:
        reasons.append("TIMESTAMP_INVALID")

    units = intent.get("requested_units")
    if intent.get("side") in ("LONG", "SHORT"):
        if not isinstance(units, (int, float)) or isinstance(units, bool) or units <= 0:
            reasons.append("REQUESTED_UNITS_INVALID")
        elif float(units) > float(policy.get("max_fixture_units", -1)):
            reasons.append("FIXTURE_UNITS_LIMIT")

    if float(policy.get("projected_gross_fixture_exposure", 0)) > float(policy.get("max_gross_fixture_exposure", -1)):
        reasons.append("GROSS_EXPOSURE_LIMIT")
    if float(policy.get("projected_currency_leg_fixture_exposure", 0)) > float(policy.get("max_currency_leg_fixture_exposure", -1)):
        reasons.append("CURRENCY_LEG_LIMIT")

    return {
        "decision": "SHADOW_ACCEPT" if not reasons else "SHADOW_REJECT",
        "reasons": reasons,
        "broker_writes": False,
        "capital_authority": False,
        "execution_authority": False,
    }
