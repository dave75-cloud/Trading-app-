#!/usr/bin/env python3
"""Fixed-R000 simulator for RND-0035 sensitive E/F adversarial trials.

This module integrates only the already-frozen gap-policy and conservative
execution variants.  It consumes in-memory rows only and grants no authority
to open historical outcomes, broker writes, capital, validation, promotion,
or merge.
"""

from __future__ import annotations

from gap_aware_m005_reconstruction import (
    AUTHORIZED_YEARS,
    M5_SECONDS,
    SYMBOLS,
    _max_drawdown,
    _trade_return,
    population_std,
    validate_rows,
)
from rnd0035_sensitive_semantics import (
    CompleteSessionCooldown,
    HundredBarCooldown,
    PendingEntry,
    PendingExit,
)

SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}

SENSITIVE_TRIALS = {"E001", "E002", "F001", "F002", "F003", "F004"}


class RND0035SensitiveKernelError(ValueError):
    pass


def _raw_signal(symbol, closes, returns, dt):
    if len(closes) < 50 or len(returns) < 12:
        return None
    fast = sum(closes[-20:]) / 20
    slow = sum(closes[-50:]) / 50
    vol = population_std(returns[-12:])
    start, end = SESSIONS[symbol]
    if not (dt.weekday() < 5 and start <= dt.hour < end) or vol < 0.0005:
        return 0
    if fast > slow:
        return 1
    if fast < slow:
        return -1
    return 0


