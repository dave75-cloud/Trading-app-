from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

VALID_DIRECTIONS={"LONG","SHORT"}
VALID_PROVIDER={"CONNECTED","DEGRADED","DISCONNECTED"}
VALID_SESSION={"OPEN","CLOSED","UNKNOWN"}
VALID_RECON={"RECONCILED","RECONCILIATION_PENDING","RECONCILIATION_FAILED"}
VALID_KILLS={None,"GLOBAL_KILL","RECONCILIATION_KILL","DATA_INTEGRITY_KILL","RISK_LIMIT_KILL","STRATEGY_SUSPEND"}
VALID_REJECTIONS={
    "STALE_QUOTE","PROVIDER_DISCONNECTED","SESSION_CLOSED","INVALID_QUOTE",
    "LATENCY_VIOLATION","DUPLICATE_REQUEST","RISK_STATE_STALE","RECONCILIATION_BLOCK",
    "KILL_ACTIVE","SIMULATED_LIQUIDITY_REJECT","PROVIDER_DEGRADED","UNKNOWN_PROVIDER",
    "UNKNOWN_SESSION","INVALID_SLIPPAGE","INVALID_PARTIAL_FILL","INVALID_REPLACEMENT",
    "MODE_VIOLATION","AUDIT_FAILURE"
}

class RND0060VError(ValueError):
    pass

def _req(c: bool, m: str):
    if not c:
        raise RND0060VError(m)

@dataclass(frozen=True)
class QuoteSnapshot:
    instrument: str
    bid: float
    ask: float
    quote_timestamp_utc: float
    quote_source_identity: str
    quote_sequence: int
    session_state: str
    provider_state: str
    fresh: bool=True
    degraded_integrity_pass: bool=False

@dataclass(frozen=True)
class RiskState:
    risk_state_id: str
    portfolio_state_id: str
    fresh: bool
    reconciliation_state: str
    kill_state: Optional[str]
    mode: str="SHADOW_ONLY"
    broker_write_authority: bool=False

@dataclass(frozen=True)
class ShadowRequest:
    request_id: str
    parent_intent_id: str
    parent_risk_id: str
    parent_admissibility_id: str
    parent_signal_id: str
    instrument: str
    direction: str
    requested_exposure: float
    authorized_exposure: float
    intent_timestamp_utc: float
    slippage: float
    latency_seconds: float
    fill_fraction: float=1.0
    simulate_reject: bool=False
    mode: str="SHADOW_ONLY"
    broker_write_authority: bool=False
    replacement_of: Optional[str]=None


def _base_validate(req: ShadowRequest, quote: QuoteSnapshot, risk: RiskState):
    _req(req.mode=="SHADOW_ONLY" and risk.mode=="SHADOW_ONLY", "MODE_VIOLATION")
    _req(req.broker_write_authority is False and risk.broker_write_authority is False, "MODE_VIOLATION")
    _req(req.direction in VALID_DIRECTIONS, "invalid direction")
    _req(req.instrument==quote.instrument, "instrument mismatch")
    _req(req.requested_exposure>=0 and req.authorized_exposure>=0, "negative exposure")
    _req(req.authorized_exposure<=req.requested_exposure, "exposure monotonicity breach")
    _req(req.slippage>=0, "INVALID_SLIPPAGE")
    _req(req.latency_seconds>=0, "LATENCY_VIOLATION")
    _req(0 <= req.fill_fraction <= 1, "INVALID_PARTIAL_FILL")
    _req(risk.reconciliation_state in VALID_RECON, "RECONCILIATION_BLOCK")
    _req(risk.kill_state in VALID_KILLS, "KILL_ACTIVE")
    _req(quote.provider_state in VALID_PROVIDER, "UNKNOWN_PROVIDER")
    _req(quote.session_state in VALID_SESSION, "UNKNOWN_SESSION")


def _reject(req: ShadowRequest, quote: QuoteSnapshot, risk: RiskState, code: str) -> Dict[str,Any]:
    _req(code in VALID_REJECTIONS, "unknown rejection code")
    return {
        "request_id": req.request_id,
        "parent_intent_id": req.parent_intent_id,
        "parent_risk_id": req.parent_risk_id,
        "parent_admissibility_id": req.parent_admissibility_id,
        "parent_signal_id": req.parent_signal_id,
        "quote_identity": f"{quote.quote_source_identity}:{quote.quote_sequence}",
        "risk_state_identity": risk.risk_state_id,
        "simulated_status": "REJECTED",
        "requested_exposure": req.requested_exposure,
        "authorized_exposure": req.authorized_exposure,
        "filled_exposure": 0.0,
        "residual_exposure": req.authorized_exposure,
        "reference_executable_side": "ASK" if req.direction=="LONG" else "BID",
        "simulated_fill_price": None,
        "slippage_assumption": req.slippage,
        "latency_assumption": req.latency_seconds,
        "rejection_code": code,
        "mode": "SHADOW_ONLY",
        "broker_write_authority": False,
        "replacement_of": req.replacement_of,
    }


