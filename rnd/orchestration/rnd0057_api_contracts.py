#!/usr/bin/env python3
"""Pure machine-readable control/API validators for RND-0057."""

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
AUTHORITY_FIELDS = (
    "strategy_evaluation_authorized",
    "shadow_authorized",
    "risk_policy_authorized",
    "broker_writes_authorized",
    "capital_authority",
    "live_environment_authorized",
)
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


class APIContractError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise APIContractError(message)


def candidate_identity(value):
    _req(isinstance(value, dict) and set(value) == {"candidate_id", "candidate_fingerprint", "symbols"}, "candidate identity exact fields required")
    _req(value["candidate_id"] == "Q003", "candidate id mismatch")
    _req(value["candidate_fingerprint"] == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(value["symbols"] == ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"], "symbol universe mismatch")
    return dict(value)


def authority_map(value):
    _req(isinstance(value, dict), "authority mapping required")
    _req(set(value) <= set(AUTHORITY_FIELDS), "unknown authority field")
    return {field: value.get(field) is True for field in AUTHORITY_FIELDS}


def human_authority_receipt(value):
    required = {"receipt_id", "action", "from_state", "to_state", "human_authorized", "candidate_fingerprint"}
    _req(isinstance(value, dict) and set(value) == required, "human authority receipt exact fields required")
    _req(isinstance(value["receipt_id"], str) and value["receipt_id"], "receipt id required")
    _req(isinstance(value["action"], str) and value["action"], "action required")
    _req(value["from_state"] in STATES and value["to_state"] in STATES, "unknown state")
    _req(value["human_authorized"] is True, "explicit human authorization required")
    _req(value["candidate_fingerprint"] == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    return dict(value)


def control_envelope(value):
    required = {"candidate", "state", "authority", "human_receipt", "broker_writes", "capital_authority", "live_environment"}
    _req(isinstance(value, dict) and set(value) == required, "control envelope exact fields required")
    candidate_identity(value["candidate"])
    _req(value["state"] in STATES, "unknown lifecycle state")
    auth = authority_map(value["authority"])
    receipt = value["human_receipt"]
    if receipt is not None:
        human_authority_receipt(receipt)

    # API data cannot manufacture authority from lifecycle state.
    _req(value["broker_writes"] is False, "broker writes must remain false")
    _req(value["capital_authority"] is False, "capital authority must remain false")
    _req(value["live_environment"] is False, "live environment must remain false")

    if value["state"] != "EXECUTION_ELIGIBLE":
        _req(auth["broker_writes_authorized"] is False, "pre-execution broker authority prohibited")
        _req(auth["capital_authority"] is False, "pre-execution capital authority prohibited")
        _req(auth["live_environment_authorized"] is False, "pre-execution live authority prohibited")

    return {
        "candidate": value["candidate"],
        "state": value["state"],
        "authority": auth,
        "human_receipt": receipt,
        "broker_writes": False,
        "capital_authority": False,
        "live_environment": False,
    }
