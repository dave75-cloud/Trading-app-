#!/usr/bin/env python3
"""Pure-local falsification helpers for RND-0026.

No file writes, network access, strategy search, ranking, broker access or
promotion authority.
"""

from __future__ import annotations

import math
import re
from datetime import datetime


LEDGER_VERSION = "RND-historical-evidence-ledger-v0.1"
ALLOWED_STATUSES = {
    "REPRODUCIBLE",
    "PARTIALLY_REPRODUCIBLE",
    "UNREPRODUCIBLE",
    "INVALID_AS_PERFORMANCE_EVIDENCE",
}
GIT_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")


class HistoricalEvidenceError(ValueError):
    pass


def _text(value, role):
    if not isinstance(value, str) or not value.strip():
        raise HistoricalEvidenceError(f"{role}: expected non-empty string")
    return value.strip()


def _utc(value, role):
    value = _text(value, role)
    if not value.endswith("Z"):
        raise HistoricalEvidenceError(f"{role}: expected UTC timestamp ending Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HistoricalEvidenceError(f"{role}: invalid timestamp") from exc


def validate_evidence_ledger(ledger):
    if not isinstance(ledger, dict):
        raise HistoricalEvidenceError("ledger: expected object")
    if set(ledger) != {"contract_version", "base_commit", "claims"}:
        raise HistoricalEvidenceError("ledger: unexpected or missing fields")
    if ledger["contract_version"] != LEDGER_VERSION:
        raise HistoricalEvidenceError("ledger: unsupported contract version")
    if not GIT_BLOB_RE.fullmatch(_text(ledger["base_commit"], "base_commit")):
        raise HistoricalEvidenceError("base_commit: expected 40 lowercase hex chars")

    claims = ledger["claims"]
    if not isinstance(claims, list) or not claims:
        raise HistoricalEvidenceError("claims: expected non-empty list")
    ids = []
    for i, claim in enumerate(claims):
        role = f"claims[{i}]"
        if not isinstance(claim, dict):
            raise HistoricalEvidenceError(f"{role}: expected object")
        allowed = {"claim_id", "status", "claim", "evidence", "missing"}
        if not set(claim).issubset(allowed):
            raise HistoricalEvidenceError(f"{role}: unexpected field")
        for required in ("claim_id", "status", "claim", "evidence"):
            if required not in claim:
                raise HistoricalEvidenceError(f"{role}: missing {required}")
        ids.append(_text(claim["claim_id"], role + ".claim_id"))
        if claim["status"] not in ALLOWED_STATUSES:
            raise HistoricalEvidenceError(f"{role}: invalid status")
        _text(claim["claim"], role + ".claim")
        evidence = claim["evidence"]
        if not isinstance(evidence, list):
            raise HistoricalEvidenceError(f"{role}.evidence: expected list")
        for j, item in enumerate(evidence):
            if not isinstance(item, dict) or set(item) != {"path", "git_blob"}:
                raise HistoricalEvidenceError(
                    f"{role}.evidence[{j}]: exact path/git_blob required"
                )
            _text(item["path"], f"{role}.evidence[{j}].path")
            if not GIT_BLOB_RE.fullmatch(item["git_blob"]):
                raise HistoricalEvidenceError(
                    f"{role}.evidence[{j}].git_blob: invalid"
                )
        missing = claim.get("missing", [])
        if not isinstance(missing, list) or not all(
            isinstance(x, str) and x.strip() for x in missing
        ):
            raise HistoricalEvidenceError(f"{role}.missing: invalid")
        if claim["status"] == "UNREPRODUCIBLE" and not missing:
            raise HistoricalEvidenceError(
                f"{role}: unreproducible claim must identify missing evidence"
            )
        if claim["status"] == "REPRODUCIBLE" and not evidence:
            raise HistoricalEvidenceError(
                f"{role}: reproducible claim requires repository evidence"
            )
    if len(set(ids)) != len(ids):
        raise HistoricalEvidenceError("claims: duplicate claim_id")
    return True


def clipping_counterfactual(net_returns, notional=5.0, max_loss=0.005):
    """Compare raw scaled compounding with legacy lower-only clipping.

    This is a diagnostic counterfactual, not an executable stop-loss model.
    """
    if not isinstance(net_returns, (list, tuple)) or not net_returns:
        raise HistoricalEvidenceError("net_returns: expected non-empty sequence")
    if not isinstance(notional, (int, float)) or notional <= 0:
        raise HistoricalEvidenceError("notional: must be positive")
    if not isinstance(max_loss, (int, float)) or not (0 < max_loss < 1):
        raise HistoricalEvidenceError("max_loss: must be between 0 and 1")

    raw_equity = 1.0
    clipped_equity = 1.0
    affected = 0
    rows = []
    for i, value in enumerate(net_returns):
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise HistoricalEvidenceError(f"net_returns[{i}]: invalid")
        scaled = float(value) * float(notional)
        if scaled <= -1:
            raise HistoricalEvidenceError(
                f"net_returns[{i}]: scaled return <= -100%; compounding undefined"
            )
        clipped = max(scaled, -float(max_loss))
        affected += int(clipped != scaled)
        raw_equity *= 1.0 + scaled
        clipped_equity *= 1.0 + clipped
        rows.append({"scaled": scaled, "clipped": clipped})

    return {
        "raw_final_equity": raw_equity,
        "clipped_final_equity": clipped_equity,
        "equity_uplift": clipped_equity - raw_equity,
        "affected_trades": affected,
        "rows": rows,
        "executable_stop_loss_evidence": False,
    }


def validate_chronological_windows(windows):
    if not isinstance(windows, dict) or set(windows) != {
        "development", "validation", "test"
    }:
        raise HistoricalEvidenceError(
            "windows: require development, validation and test"
        )
    parsed = {}
    for name in ("development", "validation", "test"):
        item = windows[name]
        if not isinstance(item, dict) or set(item) != {"start_utc", "end_utc"}:
            raise HistoricalEvidenceError(f"windows.{name}: invalid")
        start = _utc(item["start_utc"], f"windows.{name}.start_utc")
        end = _utc(item["end_utc"], f"windows.{name}.end_utc")
        if start >= end:
            raise HistoricalEvidenceError(f"windows.{name}: start >= end")
        parsed[name] = (start, end)
    if (
        parsed["development"][1] > parsed["validation"][0]
        or parsed["validation"][1] > parsed["test"][0]
    ):
        raise HistoricalEvidenceError("windows: temporal contamination/overlap")
    return True


def overlapping_trade_pairs(trades):
    """Return overlapping trade-id pairs; empty means no interval overlap."""
    if not isinstance(trades, list):
        raise HistoricalEvidenceError("trades: expected list")
    parsed = []
    ids = []
    for i, trade in enumerate(trades):
        if not isinstance(trade, dict) or set(trade) != {
            "trade_id", "entry_utc", "exit_utc"
        }:
            raise HistoricalEvidenceError(f"trades[{i}]: invalid fields")
        trade_id = _text(trade["trade_id"], f"trades[{i}].trade_id")
        start = _utc(trade["entry_utc"], f"trades[{i}].entry_utc")
        end = _utc(trade["exit_utc"], f"trades[{i}].exit_utc")
        if start >= end:
            raise HistoricalEvidenceError(f"trades[{i}]: entry must precede exit")
        ids.append(trade_id)
        parsed.append((trade_id, start, end))
    if len(set(ids)) != len(ids):
        raise HistoricalEvidenceError("trades: duplicate trade_id")
    overlaps = []
    for i, (left_id, left_start, left_end) in enumerate(parsed):
        for right_id, right_start, right_end in parsed[i + 1:]:
            if max(left_start, right_start) < min(left_end, right_end):
                overlaps.append((left_id, right_id))
    return overlaps


def classify_ambiguous_bar(high, low, stop, target, side):
    """Fail closed when one OHLC bar touches both stop and target."""
    values = (high, low, stop, target)
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in values):
        raise HistoricalEvidenceError("bar values: invalid")
    if high < low:
        raise HistoricalEvidenceError("bar: high below low")
    if side == "long":
        hit_stop = low <= stop
        hit_target = high >= target
    elif side == "short":
        hit_stop = high >= stop
        hit_target = low <= target
    else:
        raise HistoricalEvidenceError("side: expected long or short")
    if hit_stop and hit_target:
        return "AMBIGUOUS"
    if hit_stop:
        return "STOP"
    if hit_target:
        return "TARGET"
    return "NEITHER"


def m005_performance_gate(gap_report):
    if not isinstance(gap_report, dict):
        raise HistoricalEvidenceError("gap report: expected object")
    required = {
        "contract_version", "task_id", "base_commit", "fixed_behaviour",
        "performance_declaration_status", "blocking_gaps", "next_stage",
    }
    if set(gap_report) != required:
        raise HistoricalEvidenceError("gap report: field mismatch")
    if gap_report["performance_declaration_status"] != "BLOCKED_INSUFFICIENT_EVIDENCE":
        raise HistoricalEvidenceError("gap report: must fail closed in RND-0026")
    gaps = gap_report["blocking_gaps"]
    if not isinstance(gaps, list) or not gaps or not all(
        isinstance(x, str) and x.strip() for x in gaps
    ):
        raise HistoricalEvidenceError("gap report: blocking gaps required")
    return {
        "performance_declaration_allowed": False,
        "blocking_gap_count": len(gaps),
        "strategy_selection_authority": False,
        "promotion_authority": False,
    }
