#!/usr/bin/env python3
"""Outcome-blind parameterized robustness kernel for RND-0035.

R000 delegates directly to the frozen RND-0034 reconstruction engine.
Only predeclared A/C/D families are executable in this stage. E/F remain
fail-closed until their semantics are separately fixture-proven.

No network, broker, capital, promotion, validation or final-test authority.
"""

from __future__ import annotations

import copy

from gap_aware_m005_reconstruction import (
    AUTHORIZED_YEARS,
    M5_SECONDS,
    SYMBOLS,
    GapAwareM005Error,
    _max_drawdown,
    _trade_return,
    population_std,
    reconstruct_pair,
    validate_rows,
)


class RND0035KernelError(ValueError):
    pass


REFERENCE = {
    "fast_ma": 20,
    "slow_ma": 50,
    "volatility_window": 12,
    "volatility_ddof": 0,
    "volatility_threshold": 0.0005,
    "signal_delay_observed_bars": 1,
    "minimum_hold_observed_bars": 3,
    "sessions_utc": {
        "AUDUSD": (11, 14),
        "EURUSD": (11, 13),
        "GBPUSD": (11, 13),
        "USDJPY": (11, 13),
    },
}

A_CHANGES = {
    "A001": {"fast_ma": 16},
    "A002": {"fast_ma": 18},
    "A003": {"fast_ma": 22},
    "A004": {"fast_ma": 24},
    "A005": {"slow_ma": 40},
    "A006": {"slow_ma": 45},
    "A007": {"slow_ma": 55},
    "A008": {"slow_ma": 60},
    "A009": {"volatility_window": 8},
    "A010": {"volatility_window": 10},
    "A011": {"volatility_window": 14},
    "A012": {"volatility_window": 16},
    "A013": {"volatility_threshold": 0.0004},
    "A014": {"volatility_threshold": 0.00045},
    "A015": {"volatility_threshold": 0.00055},
    "A016": {"volatility_threshold": 0.0006},
    "A017": {"signal_delay_observed_bars": 2},
    "A018": {"signal_delay_observed_bars": 3},
    "A019": {"minimum_hold_observed_bars": 2},
    "A020": {"minimum_hold_observed_bars": 4},
    "A021": {"minimum_hold_observed_bars": 5},
}

C_TRANSFORMS = {
    "C001": "SHIFT_MINUS_1H",
    "C002": "SHIFT_PLUS_1H",
    "C003": "OPEN_PLUS_1H",
    "C004": "CLOSE_MINUS_1H",
}

D_BPS = {
    "D001": 0.5,
    "D002": 1.0,
    "D003": 2.0,
    "D004": 5.0,
}


def _session_transform(name):
    out = {}
    for symbol, (start, end) in REFERENCE["sessions_utc"].items():
        if name == "SHIFT_MINUS_1H":
            pair = (start - 1, end - 1)
        elif name == "SHIFT_PLUS_1H":
            pair = (start + 1, end + 1)
        elif name == "OPEN_PLUS_1H":
            pair = (start + 1, end)
        elif name == "CLOSE_MINUS_1H":
            pair = (start, end - 1)
        else:
            raise RND0035KernelError("unknown session transform")
        if not (0 <= pair[0] < pair[1] <= 24):
            raise RND0035KernelError("invalid transformed session")
        out[symbol] = pair
    return out


def trial_configuration(trial_id):
    if trial_id == "R000":
        return copy.deepcopy(REFERENCE)
    if trial_id in A_CHANGES:
        config = copy.deepcopy(REFERENCE)
        config.update(A_CHANGES[trial_id])
        _validate_config(config)
        return config
    if trial_id in C_TRANSFORMS:
        config = copy.deepcopy(REFERENCE)
        config["sessions_utc"] = _session_transform(C_TRANSFORMS[trial_id])
        _validate_config(config)
        return config
    if trial_id in D_BPS:
        return copy.deepcopy(REFERENCE)
    if trial_id.startswith(("E", "F")):
        raise RND0035KernelError("trial family not executable until fixture semantics are frozen")
    raise RND0035KernelError("undeclared or non-strategy trial id")


def _validate_config(config):
    required = set(REFERENCE)
    if set(config) != required:
        raise RND0035KernelError("configuration keys differ from frozen schema")
    for key in ("fast_ma", "slow_ma", "volatility_window", "signal_delay_observed_bars", "minimum_hold_observed_bars"):
        if isinstance(config[key], bool) or not isinstance(config[key], int) or config[key] <= 0:
            raise RND0035KernelError(f"{key}: positive integer required")
    if config["fast_ma"] >= config["slow_ma"]:
        raise RND0035KernelError("fast_ma must remain below slow_ma")
    if config["volatility_ddof"] != 0:
        raise RND0035KernelError("only population volatility is authorized")
    if not isinstance(config["volatility_threshold"], (int, float)) or config["volatility_threshold"] <= 0:
        raise RND0035KernelError("positive volatility threshold required")
    if set(config["sessions_utc"]) != set(SYMBOLS):
        raise RND0035KernelError("session universe must remain frozen")
    for start, end in config["sessions_utc"].values():
        if not (0 <= start < end <= 24):
            raise RND0035KernelError("invalid session window")
    return config


