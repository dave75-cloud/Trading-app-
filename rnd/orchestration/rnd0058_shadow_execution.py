#!/usr/bin/env python3
"""Pure fixture-only shadow execution/reconciliation state machine for RND-0058."""

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
TERMINAL = {"SHADOW_FILLED", "SHADOW_CANCELLED", "SHADOW_REJECTED", "RECONCILED"}


class ShadowExecutionError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise ShadowExecutionError(message)


def new_shadow_order(intent_receipt, risk_receipt):
    _req(isinstance(intent_receipt, dict) and isinstance(risk_receipt, dict), "receipts required")
    _req(intent_receipt.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "intent candidate mismatch")
    _req(risk_receipt.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "risk candidate mismatch")
    _req(intent_receipt.get("intent_id") == risk_receipt.get("intent_id"), "intent/risk binding mismatch")
    _req(intent_receipt.get("decision") == "SHADOW_ACCEPT", "accepted shadow intent required")
    _req(risk_receipt.get("decision") == "SHADOW_ACCEPT", "accepted risk decision required")
    units = float(intent_receipt.get("requested_units", 0))
    _req(units > 0, "positive fixture units required")
    return {
        "shadow_order_id": "shadow:" + intent_receipt["intent_id"],
        "intent_id": intent_receipt["intent_id"],
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "state": "SHADOW_ORDER_PLANNED",
        "planned_units": units,
        "filled_units": 0.0,
        "position_delta_units": 0.0,
        "seen_event_ids": [],
        "broker_writes": False,
        "capital_authority": False,
        "execution_authority": False,
    }


def apply_event(order, event):
    _req(isinstance(order, dict) and isinstance(event, dict), "order/event mapping required")
    _req(order.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate mismatch")
    _req(order.get("broker_writes") is False and order.get("capital_authority") is False, "authority drift")
    event_id = event.get("event_id")
    _req(isinstance(event_id, str) and event_id, "event id required")
    _req(event_id not in set(order.get("seen_event_ids", [])), "duplicate event")
    kind = event.get("kind")
    state = order.get("state")
    out = dict(order)
    seen = list(order.get("seen_event_ids", [])) + [event_id]

    if kind == "ACK":
        _req(state == "SHADOW_ORDER_PLANNED", "ack state invalid")
        out["state"] = "SHADOW_ACKNOWLEDGED"
    elif kind == "FILL":
        _req(state in {"SHADOW_ACKNOWLEDGED", "SHADOW_PARTIAL"}, "fill requires acknowledgement")
        qty = float(event.get("units", 0))
        _req(qty > 0, "positive fill units required")
        total = float(order.get("filled_units", 0)) + qty
        _req(total <= float(order["planned_units"]), "fill exceeds planned units")
        out["filled_units"] = total
        out["position_delta_units"] = total
        out["state"] = "SHADOW_FILLED" if total == float(order["planned_units"]) else "SHADOW_PARTIAL"
    elif kind == "CANCEL":
        _req(state in {"SHADOW_ORDER_PLANNED", "SHADOW_ACKNOWLEDGED", "SHADOW_PARTIAL"}, "cancel state invalid")
        out["state"] = "SHADOW_CANCELLED"
    elif kind == "REJECT":
        _req(state in {"SHADOW_ORDER_PLANNED", "SHADOW_ACKNOWLEDGED"}, "reject state invalid")
        out["state"] = "SHADOW_REJECTED"
    elif kind == "RECONCILE":
        _req(state in {"SHADOW_FILLED", "SHADOW_CANCELLED", "SHADOW_REJECTED"}, "reconciliation requires terminal shadow state")
        _req(float(event.get("filled_units", -1)) == float(order.get("filled_units", 0)), "reconciliation fill mismatch")
        _req(float(event.get("position_delta_units", -1)) == float(order.get("position_delta_units", 0)), "reconciliation position mismatch")
        out["state"] = "RECONCILED"
    else:
        raise ShadowExecutionError("unknown event kind")

    out["seen_event_ids"] = seen
    out["broker_writes"] = False
    out["capital_authority"] = False
    out["execution_authority"] = False
    return out
