#!/usr/bin/env python3
"""Pure control-plane state machine for RND-0052.

No broker, network, credential, order, capital, or strategy execution capability.
"""

STATES = {
    "RESEARCH_FROZEN",
    "PROSPECTIVE_ACCUMULATING",
    "VALIDATION_INCONCLUSIVE_STRUCTURAL",
    "VALIDATION_REJECTED",
    "VALIDATION_SUPPORTED",
    "SHADOW_ELIGIBLE",
    "SHADOW_ACTIVE",
    "RISK_REVIEW_REQUIRED",
    "EXECUTION_ELIGIBLE",
}

HUMAN_ONLY = {
    ("RESEARCH_FROZEN", "PROSPECTIVE_ACCUMULATING"),
    ("PROSPECTIVE_ACCUMULATING", "VALIDATION_INCONCLUSIVE_STRUCTURAL"),
    ("PROSPECTIVE_ACCUMULATING", "VALIDATION_REJECTED"),
    ("PROSPECTIVE_ACCUMULATING", "VALIDATION_SUPPORTED"),
    ("VALIDATION_SUPPORTED", "SHADOW_ELIGIBLE"),
    ("SHADOW_ELIGIBLE", "SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE", "RISK_REVIEW_REQUIRED"),
    ("RISK_REVIEW_REQUIRED", "EXECUTION_ELIGIBLE"),
    ("VALIDATION_INCONCLUSIVE_STRUCTURAL", "PROSPECTIVE_ACCUMULATING"),
}

AUTHORITY_FIELDS = (
    "strategy_evaluation_authorized",
    "shadow_authorized",
    "risk_policy_authorized",
    "broker_writes_authorized",
    "capital_authority",
    "live_environment_authorized",
)


def transition(current_state, next_state, *, human_authorized=False):
    if current_state not in STATES or next_state not in STATES:
        return {"allowed": False, "reason": "UNKNOWN_STATE"}
    if current_state == "VALIDATION_REJECTED":
        return {"allowed": False, "reason": "REJECTED_CANDIDATE_TERMINAL"}
    edge = (current_state, next_state)
    if edge not in HUMAN_ONLY:
        return {"allowed": False, "reason": "TRANSITION_NOT_ALLOWED"}
    if not human_authorized:
        return {"allowed": False, "reason": "HUMAN_AUTHORIZATION_REQUIRED"}
    return {"allowed": True, "reason": "HUMAN_AUTHORIZED_TRANSITION", "state": next_state}


def effective_authority(state, authority):
    if state not in STATES or not isinstance(authority, dict):
        return {field: False for field in AUTHORITY_FIELDS}
    out = {field: authority.get(field) is True for field in AUTHORITY_FIELDS}

    # Fail closed by lifecycle stage. State never grants authority by itself.
    if state in {"RESEARCH_FROZEN", "PROSPECTIVE_ACCUMULATING", "VALIDATION_INCONCLUSIVE_STRUCTURAL", "VALIDATION_REJECTED", "VALIDATION_SUPPORTED"}:
        out["shadow_authorized"] = False
        out["risk_policy_authorized"] = False
        out["broker_writes_authorized"] = False
        out["capital_authority"] = False
        out["live_environment_authorized"] = False
    if state != "EXECUTION_ELIGIBLE":
        out["broker_writes_authorized"] = False
        out["capital_authority"] = False
        out["live_environment_authorized"] = False
    return out
