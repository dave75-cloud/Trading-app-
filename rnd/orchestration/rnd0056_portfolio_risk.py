#!/usr/bin/env python3
"""Deterministic fixture-only portfolio shadow risk engine for RND-0056."""

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
PAIR_CURRENCIES = {
    "AUDUSD": ("AUD", "USD"),
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
}


def _signed_units(side, units):
    if side == "LONG":
        return float(units)
    if side == "SHORT":
        return -float(units)
    if side == "FLAT":
        return 0.0
    raise ValueError("invalid side")


def _currency_legs(positions):
    legs = {}
    for symbol, signed in positions.items():
        base, quote = PAIR_CURRENCIES[symbol]
        legs[base] = legs.get(base, 0.0) + signed
        legs[quote] = legs.get(quote, 0.0) - signed
    return legs


def evaluate_portfolio_intent(intent, positions, policy, seen_intent_ids=()):
    reasons = []
    if not isinstance(intent, dict) or not isinstance(positions, dict) or not isinstance(policy, dict):
        return {"decision": "SHADOW_REJECT", "reasons": ["INVALID_INPUT"], "broker_writes": False, "capital_authority": False, "execution_authority": False}

    if intent.get("candidate_fingerprint") != CANDIDATE_FINGERPRINT:
        reasons.append("CANDIDATE_MISMATCH")
    symbol = intent.get("symbol")
    if symbol not in SYMBOLS:
        reasons.append("SYMBOL_NOT_ALLOWED")
    side = intent.get("side")
    if side not in ("LONG", "SHORT", "FLAT"):
        reasons.append("SIDE_NOT_ALLOWED")
    if intent.get("broker_writes") is not False or intent.get("capital_authority") is not False:
        reasons.append("AUTHORITY_ESCALATION")
    if policy.get("kill_switch") is True:
        reasons.append("KILL_SWITCH_ACTIVE")

    intent_id = intent.get("intent_id")
    if not isinstance(intent_id, str) or not intent_id:
        reasons.append("INTENT_ID_INVALID")
    elif intent_id in set(seen_intent_ids):
        reasons.append("DUPLICATE_INTENT")

    units = intent.get("requested_units", 0)
    if isinstance(units, bool) or not isinstance(units, (int, float)) or units < 0:
        reasons.append("REQUESTED_UNITS_INVALID")
        units = 0
    if float(units) > float(policy.get("max_intent_units", -1)):
        reasons.append("INTENT_UNITS_LIMIT")

    clean_positions = {s: float(positions.get(s, 0.0)) for s in SYMBOLS}
    projected = dict(clean_positions)
    if symbol in SYMBOLS and side in ("LONG", "SHORT", "FLAT"):
        projected[symbol] = _signed_units(side, units)

    max_pair = float(policy.get("max_pair_abs_units", -1))
    if any(abs(v) > max_pair for v in projected.values()):
        reasons.append("PAIR_POSITION_LIMIT")

    gross = sum(abs(v) for v in projected.values())
    net = abs(sum(projected.values()))
    active_pairs = sum(1 for v in projected.values() if v != 0)
    legs = _currency_legs(projected)
    max_leg = max([abs(v) for v in legs.values()] or [0.0])

    if gross > float(policy.get("max_gross_units", -1)):
        reasons.append("GROSS_EXPOSURE_LIMIT")
    if net > float(policy.get("max_net_units", -1)):
        reasons.append("NET_EXPOSURE_LIMIT")
    if active_pairs > int(policy.get("max_active_pairs", -1)):
        reasons.append("ACTIVE_PAIR_LIMIT")
    if max_leg > float(policy.get("max_currency_leg_units", -1)):
        reasons.append("CURRENCY_LEG_LIMIT")

    return {
        "decision": "SHADOW_ACCEPT" if not reasons else "SHADOW_REJECT",
        "reasons": reasons,
        "projected_positions": projected,
        "projected_currency_legs": legs,
        "projected_gross_units": gross,
        "projected_net_units": net,
        "broker_writes": False,
        "capital_authority": False,
        "execution_authority": False,
    }
