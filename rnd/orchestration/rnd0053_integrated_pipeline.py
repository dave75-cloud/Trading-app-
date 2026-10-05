#!/usr/bin/env python3
"""Integrated zero-write coordinator for RND-0053.

This module composes the verified RND-0049..0052 kernels without adding network,
file, broker, credential, order, market-data, or strategy-execution capability.
"""

from rnd0049_validation_decision import classify_validation
from rnd0050_weekly_planner import plan_next
from rnd0051_shadow_risk import evaluate_shadow_intent
from rnd0052_control_state import transition, effective_authority


class RND0053PipelineError(ValueError):
    pass


def plan_accumulation(ledger, now_utc):
    """Delegate prospective tranche planning to the verified RND-0050 planner."""
    return plan_next(ledger, now_utc)


def validation_readout(evidence, metrics=None, *, validation_readout_authorized=False):
    """Apply the one-time validation classifier only behind an explicit human gate.

    Structural failure may be diagnosed without opening economic metrics. Any
    structurally eligible economic readout requires explicit authorization.
    """
    structural_keys = (
        "all_post_freeze",
        "all_sha_bound",
        "chronology_valid",
        "all_four_symbols",
        "m5_bid_ask_mid_complete_only",
        "no_synthetic_fill",
        "integrity_verifiers_pass",
        "candidate_mechanics_unchanged",
    )
    structural_pass = isinstance(evidence, dict) and all(evidence.get(k) is True for k in structural_keys)

    if not structural_pass:
        if metrics is not None:
            raise RND0053PipelineError("economic metrics prohibited on structural failure")
        return classify_validation(evidence, None)

    if not validation_readout_authorized:
        if metrics is not None:
            raise RND0053PipelineError("validation readout requires explicit human authorization")
        return {
            "status": "READOUT_ELIGIBLE_PENDING_HUMAN_GATE",
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
        }

    if metrics is None:
        raise RND0053PipelineError("authorized readout requires frozen metrics package")

    return classify_validation(evidence, metrics)


def request_lifecycle_transition(current_state, next_state, *, human_authorized=False):
    """Expose only the verified human-gated RND-0052 transition path."""
    return transition(current_state, next_state, human_authorized=human_authorized)


def evaluate_fixture_shadow(intent, policy, *, lifecycle_state, authority=None, seen_intent_ids=()):
    """Evaluate a fixture-only shadow intent under lifecycle and authority controls."""
    authority = authority or {}
    effective = effective_authority(lifecycle_state, authority)

    if lifecycle_state != "SHADOW_ACTIVE":
        return {
            "decision": "SHADOW_REJECT",
            "reasons": ["LIFECYCLE_NOT_SHADOW_ACTIVE"],
            "broker_writes": False,
            "capital_authority": False,
            "execution_authority": False,
        }

    # RND-0053 fixture evaluation never accepts broker/capital/live authority,
    # even if supplied by a hostile caller.
    if any([
        effective.get("broker_writes_authorized") is True,
        effective.get("capital_authority") is True,
        effective.get("live_environment_authorized") is True,
    ]):
        return {
            "decision": "SHADOW_REJECT",
            "reasons": ["AUTHORITY_ESCALATION_PROHIBITED"],
            "broker_writes": False,
            "capital_authority": False,
            "execution_authority": False,
        }

    return evaluate_shadow_intent(intent, policy, seen_intent_ids=seen_intent_ids)


def authority_snapshot(state, requested_authority=None):
    """Return the fail-closed effective authority snapshot for inspection/testing."""
    return effective_authority(state, requested_authority or {})