def _raw_signal(symbol, closes, returns, dt, config):
    need = max(config["slow_ma"], config["volatility_window"])
    if len(closes) < config["slow_ma"] or len(returns) < config["volatility_window"]:
        return None
    fast = sum(closes[-config["fast_ma"] :]) / config["fast_ma"]
    slow = sum(closes[-config["slow_ma"] :]) / config["slow_ma"]
    vol = population_std(returns[-config["volatility_window"] :])
    start, end = config["sessions_utc"][symbol]
    in_session = dt.weekday() < 5 and start <= dt.hour < end
    if not in_session or vol < config["volatility_threshold"]:
        return 0
    if fast > slow:
        return 1
    if fast < slow:
        return -1
    return 0


def _parameterized_reconstruct(symbol, rows, config, trial_id):
    if symbol not in SYMBOLS:
        raise RND0035KernelError("unsupported symbol")
    _validate_config(config)
    parsed = validate_rows(rows)

    closes, returns = [], []
    previous_dt = previous_mid = None
    delay_queue = []
    episode = 0
    position = 0
    bars_held = 0
    entry = None
    gaps, trades, censored, events, marks = [], [], [], [], []

    def reset_strategy_state():
        nonlocal closes, returns, previous_mid, delay_queue, episode
        closes, returns, delay_queue = [], [], []
        previous_mid = None
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

    reset_strategy_state()

    for dt, bid, ask, mid in parsed:
        if previous_dt is not None:
            delta = int((dt - previous_dt).total_seconds())
            if delta != M5_SECONDS:
                gap = {
                    "symbol": symbol,
                    "previous_timestamp": previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "next_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "elapsed_seconds": delta,
                    "position_was_open": position != 0,
                }
                gaps.append(gap)
                events.append({"event_type": "GAP", **gap})
                if delay_queue:
                    events.append({
                        "event_type": "PENDING_SIGNAL_CANCELLED",
                        "symbol": symbol,
                        "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "pending_signal_count": len(delay_queue),
                        "reason": "OBSERVATION_DISCONTINUITY",
                    })
                if position != 0 and entry is not None:
                    entry["gap_exposure_count"] += 1
                    entry["gap_elapsed_seconds"] += delta
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

        raw = _raw_signal(symbol, closes, returns, dt, config)
        desired = None
        if raw is not None:
            delay_queue.append(raw)
            events.append({
                "event_type": "RAW_SIGNAL",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal": raw,
            })
            if len(delay_queue) > config["signal_delay_observed_bars"]:
                desired = delay_queue.pop(0)
        if desired is not None:
            events.append({
                "event_type": "DELAYED_SIGNAL",
                "symbol": symbol,
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal": desired,
            })

        if position != 0:
            bars_held += 1

        if position == 0 and desired not in (None, 0):
            position = desired
            bars_held = 0
            entry = open_trade(position, dt, bid, ask, mid)
        elif position != 0 and desired is not None and bars_held >= config["minimum_hold_observed_bars"]:
            if desired == 0 or desired == -position:
                completed = complete_trade(entry, dt, bid, ask, mid, bars_held)
                trades.append(completed)
                old_side = position
                position = 0
                bars_held = 0
                entry = None
                if desired == -old_side:
                    position = desired
                    entry = open_trade(position, dt, bid, ask, mid)

        mark_return = None
        if position != 0 and entry is not None:
            mark_exec = bid if position == 1 else ask
            mark_return = (
                (mark_exec - entry["entry_execution_price"]) / entry["entry_execution_price"]
                if position == 1
                else (entry["entry_execution_price"] - mark_exec) / entry["entry_execution_price"]
            )
        marks.append({
            "symbol": symbol,
            "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "position": position,
            "mark_return": mark_return,
            "strategy_signal_available": raw is not None,
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
        "contract_version": "RND-0035-adversarial-kernel-v0.1",
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


def _apply_cost_stress(reference_result, bps, trial_id):
    result = copy.deepcopy(reference_result)
    result["contract_version"] = "RND-0035-adversarial-kernel-v0.1"
    result["trial_id"] = trial_id
    drag = bps / 10000.0
    for trade in result["trades"]:
        trade["reference_net_return"] = trade["net_return"]
        trade["additional_round_trip_bps"] = bps
        trade["net_return"] = trade["net_return"] - drag
        trade["execution_cost_drag"] = trade["gross_return"] - trade["net_return"]
    net_returns = [x["net_return"] for x in result["trades"]]
    net_equity, net_dd = _max_drawdown(net_returns)
    result["completed_trade_net_equity_index"] = net_equity
    result["completed_trade_net_max_drawdown"] = net_dd
    result["total_execution_cost_drag"] = sum(x["execution_cost_drag"] for x in result["trades"])
    return result


def run_trial_pair(trial_id, symbol, rows):
    """Run one declared pair-level RND-0035 strategy trial.

    This function never opens the global outcome gate. It is intended for
    fixture/conformance use until the governed runner separately authorizes
    historical evidence execution.
    """
    if trial_id == "R000":
        return reconstruct_pair(symbol, rows)
    if trial_id in D_BPS:
        return _apply_cost_stress(reconstruct_pair(symbol, rows), D_BPS[trial_id], trial_id)
    config = trial_configuration(trial_id)
    return _parameterized_reconstruct(symbol, rows, config, trial_id)