def simulate_shadow_execution(req: ShadowRequest, quote: QuoteSnapshot, risk: RiskState, seen_request_ids: Optional[set]=None) -> Dict[str,Any]:
    _base_validate(req, quote, risk)
    seen_request_ids = seen_request_ids if seen_request_ids is not None else set()
    if req.request_id in seen_request_ids:
        return _reject(req, quote, risk, "DUPLICATE_REQUEST")
    seen_request_ids.add(req.request_id)
    if risk.kill_state is not None:
        return _reject(req, quote, risk, "KILL_ACTIVE")
    if not risk.fresh:
        return _reject(req, quote, risk, "RISK_STATE_STALE")
    if risk.reconciliation_state != "RECONCILED":
        return _reject(req, quote, risk, "RECONCILIATION_BLOCK")
    if quote.bid<=0 or quote.ask<=0 or quote.bid>=quote.ask or not quote.quote_source_identity:
        return _reject(req, quote, risk, "INVALID_QUOTE")
    if not quote.fresh:
        return _reject(req, quote, risk, "STALE_QUOTE")
    if quote.session_state=="CLOSED":
        return _reject(req, quote, risk, "SESSION_CLOSED")
    if quote.session_state=="UNKNOWN":
        return _reject(req, quote, risk, "UNKNOWN_SESSION")
    if quote.provider_state=="DISCONNECTED":
        return _reject(req, quote, risk, "PROVIDER_DISCONNECTED")
    if quote.provider_state=="DEGRADED" and not quote.degraded_integrity_pass:
        return _reject(req, quote, risk, "PROVIDER_DEGRADED")
    if quote.quote_timestamp_utc < req.intent_timestamp_utc + req.latency_seconds:
        return _reject(req, quote, risk, "LATENCY_VIOLATION")
    if req.simulate_reject:
        return _reject(req, quote, risk, "SIMULATED_LIQUIDITY_REJECT")
    filled=req.authorized_exposure*req.fill_fraction
    _req(filled<=req.authorized_exposure<=req.requested_exposure, "exposure monotonicity breach")
    if req.direction=="LONG":
        price=quote.ask+req.slippage
        _req(price>=quote.ask, "INVALID_SLIPPAGE")
        side="ASK"
    else:
        price=quote.bid-req.slippage
        _req(price<=quote.bid, "INVALID_SLIPPAGE")
        side="BID"
    return {
        "request_id": req.request_id,
        "parent_intent_id": req.parent_intent_id,
        "parent_risk_id": req.parent_risk_id,
        "parent_admissibility_id": req.parent_admissibility_id,
        "parent_signal_id": req.parent_signal_id,
        "quote_identity": f"{quote.quote_source_identity}:{quote.quote_sequence}",
        "risk_state_identity": risk.risk_state_id,
        "simulated_status": "FILLED" if req.fill_fraction==1 else "PARTIAL_FILL",
        "requested_exposure": req.requested_exposure,
        "authorized_exposure": req.authorized_exposure,
        "filled_exposure": filled,
        "residual_exposure": req.authorized_exposure-filled,
        "reference_executable_side": side,
        "simulated_fill_price": price,
        "slippage_assumption": req.slippage,
        "latency_assumption": req.latency_seconds,
        "rejection_code": None,
        "mode": "SHADOW_ONLY",
        "broker_write_authority": False,
        "replacement_of": req.replacement_of,
    }


def validate_replacement(original: ShadowRequest, replacement: ShadowRequest):
    _req(replacement.replacement_of==original.request_id, "INVALID_REPLACEMENT")
    _req(replacement.request_id!=original.request_id, "INVALID_REPLACEMENT")
    _req(replacement.instrument==original.instrument, "INVALID_REPLACEMENT")
    _req(replacement.direction==original.direction, "INVALID_REPLACEMENT")
    _req(replacement.authorized_exposure<=original.authorized_exposure, "INVALID_REPLACEMENT")
    _req(replacement.parent_signal_id==original.parent_signal_id, "INVALID_REPLACEMENT")
    _req(replacement.parent_admissibility_id==original.parent_admissibility_id, "INVALID_REPLACEMENT")
    _req(replacement.parent_risk_id==original.parent_risk_id, "INVALID_REPLACEMENT")
    _req(replacement.mode=="SHADOW_ONLY" and replacement.broker_write_authority is False, "MODE_VIOLATION")
    return True


def audit_lineage(result: Dict[str,Any]) -> bool:
    required=("request_id","parent_intent_id","parent_risk_id","parent_admissibility_id","parent_signal_id","quote_identity","risk_state_identity","mode","broker_write_authority")
    return all(result.get(k) not in (None,"") for k in required[:-2]) and result.get("mode")=="SHADOW_ONLY" and result.get("broker_write_authority") is False
