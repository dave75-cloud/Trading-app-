from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any

Q003_STREAM = "Q003"
ACTIVITY_STREAM = "RND0060QR"
Q003_EARLIEST = datetime.fromisoformat("2027-04-03T07:25:00+00:00")
ACTIVITY_EARLIEST = datetime.fromisoformat("2027-04-07T02:33:50+00:00")

class RND0060XError(ValueError):
    pass

def _req(cond: bool, msg: str):
    if not cond:
        raise RND0060XError(msg)

def _dt(v: str) -> datetime:
    d = datetime.fromisoformat(v.replace("Z", "+00:00"))
    _req(d.tzinfo is not None, "timezone required")
    return d.astimezone(timezone.utc)

@dataclass(frozen=True)
class ReadinessInput:
    stream_id: str
    prospective_start_utc: str
    evaluation_time_utc: str
    minimum_horizon_days: int
    elapsed_calendar_days: int
    minimum_observation_count: Optional[int]
    eligible_observation_count: Optional[int]
    provenance_integrity_pass: bool
    duplicate_check_pass: bool
    chronology_check_pass: bool
    pre_start_contamination_count: int
    prohibited_partition_access_count: int
    cross_stream_outcome_contamination: bool
    early_economic_access_count: int = 0
    expected_evidence_accounted_for: bool = True
    admit_group_count: Optional[int] = None
    veto_group_count: Optional[int] = None
    minimum_group_count: Optional[int] = None
    protocol_version_known: bool = True
    evidence_ledger_present: bool = True
    hashes_present: bool = True
    evidence_mutation_detected: bool = False
    economic_fields_open: bool = False
    human_readout_gate: bool = False
    promotion_authority: bool = False
    broker_write_authority: bool = False
    capital_authority: bool = False
    live_execution_authority: bool = False
    reserved_final_open: bool = False

@dataclass(frozen=True)
class HumanReadoutReceipt:
    stream_id: str
    evidence_ledger_version: str
    readout_protocol_version: str
    authorization_timestamp_utc: str
    tuning_authorized: bool
    reserved_final_remains_closed: bool
    automatic_promotion_authorized: bool


def _base_guard(inp: ReadinessInput):
    _req(inp.stream_id in {Q003_STREAM, ACTIVITY_STREAM}, "unknown stream")
    _req(inp.minimum_horizon_days == 180, "unexpected horizon")
    _req(inp.economic_fields_open is False, "economic fields cannot open in readiness kernel")
    _req(inp.human_readout_gate is False, "human gate cannot be pre-opened by machine")
    _req(inp.promotion_authority is False, "promotion authority forbidden")
    _req(inp.broker_write_authority is False, "broker authority forbidden")
    _req(inp.capital_authority is False, "capital authority forbidden")
    _req(inp.live_execution_authority is False, "live authority forbidden")
    _req(inp.reserved_final_open is False, "reserved final must remain closed")
    _req(inp.protocol_version_known, "unknown protocol version")
    _req(inp.evidence_ledger_present, "missing evidence ledger")
    _req(inp.hashes_present, "missing hashes/provenance identity")
    _req(not inp.evidence_mutation_detected, "evidence mutation detected")
    _req(inp.pre_start_contamination_count >= 0, "invalid contamination count")
    _req(inp.prohibited_partition_access_count >= 0, "invalid prohibited access count")
    _req(inp.early_economic_access_count >= 0, "invalid early access count")
    _req(_dt(inp.evaluation_time_utc) >= _dt(inp.prospective_start_utc), "evaluation before prospective start")