def reconstruct_sensitive_pair(trial_id, symbol, rows):
    if trial_id not in SENSITIVE_TRIALS:
        raise RND0035SensitiveKernelError("undeclared sensitive trial")
    if symbol not in SYMBOLS:
        raise RND0035SensitiveKernelError("unsupported symbol")

    parsed = validate_rows(rows)
    start_hour, end_hour = SESSIONS[symbol]
    cooldown = None
    if trial_id == "E001":
        cooldown = CompleteSessionCooldown(start_hour, end_hour)
    elif trial_id == "E002":
        cooldown = HundredBarCooldown()

    entry_latency = trial_id in {"F001", "F003"}
    exit_latency = trial_id in {"F002", "F003"}
    no_same_obs_reentry = trial_id == "F004"

    closes, returns = [], []
    previous_dt = previous_mid = previous_raw = None
    episode = 0
    position = 0
    bars_held = 0
    entry = None
    pending_entry = None
    pending_exit = None
    pending_exit_target = None
    gaps, trades, censored, events, marks = [], [], [], [], []

    def reset_strategy_state():
        nonlocal closes, returns, previous_mid, previous_raw, episode
        closes, returns = [], []
        previous_mid = None
        previous_raw = None
        episode += 1

    def open_trade(side, dt, bid, ask, mid):
        return {
            "symbol": symbol,
            "side": "long" if side == 1 else "short",
            "side_value": side,
            "entry_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": ask if side == 1 else bid,
            "entry_mid_price": mid,
            "episode": episode,
            "gap_exposure_count": 0,
            "gap_elapsed_seconds": 0,
        }

    def complete_trade(current, dt, bid, ask, mid, held):
        side = current["side_value"]
        exit_exec = bid if side == 1 else ask
        gross, net = _trade_return(
            side,
            current["entry_execution_price"],
            exit_exec,
            current["entry_mid_price"],
            mid,
        )
        return {
            "symbol": symbol,
            "side": current["side"],
            "entry_timestamp": current["entry_timestamp"],
            "exit_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entry_execution_price": current["entry_execution_price"],
            "exit_execution_price": exit_exec,
            "entry_mid_price": current["entry_mid_price"],
            "exit_mid_price": mid,
            "gross_return": gross,
            "net_return": net,
            "execution_cost_drag": gross - net,
            "holding_bars": held,
            "gap_exposure_count": current["gap_exposure_count"],
            "gap_elapsed_seconds": current["gap_elapsed_seconds"],
            "gap_exposed": current["gap_exposure_count"] > 0,
            "exit_year": dt.year,
            "episode": current["episode"],
            "status": "COMPLETE",
        }

    def execute_entry(side, dt, bid, ask, mid):
        nonlocal position, bars_held, entry
        position = side
        bars_held = 0
        entry = open_trade(side, dt, bid, ask, mid)
        events.append({
            "event_type": "ENTRY",
            "symbol": symbol,
            "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "side_value": side,
            "execution_price": entry["entry_execution_price"],
        })

    def execute_exit(dt, bid, ask, mid):
        nonlocal position, bars_held, entry
        completed = complete_trade(entry, dt, bid, ask, mid, bars_held)
        trades.append(completed)
        events.append({
            "event_type": "EXIT",
            "symbol": symbol,
            "timestamp": completed["exit_timestamp"],
            "side_value": entry["side_value"],
            "execution_price": completed["exit_execution_price"],
            "net_return": completed["net_return"],
        })
        position = 0
        bars_held = 0
        entry = None

    reset_strategy_state()

    for dt, bid, ask, mid in parsed:
        gap_now = False
        if previous_dt is not None:
            delta = int((dt - previous_dt).total_seconds())
            if delta != M5_SECONDS:
                gap_now = True
                gap = {
                    "symbol": symbol,
                    "previous_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "elapsed_seconds": delta,
                    "position_was_open": position != 0,
                }
                gaps.append(gap)
                events.append({"event_type": "GAP", **gap})
                if position != 0 and entry is not None:
                    entry["gap_exposure_count"] += 1
                    entry["gap_elapsed_seconds"] += delta
                if pending_entry is not None:
                    events.append({
                        "event_type": "PENDING_ENTRY_CANCELLED",
                        "symbol": symbol,
                        "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "reason": "OBSERVATION_DISCONTINUITY",
                    })
                    pending_entry = None
                if cooldown is not None:
                    cooldown.on_gap()
                reset_strategy_state()
                events.append({
                    "event_type": "STRATEGY_RESET",
                    "symbol": symbol,
                    "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "reason": "OBSERVATION_DISCONTINUITY",
                    "portfolio_position": position,
                })

        if previous_mid is not None:
            returns.append(mid / previous_mid - 1.0)
        closes.append(mid)

        raw = _raw_signal(symbol, closes, returns, dt)
        desired = previous_raw
        previous_raw = raw
        if raw is not None:
            events.append({"event_type": "RAW_SIGNAL", "symbol": symbol,
                           "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "signal": raw})
        if desired is not None:
            events.append({"event_type": "DELAYED_SIGNAL", "symbol": symbol,
                           "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "signal": desired})

        entry_eligible = cooldown.observe(dt) if cooldown is not None else True

        if position != 0:
            bars_held += 1

        # Resolve a delayed exit before considering today's fresh instruction.
        if pending_exit is not None and position != 0:
            resolution = pending_exit.resolve(dt)
            target = pending_exit_target
            events.append({
                "event_type": "PENDING_EXIT_EXECUTED",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "gap_exposed": resolution["gap_exposed"],
            })
            execute_exit(dt, bid, ask, mid)
            pending_exit = None
            pending_exit_target = None
            if target in (-1, 1):
                if entry_latency:
                    pending_entry = PendingEntry(target, dt)
                elif entry_eligible:
                    execute_entry(target, dt, bid, ask, mid)

        # Resolve one-bar entry latency only while flat.
        if pending_entry is not None and position == 0:
            resolution = pending_entry.resolve(dt, desired)
            side = pending_entry.side
            pending_entry = None
            events.append({
                "event_type": "PENDING_ENTRY_RESOLVED",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "resolution": resolution,
            })
            if resolution == "EXECUTE" and entry_eligible:
                execute_entry(side, dt, bid, ask, mid)

        if position == 0 and pending_entry is None and desired not in (None, 0) and entry_eligible:
            if entry_latency:
                pending_entry = PendingEntry(desired, dt)
                events.append({"event_type": "PENDING_ENTRY_CREATED", "symbol": symbol,
                               "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "side_value": desired})
            else:
                execute_entry(desired, dt, bid, ask, mid)

        elif (
            position != 0
            and pending_exit is None
            and desired is not None
            and bars_held >= 3
            and (desired == 0 or desired == -position)
        ):
            target = desired if desired == -position else 0
            if exit_latency:
                pending_exit = PendingExit(position, dt)
                pending_exit_target = target
                events.append({"event_type": "PENDING_EXIT_CREATED", "symbol": symbol,
                               "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "target_side": target})
            else:
                execute_exit(dt, bid, ask, mid)
                if target in (-1, 1) and not no_same_obs_reentry:
                    execute_entry(target, dt, bid, ask, mid)
                elif target in (-1, 1) and no_same_obs_reentry:
                    events.append({"event_type": "SAME_OBSERVATION_REENTRY_SUPPRESSED", "symbol": symbol,
                                   "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "side_value": target})

        mark_return = None
        if position != 0 and entry is not None:
            mark_exec = bid if position == 1 else ask
            if position == 1:
                mark_return = (mark_exec - entry["entry_execution_price"]) / entry["entry_execution_price"]
            else:
                mark_return = (entry["entry_execution_price"] - mark_exec) / entry["entry_execution_price"]
        marks.append({
            "symbol": symbol,
            "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "position": position,
            "mark_return": mark_return,
            "strategy_signal_available": raw is not None,
            "entry_eligible": entry_eligible,
        })
        previous_dt, previous_mid = dt, mid

    if position != 0 and entry is not None:
        censored.append({
            "symbol": symbol,
            "side": entry["side"],
            "entry_timestamp": entry["entry_timestamp"],
            "last_observed_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "RIGHT_CENSORED_END_OF_SAMPLE",
            "gap_exposure_count": entry["gap_exposure_count"],
            "gap_elapsed_seconds": entry["gap_elapsed_seconds"],
        })

    net_returns = [x["net_return"] for x in trades]
    gross_returns = [x["gross_return"] for x in trades]
    net_equity, net_dd = _max_drawdown(net_returns)
    gross_equity, gross_dd = _max_drawdown(gross_returns)
    return {
        "contract_version": "RND-0035-sensitive-kernel-v0.1",
        "trial_id": trial_id,
        "symbol": symbol,
        "authorized_years": sorted(AUTHORIZED_YEARS),
        "row_count": len(parsed),
        "gap_count": len(gaps),
        "completed_trade_count": len(trades),
        "censored_trade_count": len(censored),
        "completed_trade_net_equity_index": net_equity,
        "completed_trade_net_max_drawdown": net_dd,
        "completed_trade_gross_equity_index": gross_equity,
        "completed_trade_gross_max_drawdown": gross_dd,
        "total_execution_cost_drag": sum(x["execution_cost_drag"] for x in trades),
        "trades": trades,
        "censored_trades": censored,
        "gaps": gaps,
        "events": events,
        "marks": marks,
        "authority": {
            "strategy_selection": False,
            "portfolio_sizing": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "automatic_merge": False,
            "validation_open": False,
            "final_test_open": False,
            "human_review_required": True,
        },
    }
