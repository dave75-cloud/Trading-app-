#!/usr/bin/env python3
"""Pure development-only cross-sectional relative-value kernel for RND-0060C."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
ORIENTATION = {"AUDUSD": -1.0, "EURUSD": -1.0, "GBPUSD": -1.0, "USDJPY": 1.0}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
DECISION_HOUR = 11
DECISION_MINUTE = 30
LOOKBACK_MINUTES = 30
HOLD_BARS = 3
M5 = timedelta(minutes=5)


class RND0060CError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060CError(message)


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0060CError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def _price(value, role):
    _req(not isinstance(value, bool), f"{role}: positive finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060CError(f"{role}: positive finite number required") from exc
    _req(math.isfinite(out) and out > 0, f"{role}: positive finite number required")
    return out


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close"}
    out = []
    prev = None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(prev is None or dt > prev, "rows: timestamps must be unique and ordered")
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        _req(bid <= mid <= ask, "bid/mid/ask ordering invalid")
        out.append({"dt": dt, "bid": bid, "ask": ask, "mid": mid})
        prev = dt
    return out


def _trade_return(side, entry_exec, exit_exec, entry_mid, exit_mid):
    if side == 1:
        gross = (exit_mid - entry_mid) / entry_mid
        net = (exit_exec - entry_exec) / entry_exec
    else:
        gross = (entry_mid - exit_mid) / entry_mid
        net = (entry_exec - exit_exec) / entry_exec
    return gross, net


def _max_drawdown(returns):
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
    return equity, max_dd


def _side_from_residual(symbol, residual):
    _req(residual != 0.0, "zero residual cannot define side")
    sign = 1 if residual > 0 else -1
    return sign if ORIENTATION[symbol] < 0 else -sign


def evaluate_portfolio(rows_by_symbol):
    _req(isinstance(rows_by_symbol, dict) and set(rows_by_symbol) == set(SYMBOLS), "exact four-symbol row mapping required")
    parsed = {s: validate_rows(rows_by_symbol[s]) for s in SYMBOLS}
    by_dt = {s: {r["dt"]: r for r in parsed[s]} for s in SYMBOLS}
    index_by_dt = {s: {r["dt"]: i for i, r in enumerate(parsed[s])} for s in SYMBOLS}

    per_symbol_trades = {s: [] for s in SYMBOLS}
    per_symbol_marks = {s: [] for s in SYMBOLS}
    events = []
    selected_counts = {s: 0 for s in SYMBOLS}

    # Use dates present in every symbol at the fixed decision timestamp.
    date_sets = []
    for s in SYMBOLS:
        date_sets.append({r["dt"].date() for r in parsed[s] if r["dt"].hour == DECISION_HOUR and r["dt"].minute == DECISION_MINUTE and r["dt"].weekday() < 5})
    days = sorted(set.intersection(*date_sets)) if date_sets else []

    active = None
    held = 0
    previous_dt = None
    gap_count = 0

    # A helper to advance any open position through genuine observations of its symbol up to a target timestamp.
    def advance_until(target_dt):
        nonlocal active, held, previous_dt, gap_count
        if active is None:
            return
        symbol = active["symbol"]
        start_i = index_by_dt[symbol][active["last_dt"]] + 1
        rows = parsed[symbol]
        i = start_i
        while i < len(rows) and active is not None and rows[i]["dt"] <= target_dt:
            bar = rows[i]
            delta = bar["dt"] - previous_dt
            if delta != M5:
                gap_count += 1
                events.append({
                    "event_type": "GAP_DURING_POSITION",
                    "symbol": symbol,
                    "previous_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
            held += 1
            previous_dt = bar["dt"]
            active["last_dt"] = bar["dt"]
            mark_exec = bar["bid"] if active["side"] == 1 else bar["ask"]
            if active["side"] == 1:
                mark_return = (mark_exec - active["entry_exec"]) / active["entry_exec"]
            else:
                mark_return = (active["entry_exec"] - mark_exec) / active["entry_exec"]

            if held == HOLD_BARS:
                exit_exec = mark_exec
                gross, net = _trade_return(active["side"], active["entry_exec"], exit_exec, active["entry_mid"], bar["mid"])
                trade = {
                    "symbol": symbol,
                    "side": "long" if active["side"] == 1 else "short",
                    "entry_timestamp": active["entry_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "exit_timestamp": bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "holding_bars": held,
                    "gap_exposure_count": gap_count,
                    "entry_execution_price": active["entry_exec"],
                    "exit_execution_price": exit_exec,
                    "entry_mid_price": active["entry_mid"],
                    "exit_mid_price": bar["mid"],
                    "gross_return": gross,
                    "net_return": net,
                    "execution_cost_drag": gross - net,
                    "exit_year": bar["dt"].year,
                }
                per_symbol_trades[symbol].append(trade)
                per_symbol_marks[symbol].append({"symbol": symbol, "timestamp": trade["exit_timestamp"], "position": 0, "mark_return": None})
                events.append({"event_type": "EXIT", "symbol": symbol, "timestamp": trade["exit_timestamp"], "net_return": net})
                active = None
                held = 0
                previous_dt = None
                gap_count = 0
            else:
                per_symbol_marks[symbol].append({
                    "symbol": symbol,
                    "timestamp": bar["dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "position": active["side"],
                    "mark_return": mark_return,
                })
            i += 1

    for day in days:
        decision_dt = datetime(day.year, day.month, day.day, DECISION_HOUR, DECISION_MINUTE, tzinfo=timezone.utc)
        advance_until(decision_dt)
        if active is not None:
            events.append({"event_type": "DAY_SKIPPED_OPEN_POSITION", "timestamp": decision_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "symbol": active["symbol"]})
            continue

        window = [decision_dt - M5 * n for n in range(6, -1, -1)]
        window_ok = True
        for s in SYMBOLS:
            if any(ts not in by_dt[s] for ts in window):
                window_ok = False
                break
        if not window_ok:
            events.append({"event_type": "DAY_SKIPPED_INCOMPLETE_CROSS_SECTION", "timestamp": decision_dt.strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue

        usd_returns = {}
        for s in SYMBOLS:
            start = by_dt[s][window[0]]["mid"]
            end = by_dt[s][window[-1]]["mid"]
            raw = end / start - 1.0
            usd_returns[s] = ORIENTATION[s] * raw

        residuals = {}
        for s in SYMBOLS:
            peers = [usd_returns[x] for x in SYMBOLS if x != s]
            residuals[s] = usd_returns[s] - sum(peers) / 3.0

        max_abs = max(abs(v) for v in residuals.values())
        winners = [s for s in SYMBOLS if abs(residuals[s]) == max_abs]
        if len(winners) != 1 or max_abs == 0.0:
            events.append({"event_type": "NO_TRADE_EXACT_TIE", "timestamp": decision_dt.strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue

        symbol = winners[0]
        residual = residuals[symbol]
        side = _side_from_residual(symbol, residual)
        entry_dt = decision_dt + M5
        entry = by_dt[symbol].get(entry_dt)
        if entry is None or index_by_dt[symbol].get(entry_dt) != index_by_dt[symbol][decision_dt] + 1:
            events.append({"event_type": "PENDING_SIGNAL_CANCELLED", "symbol": symbol, "timestamp": entry_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "OBSERVATION_DISCONTINUITY"})
            continue

        entry_exec = entry["ask"] if side == 1 else entry["bid"]
        active = {
            "symbol": symbol,
            "side": side,
            "entry_dt": entry_dt,
            "entry_exec": entry_exec,
            "entry_mid": entry["mid"],
            "last_dt": entry_dt,
        }
        held = 0
        previous_dt = entry_dt
        gap_count = 0
        selected_counts[symbol] += 1
        per_symbol_marks[symbol].append({"symbol": symbol, "timestamp": entry_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "position": side, "mark_return": ((entry["bid"] - entry_exec) / entry_exec if side == 1 else (entry_exec - entry["ask"]) / entry_exec)})
        events.append({
            "event_type": "CROSS_SECTIONAL_SIGNAL",
            "timestamp": decision_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "selected_symbol": symbol,
            "residual": residual,
            "usd_returns": usd_returns,
            "residuals": residuals,
            "side_value": side,
        })
        events.append({"event_type": "ENTRY", "symbol": symbol, "timestamp": entry_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "side_value": side, "execution_price": entry_exec})

    # Finish any remaining economic position using genuine observed rows through sample end.
    if active is not None:
        advance_until(parsed[active["symbol"]][-1]["dt"])
    if active is not None:
        events.append({"event_type": "RIGHT_CENSORED", "symbol": active["symbol"], "timestamp": active["entry_dt"].strftime("%Y-%m-%dT%H:%M:%SZ")})

    per_symbol = {}
    for s in SYMBOLS:
        trades = per_symbol_trades[s]
        net_returns = [t["net_return"] for t in trades]
        gross_returns = [t["gross_return"] for t in trades]
        net_equity, max_dd = _max_drawdown(net_returns)
        gross_equity, _ = _max_drawdown(gross_returns)
        annual = {year: 0.0 for year in sorted(AUTHORIZED_YEARS)}
        for trade in trades:
            annual[trade["exit_year"]] += trade["net_return"]
        per_symbol[s] = {
            "symbol": s,
            "trades": trades,
            "marks": per_symbol_marks[s],
            "completed_trade_count": len(trades),
            "trade_count": len(trades),
            "terminal_net_equity": net_equity,
            "terminal_gross_equity": gross_equity,
            "realized_net_sum": sum(net_returns),
            "max_drawdown": max_dd,
            "execution_cost_drag": sum(t["execution_cost_drag"] for t in trades),
            "annual_realized_net": annual,
            "selected_count": selected_counts[s],
        }

    return {
        "per_symbol": per_symbol,
        "events": events,
        "selected_pair_counts": selected_counts,
        "trial_count": 1,
        "parameter_search": False,
        "development_only": True,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
