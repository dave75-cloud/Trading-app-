#!/usr/bin/env python3
"""
KQTRL M006e.1 — OANDA-authoritative prospective observer.

ZERO-WRITE execution architecture.

Purpose:
- OANDA practice is the authoritative market-data source.
- Fetch completed M5 midpoint candles only.
- Reproduce frozen Candidate-A signal/state logic exactly:
    MA20
    MA50
    vol12 >= 0.0005
    pandas std(ddof=0)
    AUDUSD 11:00-14:00 UTC
    EURUSD/GBPUSD/USDJPY 11:00-13:00 UTC
    one-bar delayed desired signal
    minimum hold = 3 bars
- Maintain a completely separate prospective watermark/state.
- Gap protection:
    >4 pending in-session bars while flat -> quarantine/re-boundary
    >4 pending in-session bars while non-flat -> FAIL CLOSED
- Generate observation events only.
- No pricing orders, no order payload construction, no POST/PUT/PATCH/DELETE.
- Does not modify canonical M005 or M006c state.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd


PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")

PAIR_TO_INSTRUMENT = {
    "AUDUSD": "AUD_USD",
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
}

FAST = 20
SLOW = 50
VOL_WINDOW = 12
VOL_THRESHOLD = 0.0005
MIN_HOLD_BARS = 3
MAX_PENDING_IN_SESSION_BARS = 4

EVENT_COLUMNS = [
    "cycle_id",
    "provider",
    "pair",
    "bar_ts_utc",
    "event_type",
    "old_position",
    "new_position",
    "desired_delayed_signal",
    "close",
    "fast_ma",
    "slow_ma",
    "volatility",
    "volatility_ok",
    "in_session",
    "bars_held_after",
    "entry_ts_after",
    "entry_price_after",
    "observation_only",
]


def session_hours(pair: str) -> tuple[int, int]:
    if pair == "AUDUSD":
        return 11, 14
    return 11, 13


def base_url() -> str:
    env = os.environ.get("OANDA_ENV", "").strip().lower()

    if env != "practice":
        raise SystemExit(
            "FAIL_CLOSED: M006e.1 requires OANDA_ENV=practice"
        )

    return "https://api-fxpractice.oanda.com"


def request_json(path: str, token: str) -> tuple[int, bytes, dict[str, Any]]:
    # GET only.
    req = urllib.request.Request(
        base_url() + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept-Datetime-Format": "RFC3339",
            "User-Agent": "KQTRL-M006e1",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            status = response.status

    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code

    except urllib.error.URLError as exc:
        raise RuntimeError(f"OANDA connection failure: {exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"OANDA invalid JSON: {exc}") from exc

    return status, raw, payload


def parse_oanda(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []

    for candle in payload.get("candles") or []:
        # Authoritative observer accepts completed bars only.
        if not candle.get("complete", False):
            continue

        mid = candle.get("mid") or {}

        rows.append(
            {
                "ts": pd.to_datetime(candle["time"], utc=True),
                "o": float(mid["o"]),
                "h": float(mid["h"]),
                "l": float(mid["l"]),
                "c": float(mid["c"]),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["ts", "o", "h", "l", "c"])

    return (
        pd.DataFrame(rows)
        .sort_values("ts")
        .drop_duplicates("ts", keep="last")
        .reset_index(drop=True)
    )


def fetch_bars(
    pair: str,
    token: str,
    count: int,
) -> tuple[pd.DataFrame, bytes]:
    instrument = PAIR_TO_INSTRUMENT[pair]

    qs = urllib.parse.urlencode(
        {
            "price": "M",
            "granularity": "M5",
            "count": min(max(count, 100), 5000),
            "smooth": "false",
        }
    )

    status, raw, payload = request_json(
        f"/v3/instruments/{instrument}/candles?{qs}",
        token,
    )

    if status != 200:
        raise RuntimeError(
            f"OANDA candles failed for {pair}: HTTP {status}"
        )

    bars = parse_oanda(payload)

    if bars.empty:
        raise RuntimeError(f"No completed OANDA M5 candles for {pair}")

    return bars, raw


def add_indicators(df: pd.DataFrame, pair: str) -> pd.DataFrame:
    out = df.copy()

    out["ret"] = out["c"].pct_change()

    out["fast_ma"] = (
        out["c"]
        .rolling(FAST, min_periods=FAST)
        .mean()
    )

    out["slow_ma"] = (
        out["c"]
        .rolling(SLOW, min_periods=SLOW)
        .mean()
    )

    out["vol"] = (
        out["ret"]
        .rolling(VOL_WINDOW, min_periods=VOL_WINDOW)
        .std(ddof=0)
    )

    start, end = session_hours(pair)

    out["in_session"] = (
        (out["ts"].dt.hour >= start)
        & (out["ts"].dt.hour < end)
        & (out["ts"].dt.dayofweek < 5)
    )

    out["vol_ok"] = out["vol"] >= VOL_THRESHOLD

    ready = (
        out["fast_ma"].notna()
        & out["slow_ma"].notna()
        & out["vol"].notna()
    )

    out["raw_signal"] = 0

    long_mask = (
        ready
        & out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] > out["slow_ma"])
    )

    short_mask = (
        ready
        & out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] < out["slow_ma"])
    )

    out.loc[long_mask, "raw_signal"] = 1
    out.loc[short_mask, "raw_signal"] = -1

    out["delayed_signal"] = (
        out["raw_signal"]
        .shift(1)
        .fillna(0)
        .astype(int)
    )

    return out


def position_name(value: int) -> str:
    return {
        1: "long",
        -1: "short",
        0: "flat",
    }[int(value)]


def count_pending_session_bars(
    pair: str,
    last_processed: pd.Timestamp | None,
    newest: pd.Timestamp | None,
) -> int:
    if last_processed is None or newest is None:
        return 0

    lp = pd.Timestamp(last_processed)
    nw = pd.Timestamp(newest)

    if lp.tzinfo is None:
        lp = lp.tz_localize("UTC")
    else:
        lp = lp.tz_convert("UTC")

    if nw.tzinfo is None:
        nw = nw.tz_localize("UTC")
    else:
        nw = nw.tz_convert("UTC")

    if nw <= lp:
        return 0

    start, end = session_hours(pair)

    idx = pd.date_range(
        lp + pd.Timedelta(minutes=5),
        nw,
        freq="5min",
        tz="UTC",
    )

    if len(idx) == 0:
        return 0

    mask = (
        (idx.dayofweek < 5)
        & (idx.hour >= start)
        & (idx.hour < end)
    )

    return int(mask.sum())


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")

    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    os.replace(tmp, path)


def default_pair_state() -> dict[str, Any]:
    return {
        "position": 0,
        "bars_held": 0,
        "entry_ts": "",
        "entry_price": None,
        "last_observed_signal": 0,
    }


def establish_boundary(
    pair: str,
    bars: pd.DataFrame,
    pair_state: dict[str, Any],
) -> tuple[dict[str, Any], pd.Timestamp]:
    enriched = add_indicators(bars, pair)

    newest = enriched["ts"].max()

    pair_state.setdefault("position", 0)
    pair_state.setdefault("bars_held", 0)
    pair_state.setdefault("entry_ts", "")
    pair_state.setdefault("entry_price", None)

    pair_state["last_observed_signal"] = int(
        enriched.loc[
            enriched["ts"] == newest,
            "delayed_signal",
        ].iloc[-1]
    )

    return pair_state, newest


def process_pair(
    pair: str,
    bars: pd.DataFrame,
    pair_state: dict[str, Any],
    last_processed: pd.Timestamp,
    cycle_id: str,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    pd.Timestamp,
    dict[str, Any] | None,
]:
    enriched = add_indicators(bars, pair)
    newest = enriched["ts"].max()

    pending = count_pending_session_bars(
        pair,
        last_processed,
        newest,
    )

    if pending > MAX_PENDING_IN_SESSION_BARS:
        current_position = int(pair_state.get("position", 0))

        if current_position != 0:
            raise RuntimeError(
                f"M006e.1 FAIL-CLOSED {pair}: "
                f"{pending} pending in-session bars after "
                f"{last_processed}, while authoritative "
                f"position={position_name(current_position)}. "
                f"Historical replay blocked pending manual review."
            )

        pair_state, boundary = establish_boundary(
            pair,
            bars,
            pair_state,
        )

        quarantine = {
            "cycle_id": cycle_id,
            "pair": pair,
            "previous_watermark": str(last_processed),
            "new_boundary": str(boundary),
            "pending_in_session_bars": pending,
            "classification": "NON_PROSPECTIVE",
        }

        return [], pair_state, boundary, quarantine

    new_rows = enriched[
        enriched["ts"] > last_processed
    ].copy()

    events = []
    newest_processed = last_processed

    position = int(pair_state.get("position", 0))
    bars_held = int(pair_state.get("bars_held", 0))
    entry_ts = str(pair_state.get("entry_ts", ""))
    entry_price = pair_state.get("entry_price")

    for _, row in new_rows.iterrows():
        ts = row["ts"]
        desired = int(row["delayed_signal"])
        close = float(row["c"])

        newest_processed = ts

        if position != 0:
            bars_held += 1

        old_position = position
        event_type = ""

        if position == 0 and desired != 0:
            position = desired
            bars_held = 0
            entry_ts = ts.isoformat()
            entry_price = close
            event_type = "entry"

        elif (
            position != 0
            and desired == 0
            and bars_held >= MIN_HOLD_BARS
        ):
            position = 0
            event_type = "exit"

        elif (
            position != 0
            and desired == -position
            and bars_held >= MIN_HOLD_BARS
        ):
            position = desired
            bars_held = 0
            entry_ts = ts.isoformat()
            entry_price = close
            event_type = "reversal"

        if event_type:
            events.append(
                {
                    "cycle_id": cycle_id,
                    "provider": "oanda",
                    "pair": pair,
                    "bar_ts_utc": ts.isoformat(),
                    "event_type": event_type,
                    "old_position": position_name(old_position),
                    "new_position": position_name(position),
                    "desired_delayed_signal": position_name(desired),
                    "close": close,
                    "fast_ma": (
                        None
                        if pd.isna(row["fast_ma"])
                        else float(row["fast_ma"])
                    ),
                    "slow_ma": (
                        None
                        if pd.isna(row["slow_ma"])
                        else float(row["slow_ma"])
                    ),
                    "volatility": (
                        None
                        if pd.isna(row["vol"])
                        else float(row["vol"])
                    ),
                    "volatility_ok": bool(row["vol_ok"]),
                    "in_session": bool(row["in_session"]),
                    "bars_held_after": bars_held,
                    "entry_ts_after": entry_ts,
                    "entry_price_after": entry_price,
                    "observation_only": True,
                }
            )

    pair_state.update(
        {
            "position": position,
            "bars_held": bars_held,
            "entry_ts": entry_ts,
            "entry_price": entry_price,
            "last_observed_signal": (
                int(new_rows["delayed_signal"].iloc[-1])
                if not new_rows.empty
                else pair_state.get("last_observed_signal", 0)
            ),
        }
    )

    return events, pair_state, newest_processed, None


def write_event_file(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        events,
        columns=EVENT_COLUMNS,
    ).to_csv(path, index=False)


def self_test() -> int:
    # Synthetic state-machine sequence only.
    # No network calls.
    times = pd.date_range(
        "2026-08-19T12:00:00Z",
        periods=20,
        freq="5min",
    )

    position = 0
    bars_held = 0

    # Directly test frozen transition semantics.
    desired_sequence = [
        1, 1, 1, 1, 0,
        -1, -1, -1, -1, 0,
    ]

    transitions = []

    for i, desired in enumerate(desired_sequence):
        if position != 0:
            bars_held += 1

        old = position
        event = ""

        if position == 0 and desired != 0:
            position = desired
            bars_held = 0
            event = "entry"

        elif (
            position != 0
            and desired == 0
            and bars_held >= MIN_HOLD_BARS
        ):
            position = 0
            event = "exit"

        elif (
            position != 0
            and desired == -position
            and bars_held >= MIN_HOLD_BARS
        ):
            position = desired
            bars_held = 0
            event = "reversal"

        if event:
            transitions.append(
                (
                    times[i].isoformat(),
                    event,
                    position_name(old),
                    position_name(position),
                )
            )

    expected = [
        ("entry", "flat", "long"),
        ("exit", "long", "flat"),
        ("entry", "flat", "short"),
        ("exit", "short", "flat"),
    ]

    actual = [
        (e, old, new)
        for _, e, old, new in transitions
    ]

    print("KQTRL M006e.1 — OFFLINE SELF-TEST")
    print("=" * 72)

    for row in transitions:
        print(row)

    if actual != expected:
        print("SELF_TEST: FAIL")
        return 1

    print()
    print("Final position: flat")
    print("Network calls: 0")
    print("Order payload construction: NONE")
    print("OANDA write methods implemented: NONE")
    print("Canonical M005 modified: FALSE")
    print("M006c state modified: FALSE")
    print("M006E1_SELF_TEST: PASS")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=(
            "./data/research_runs/"
            "M006E_OANDA_AUTHORITATIVE"
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=2000,
    )

    parser.add_argument(
        "--initialize",
        action="store_true",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    token = os.environ.get(
        "OANDA_API_TOKEN",
        "",
    ).strip()

    account = os.environ.get(
        "OANDA_ACCOUNT_ID",
        "",
    ).strip()

    if not token or not account:
        raise SystemExit(
            "FAIL_CLOSED: missing OANDA practice credentials"
        )

    # Account is deliberately not used for trading.
    # Presence is required only as part of the practice environment contract.
    _ = account

    root = Path(args.root)
    state_path = root / "state" / "observer_state.json"

    cycle_id = pd.Timestamp.now(
        tz="UTC"
    ).strftime("%Y%m%dT%H%M%SZ")

    if args.initialize and state_path.exists():
        raise SystemExit(
            "FAIL_CLOSED: state already exists; "
            "refusing to reinitialize."
        )

    if not args.initialize and not state_path.exists():
        raise SystemExit(
            "FAIL_CLOSED: M006e.1 state does not exist.\n"
            "Run once with --initialize to establish "
            "the prospective boundary."
        )

    state = (
        {
            "version": "M006e.1",
            "initialized_at_utc": pd.Timestamp.now(
                tz="UTC"
            ).isoformat(),
            "provider": "oanda",
            "authority": "OANDA",
            "mode": "OBSERVATION_ONLY_ZERO_WRITE",
            "pairs": {},
            "watermarks": {},
            "gap_quarantines": [],
            "order_endpoints_invoked": False,
            "canonical_m005_modified": False,
            "m006c_state_modified": False,
        }
        if args.initialize
        else json.loads(state_path.read_text())
    )

    all_events = []
    quarantines = []
    latest = {}

    for pair in PAIRS:
        bars, _raw = fetch_bars(
            pair,
            token,
            args.count,
        )

        newest = bars["ts"].max()

        latest[pair] = newest.isoformat()

        pair_state = state["pairs"].get(
            pair,
            default_pair_state(),
        )

        if args.initialize:
            pair_state, boundary = establish_boundary(
                pair,
                bars,
                pair_state,
            )

            state["pairs"][pair] = pair_state
            state["watermarks"][pair] = boundary.isoformat()

            continue

        last_processed = pd.to_datetime(
            state["watermarks"][pair],
            utc=True,
        )

        (
            events,
            pair_state,
            newest_processed,
            quarantine,
        ) = process_pair(
            pair,
            bars,
            pair_state,
            last_processed,
            cycle_id,
        )

        state["pairs"][pair] = pair_state
        state["watermarks"][pair] = (
            newest_processed.isoformat()
        )

        all_events.extend(events)

        if quarantine is not None:
            quarantines.append(quarantine)
            state["gap_quarantines"].append(
                quarantine
            )

    state["last_cycle_id"] = cycle_id
    state["last_cycle_utc"] = pd.Timestamp.now(
        tz="UTC"
    ).isoformat()

    state["latest_completed_bar"] = latest
    state["order_endpoints_invoked"] = False
    state["canonical_m005_modified"] = False
    state["m006c_state_modified"] = False

    atomic_json(
        state_path,
        state,
    )

    if not args.initialize:
        write_event_file(
            root / "events" / f"cycle_{cycle_id}.csv",
            all_events,
        )

        report = {
            "cycle_id": cycle_id,
            "mode": "OBSERVATION_ONLY_ZERO_WRITE",
            "authority": "OANDA",
            "events": len(all_events),
            "entries": sum(
                e["event_type"] == "entry"
                for e in all_events
            ),
            "exits": sum(
                e["event_type"] == "exit"
                for e in all_events
            ),
            "reversals": sum(
                e["event_type"] == "reversal"
                for e in all_events
            ),
            "gap_quarantines": quarantines,
            "positions_after": {
                pair: position_name(
                    state["pairs"][pair]["position"]
                )
                for pair in PAIRS
            },
            "latest_completed_bar": latest,
            "order_payloads_constructed": 0,
            "oanda_write_requests_performed": 0,
            "order_endpoints_invoked": False,
            "canonical_m005_modified": False,
            "m006c_state_modified": False,
        }

        atomic_json(
            root / "reports" / f"cycle_{cycle_id}.json",
            report,
        )

    print("KQTRL M006e.1 — OANDA AUTHORITATIVE OBSERVER")
    print("=" * 78)
    print("Environment: OANDA practice")
    print("Authority: OANDA completed M5 midpoint candles")
    print("Mode: OBSERVATION ONLY / ZERO WRITE")
    print("Cycle:", cycle_id)

    if args.initialize:
        print("Action: prospective boundary initialized")
        print("Historical events replayed: 0")
    else:
        print("Events:", len(all_events))
        print(
            "Positions:",
            ", ".join(
                f"{p}={position_name(state['pairs'][p]['position'])}"
                for p in PAIRS
            ),
        )

    for pair in PAIRS:
        print(
            f"{pair}: latest_completed="
            f"{latest[pair]} "
            f"watermark={state['watermarks'][pair]}"
        )

    if quarantines:
        print("Gap quarantines:")
        for q in quarantines:
            print(
                f"  {q['pair']}: "
                f"{q['pending_in_session_bars']} "
                f"pending session bars "
                f"-> NON_PROSPECTIVE"
            )

    print("Order payloads constructed: 0")
    print("OANDA write requests performed: 0")
    print("Order endpoints invoked: FALSE")
    print("Canonical M005 modified: FALSE")
    print("M006c state modified: FALSE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
