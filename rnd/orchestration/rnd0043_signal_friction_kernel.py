#!/usr/bin/env python3
"""RND-0043 isolated development research kernel.

Preserves frozen R000 mechanics and adds one optional entry-eligibility gate:
contemporaneous volatility-to-spread ratio. Pure local computation only.
"""
from __future__ import annotations

import math
from datetime import datetime

import gap_aware_m005_reconstruction as frozen

SYMBOLS = frozen.SYMBOLS
SESSIONS = frozen.SESSIONS
FAST = frozen.FAST
SLOW = frozen.SLOW
VOL_WINDOW = frozen.VOL_WINDOW
VOL_THRESHOLD = frozen.VOL_THRESHOLD
MIN_HOLD_BARS = frozen.MIN_HOLD_BARS
M5_SECONDS = frozen.M5_SECONDS
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
AUTHORIZED_ARMS = {"F000": None, "F001": 3.0, "F002": 5.0, "F003": 8.0}


class RND0043KernelError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RND0043KernelError(message)


def _utc(value):
    _require(isinstance(value, str) and value.endswith("Z"), "timestamp must be UTC ending Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0043KernelError("invalid timestamp") from exc
    _require(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _require(dt.year in AUTHORIZED_YEARS, "RND-0043 evaluation outside development years prohibited")
    return dt


def _price(value, role):
    _require(not isinstance(value, bool), f"{role}: positive finite price required")
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0043KernelError(f"{role}: positive finite price required") from exc
    _require(math.isfinite(x) and x > 0, f"{role}: positive finite price required")
    return x


def validate_rows(rows):
    _require(isinstance(rows, list) and rows, "rows: non-empty list required")
    out, seen, previous = [], set(), None
    for i, row in enumerate(rows):
        _require(isinstance(row, dict), f"rows[{i}]: mapping required")
        required = {"timestamp_utc", "complete", "bid_close", "ask_close", "mid_close"}
        _require(required.issubset(row), f"rows[{i}]: execution fields missing")
        _require(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _require(dt not in seen, "rows: duplicate timestamp")
        _require(previous is None or dt > previous, "rows: timestamps out of order")
        seen.add(dt); previous = dt
        bid = _price(row["bid_close"], "bid_close")
        ask = _price(row["ask_close"], "ask_close")
        mid = _price(row["mid_close"], "mid_close")
        _require(bid <= mid <= ask, "rows: bid/mid/ask ordering invalid")
        out.append((dt, bid, ask, mid))
    return out


def signal_to_friction_ratio(returns, bid, ask, mid):
    """Compute the predeclared ratio from the current observation only."""
    _require(isinstance(returns, list) and len(returns) >= VOL_WINDOW, "ratio: 12 contiguous returns required")
    spread = (ask - bid) / mid
    _require(math.isfinite(spread) and spread > 0, "ratio: positive relative spread required")
    sigma = frozen.population_std(returns[-VOL_WINDOW:])
    ratio = sigma / spread
    _require(math.isfinite(ratio) and ratio >= 0, "ratio: finite nonnegative value required")
    return {"sigma12_mid_return": sigma, "relative_spread": spread, "signal_to_friction": ratio}


def raw_signal(symbol, closes, returns, dt, bid, ask, mid, arm):
    """Return base R000 raw signal plus entry eligibility metadata.

    The ratio never changes an exit signal. It controls only whether a nonzero
    raw signal may later open a new position after the frozen one-bar delay.
    """
    _require(symbol in SYMBOLS, "unsupported symbol")
    _require(arm in AUTHORIZED_ARMS, "arm outside predeclared RND-0043 set")
    if len(closes) < SLOW or len(returns) < VOL_WINDOW:
        return None, True, None
    fast = sum(closes[-FAST:]) / FAST
    slow = sum(closes[-SLOW:]) / SLOW
    vol = frozen.population_std(returns[-VOL_WINDOW:])
    start, end = SESSIONS[symbol]
    in_session = dt.weekday() < 5 and start <= dt.hour < end
    if not in_session or vol < VOL_THRESHOLD:
        return 0, True, None
    ratio = signal_to_friction_ratio(returns, bid, ask, mid)
    threshold = AUTHORIZED_ARMS[arm]
    eligible = threshold is None or ratio["signal_to_friction"] >= threshold
    if fast > slow:
        return 1, eligible, ratio
    if fast < slow:
        return -1, eligible, ratio
    return 0, True, ratio


def reconstruct_pair(symbol, rows, arm):
    _require(symbol in SYMBOLS, "unsupported symbol")
    _require(arm in AUTHORIZED_ARMS, "arm outside predeclared RND-0043 set")
    parsed = validate_rows(rows)
    closes, returns, gaps, trades, censored, marks = [], [], [], [], [], []
    previous_dt = previous_mid = previous_raw = None
    previous_entry_eligible = True
    episode = 0; position = 0; bars_held = 0; entry = None
    rejected_entry_signal_count = 0; eligible_entry_ratios = []

    def reset_state():
        nonlocal closes, returns, previous_mid, previous_raw, previous_entry_eligible, episode
        closes=[]; returns=[]; previous_mid=None; previous_raw=None; previous_entry_eligible=True; episode += 1

    def open_trade(side, dt, bid, ask, mid):
        return {"symbol":symbol,"side":"long" if side==1 else "short","side_value":side,"entry_timestamp":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"entry_execution_price":ask if side==1 else bid,"entry_mid_price":mid,"episode":episode,"gap_exposure_count":0,"gap_elapsed_seconds":0}

    def complete_trade(current, dt, bid, ask, mid, held):
        side=current["side_value"]; exit_exec=bid if side==1 else ask
        gross,net=frozen._trade_return(side,current["entry_execution_price"],exit_exec,current["entry_mid_price"],mid)
        return {"symbol":symbol,"side":current["side"],"entry_timestamp":current["entry_timestamp"],"exit_timestamp":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"entry_execution_price":current["entry_execution_price"],"exit_execution_price":exit_exec,"entry_mid_price":current["entry_mid_price"],"exit_mid_price":mid,"gross_return":gross,"net_return":net,"execution_cost_drag":gross-net,"holding_bars":held,"gap_exposure_count":current.get("gap_exposure_count",0),"gap_elapsed_seconds":current.get("gap_elapsed_seconds",0),"gap_exposed":current.get("gap_exposure_count",0)>0,"exit_year":dt.year,"episode":current["episode"],"status":"COMPLETE"}

    reset_state()
    for dt,bid,ask,mid in parsed:
        if previous_dt is not None:
            delta=int((dt-previous_dt).total_seconds())
            if delta != M5_SECONDS:
                gaps.append({"symbol":symbol,"previous_timestamp":previous_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"next_timestamp":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"elapsed_seconds":delta,"position_was_open":position!=0})
                if position!=0 and entry is not None:
                    entry["gap_exposure_count"] += 1; entry["gap_elapsed_seconds"] += delta
                reset_state()
        if previous_mid is not None:
            returns.append(mid/previous_mid-1.0)
        closes.append(mid)

        raw, entry_eligible, ratio = raw_signal(symbol,closes,returns,dt,bid,ask,mid,arm)
        desired = previous_raw
        desired_entry_eligible = previous_entry_eligible
        previous_raw = raw
        previous_entry_eligible = entry_eligible

        if raw is not None and raw != 0 and ratio is not None:
            if entry_eligible:
                eligible_entry_ratios.append(ratio["signal_to_friction"])
            else:
                rejected_entry_signal_count += 1

        if position!=0:
            bars_held += 1

        if position==0 and desired is not None and desired!=0 and desired_entry_eligible:
            position=desired; bars_held=0; entry=open_trade(position,dt,bid,ask,mid)
        elif position!=0 and desired is not None and desired==0 and bars_held>=MIN_HOLD_BARS:
            trades.append(complete_trade(entry,dt,bid,ask,mid,bars_held)); position=0; bars_held=0; entry=None
        elif position!=0 and desired is not None and desired==-position and bars_held>=MIN_HOLD_BARS:
            trades.append(complete_trade(entry,dt,bid,ask,mid,bars_held)); position=0; bars_held=0; entry=None
            if desired_entry_eligible:
                position=desired; entry=open_trade(position,dt,bid,ask,mid)

        mark_return=None
        if position!=0 and entry is not None:
            mark_exec=bid if position==1 else ask
            mark_return=(mark_exec-entry["entry_execution_price"])/entry["entry_execution_price"] if position==1 else (entry["entry_execution_price"]-mark_exec)/entry["entry_execution_price"]
        marks.append({"symbol":symbol,"timestamp":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"position":position,"mark_return":mark_return})
        previous_dt=dt; previous_mid=mid

    if position!=0 and entry is not None:
        censored.append({"symbol":symbol,"entry_timestamp":entry["entry_timestamp"],"status":"RIGHT_CENSORED_END_OF_SAMPLE"})
    net=[x["net_return"] for x in trades]; gross=[x["gross_return"] for x in trades]
    net_eq,net_dd=frozen._max_drawdown(net); gross_eq,gross_dd=frozen._max_drawdown(gross)
    return {"contract_version":"RND0043-signal-friction-kernel-v1","symbol":symbol,"arm":arm,"ratio_threshold":AUTHORIZED_ARMS[arm],"authorized_years":sorted(AUTHORIZED_YEARS),"row_count":len(parsed),"contiguous_episode_count":episode,"gap_count":len(gaps),"completed_trade_count":len(trades),"censored_trade_count":len(censored),"net_hit_rate":sum(1 for x in net if x>0)/len(net) if net else None,"completed_trade_net_equity_index":net_eq,"completed_trade_net_max_drawdown":net_dd,"completed_trade_gross_equity_index":gross_eq,"completed_trade_gross_max_drawdown":gross_dd,"total_execution_cost_drag":sum(x["execution_cost_drag"] for x in trades),"completed_trade_net_return_sum":sum(net),"rejected_entry_signal_count":rejected_entry_signal_count,"eligible_entry_signal_to_friction_ratios":eligible_entry_ratios,"trades":trades,"gaps":gaps,"marks":marks,"authority":{"development_outcomes":False,"strategy_selection":False,"validation_access":False,"reserved_final_open":False,"broker_writes":False,"capital_authority":False,"automatic_promotion":False,"automatic_merge":False}}