def evaluate_readiness(inp: ReadinessInput) -> Dict[str, Any]:
    _base_guard(inp)
    eval_dt = _dt(inp.evaluation_time_utc)

    structural_problem = (
        not inp.provenance_integrity_pass
        or not inp.duplicate_check_pass
        or not inp.chronology_check_pass
        or inp.pre_start_contamination_count > 0
        or inp.prohibited_partition_access_count > 0
        or inp.cross_stream_outcome_contamination
        or inp.early_economic_access_count > 0
    )

    if inp.stream_id == Q003_STREAM:
        _req(inp.minimum_observation_count is None, "Q003 may not inherit observation-count gate")
        _req(inp.eligible_observation_count is None, "Q003 may not inherit activity counters")
        time_ok = eval_dt >= Q003_EARLIEST and inp.elapsed_calendar_days >= 180
        if structural_problem or not inp.expected_evidence_accounted_for:
            status = "INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE"
        elif not time_ok:
            status = "ACCUMULATING_PROSPECTIVE_VALIDATION_EVIDENCE"
        else:
            status = "READOUT_ELIGIBLE_PENDING_HUMAN_GATE"
    else:
        _req(inp.minimum_observation_count == 100, "activity stream minimum observation count must be 100")
        _req(inp.eligible_observation_count is not None and inp.eligible_observation_count >= 0, "activity observation count required")
        _req(inp.minimum_group_count is not None and inp.minimum_group_count >= 0, "minimum group count required")
        _req(inp.admit_group_count is not None and inp.veto_group_count is not None, "group counts required")
        time_ok = eval_dt >= ACTIVITY_EARLIEST and inp.elapsed_calendar_days >= 180
        groups_ok = inp.admit_group_count >= inp.minimum_group_count and inp.veto_group_count >= inp.minimum_group_count
        if structural_problem:
            status = "INCONCLUSIVE_EXTEND_CONFIRMATION"
        elif not time_ok or inp.eligible_observation_count < 100:
            status = "ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE"
        elif not groups_ok:
            status = "INCONCLUSIVE_EXTEND_CONFIRMATION"
        else:
            status = "READOUT_ELIGIBLE_PENDING_HUMAN_GATE"

    return {
        "stream_id": inp.stream_id,
        "status": status,
        "economic_fields_open": False,
        "human_readout_gate": False,
        "promotion_authority": False,
        "broker_write_authority": False,
        "capital_authority": False,
        "live_execution_authority": False,
        "reserved_final_open": False,
        "structural_eligibility_only": status == "READOUT_ELIGIBLE_PENDING_HUMAN_GATE",
        "economic_success": None,
    }


def authorize_economic_readout(readiness: Dict[str, Any], receipt: HumanReadoutReceipt) -> Dict[str, Any]:
    _req(readiness.get("status") == "READOUT_ELIGIBLE_PENDING_HUMAN_GATE", "stream not structurally eligible")
    _req(receipt.stream_id == readiness.get("stream_id"), "receipt stream mismatch")
    _req(bool(receipt.evidence_ledger_version), "missing evidence ledger version")
    _req(bool(receipt.readout_protocol_version), "missing readout protocol version")
    _dt(receipt.authorization_timestamp_utc)
    _req(receipt.tuning_authorized is False, "readout receipt cannot authorize tuning")
    _req(receipt.reserved_final_remains_closed is True, "reserved final must remain closed")
    _req(receipt.automatic_promotion_authorized is False, "automatic promotion forbidden")
    return {
        **readiness,
        "economic_fields_open": True,
        "human_readout_gate": True,
        "promotion_authority": False,
        "broker_write_authority": False,
        "capital_authority": False,
        "live_execution_authority": False,
        "reserved_final_open": False,
        "human_readout_receipt_stream": receipt.stream_id,
    }


def promotion_firewall(readout_state: Dict[str, Any], *, positive_outcome: bool, request_promotion: bool = False,
                       broker_write_authority: bool = False, capital_authority: bool = False,
                       live_execution_authority: bool = False) -> Dict[str, Any]:
    _req(readout_state.get("human_readout_gate") is True, "human readout gate required")
    _req(readout_state.get("economic_fields_open") is True, "economic fields must be human-opened")
    _req(not broker_write_authority and not capital_authority and not live_execution_authority, "live/capital/broker authority forbidden")
    _req(request_promotion is False, "no machine path from readout to promotion")
    return {
        "stream_id": readout_state.get("stream_id"),
        "positive_outcome": bool(positive_outcome),
        "promotion_authority": False,
        "human_promotion_review_required": True,
        "broker_write_authority": False,
        "capital_authority": False,
        "live_execution_authority": False,
        "reserved_final_open": False,
    }
