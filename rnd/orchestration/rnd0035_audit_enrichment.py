#!/usr/bin/env python3
"""Deterministic audit enrichment for RND-0035 historical trial results.

This module never changes strategy decisions, executions, prices or returns.
It adds audit evidence derivable exactly from the completed-trade ledger when
an implementation family exposes a thinner event/result schema.
"""

from __future__ import annotations

import copy
from datetime import datetime


class RND0035AuditError(ValueError):
    pass


def _parse_utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RND0035AuditError("UTC Z timestamp required")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _synthetic_trade_events(trade):
    required = (
        "symbol", "side_value", "entry_timestamp", "exit_timestamp",
        "entry_execution_price", "exit_execution_price", "net_return",
    )
    if any(key not in trade for key in required):
        raise RND0035AuditError("trade ledger insufficient for audit reconstruction")
    return (
        {
            "event_type": "ENTRY",
            "symbol": trade["symbol"],
            "timestamp": trade["entry_timestamp"],
            "side_value": trade["side_value"],
            "execution_price": trade["entry_execution_price"],
            "audit_reconstructed": True,
        },
        {
            "event_type": "EXIT",
            "symbol": trade["symbol"],
            "timestamp": trade["exit_timestamp"],
            "side_value": trade["side_value"],
            "execution_price": trade["exit_execution_price"],
            "net_return": trade["net_return"],
            "audit_reconstructed": True,
        },
    )


def enrich_for_historical_audit(result):
    """Return an audit-enriched deep copy without changing economic outcomes."""
    out = copy.deepcopy(result)
    trades = out.get("trades")
    events = out.get("events")
    censored = out.get("censored_trades", [])
    if not isinstance(trades, list) or not isinstance(events, list):
        raise RND0035AuditError("trial result must expose trades and events lists")
    if out.get("completed_trade_count") != len(trades):
        raise RND0035AuditError("completed trade count does not reconcile")
    if out.get("censored_trade_count") != len(censored):
        raise RND0035AuditError("censored trade count does not reconcile")

    # RND-0034 records elapsed wall-clock time for completed trades. Add it
    # only when absent; never overwrite implementation evidence.
    for trade in trades:
        if "elapsed_seconds" not in trade:
            trade["elapsed_seconds"] = int(
                (_parse_utc(trade["exit_timestamp"]) - _parse_utc(trade["entry_timestamp"])).total_seconds()
            )

    entry_events = [e for e in events if e.get("event_type") == "ENTRY"]
    exit_events = [e for e in events if e.get("event_type") == "EXIT"]
    if (entry_events or exit_events) and (
        len(entry_events) != len(trades) or len(exit_events) != len(trades)
    ):
        raise RND0035AuditError("partial ENTRY/EXIT ledger cannot be silently repaired")
    if not entry_events and not exit_events:
        for trade in trades:
            entry_event, exit_event = _synthetic_trade_events(trade)
            events.extend((entry_event, exit_event))

    wins = sum(1 for trade in trades if trade["net_return"] > 0)
    out["censoring_rate"] = (
        len(censored) / (len(trades) + len(censored)) if trades or censored else 0.0
    )
    out["net_hit_rate"] = wins / len(trades) if trades else None

    by_year = {}
    for trade in trades:
        year = str(trade.get("exit_year") or _parse_utc(trade["exit_timestamp"]).year)
        row = by_year.setdefault(year, {"trades": 0, "net_return_sum": 0.0, "cost_drag_sum": 0.0})
        row["trades"] += 1
        row["net_return_sum"] += trade["net_return"]
        row["cost_drag_sum"] += trade["execution_cost_drag"]
    out["by_exit_year"] = by_year

    event_types = [e.get("event_type") for e in events]
    out["event_reconciliation"] = {
        "entry_events": event_types.count("ENTRY"),
        "exit_events": event_types.count("EXIT"),
        "gap_events": event_types.count("GAP"),
        "strategy_reset_events": event_types.count("STRATEGY_RESET"),
        "raw_signal_events": event_types.count("RAW_SIGNAL"),
        "delayed_signal_events": event_types.count("DELAYED_SIGNAL"),
        "pending_signal_cancel_events": event_types.count("PENDING_SIGNAL_CANCELLED"),
    }
    if out["event_reconciliation"]["entry_events"] != len(trades):
        raise RND0035AuditError("ENTRY events do not reconcile to completed trades")
    if out["event_reconciliation"]["exit_events"] != len(trades):
        raise RND0035AuditError("EXIT events do not reconcile to completed trades")

    out["historical_audit_enrichment"] = {
        "economic_fields_modified": False,
        "trade_ledger_modified": False,
        "derived_entry_exit_events_may_be_added": True,
        "status": "PASS",
    }
    return out
