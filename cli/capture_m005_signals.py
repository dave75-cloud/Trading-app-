#!/usr/bin/env python3
"""
KQTRL M005 v1.1 — prospective signal capture.

Reads a same-day candidate-signal CSV, validates frozen sessions, snapshots the
raw file, allocates simultaneous signals using the frozen pro-rata basket rule,
and appends immutable rows to the active M005 signals log.

This script does not reconstruct missed signals and does not create trades from
future information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict

import pandas as pd

PAIR_CURRENCIES = {
    "AUDUSD": ("AUD", "USD"),
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
}
CURRENCIES = ["AUD", "EUR", "GBP", "USD", "JPY"]
EPS = 1e-10

REQUIRED_INPUT = [
    "signal_id",
    "symbol",
    "side",
    "signal_timestamp",
    "expected_entry_timestamp",
    "model_entry_price",
    "observed_bid",
    "observed_ask",
    "executable_entry_price",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def gross_currency_legs(symbol: str, lev: float) -> Dict[str, float]:
    base, quote = PAIR_CURRENCIES[symbol]
    return {base: lev, quote: lev}

def load_existing_exposure(run: Path) -> tuple[float, Dict[str, float]]:
    ledger = pd.read_csv(run / "logs/ledger_5m.csv")
    if ledger.empty:
        return 0.0, {c: 0.0 for c in CURRENCIES}
    last = ledger.iloc[-1]
    gross = float(last["gross_exposure"])
    ccy = {
        "AUD": float(last["aud_gross_exposure"]),
        "EUR": float(last["eur_gross_exposure"]),
        "GBP": float(last["gbp_gross_exposure"]),
        "USD": float(last["usd_gross_exposure"]),
        "JPY": float(last["jpy_gross_exposure"]),
    }
    return gross, ccy

def pro_rata_group(
    group: pd.DataFrame,
    gross_before: float,
    ccy_before: Dict[str, float],
    per_trade_max: float,
    gross_cap: float,
    currency_cap: float,
) -> Dict[str, float]:
    ids = list(group["signal_id"].astype(str))
    symbols = dict(zip(group["signal_id"].astype(str), group["symbol"]))
    assigned = {sid: 0.0 for sid in ids}

    gross = gross_before
    ccy = ccy_before.copy()
    unresolved = set(ids)

    while unresolved:
        room_each = min(per_trade_max - assigned[sid] for sid in unresolved)
        if room_each <= EPS:
            break

        gross_each = max(0.0, gross_cap - gross) / len(unresolved)

        currency_each = float("inf")
        for curr in CURRENCIES:
            users = sum(
                1 for sid in unresolved
                if curr in gross_currency_legs(symbols[sid], 1.0)
            )
            if users:
                currency_each = min(
                    currency_each,
                    max(0.0, currency_cap - ccy[curr]) / users,
                )

        inc = min(room_each, gross_each, currency_each)
        if inc <= EPS:
            break

        for sid in unresolved:
            assigned[sid] += inc
            gross += inc
            for curr, val in gross_currency_legs(symbols[sid], inc).items():
                ccy[curr] += val

        full = {sid for sid in unresolved if per_trade_max - assigned[sid] <= EPS}
        if full:
            unresolved -= full
        else:
            break

    return assigned

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--signals-file", required=True)
    args = ap.parse_args()

    run = Path(args.run_dir)
    source = Path(args.signals_file)
    config = json.loads((run / "metadata/frozen_config.json").read_text())

    df = pd.read_csv(source)
    missing = set(REQUIRED_INPUT) - set(df.columns)
    if missing:
        raise SystemExit(f"Missing input columns: {sorted(missing)}")
    if df.empty:
        raise SystemExit("Signal input is empty")

    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["side"] = df["side"].astype(str).str.lower()
    df["signal_timestamp"] = pd.to_datetime(
        df["signal_timestamp"], utc=True, errors="raise"
    )
    df["expected_entry_timestamp"] = pd.to_datetime(
        df["expected_entry_timestamp"], utc=True, errors="raise"
    )

    for row in df.itertuples(index=False):
        if row.symbol not in config["sessions_utc"]:
            raise SystemExit(f"Unsupported symbol: {row.symbol}")
        start, end = config["sessions_utc"][row.symbol]
        if not (start <= row.signal_timestamp.hour < end):
            raise SystemExit(
                f"{row.signal_id}: outside frozen session "
                f"{row.symbol} hour={row.signal_timestamp.hour}"
            )
        if row.side not in {"long", "short"}:
            raise SystemExit(f"{row.signal_id}: invalid side {row.side}")

    existing = pd.read_csv(run / "logs/signals.csv")
    existing_ids = set(existing["signal_id"].astype(str)) if not existing.empty else set()
    duplicate_ids = sorted(set(df["signal_id"].astype(str)) & existing_ids)
    if duplicate_ids:
        raise SystemExit(f"Signal IDs already exist: {duplicate_ids[:10]}")

    raw_dir = run / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snapshot = raw_dir / f"signals_{stamp}_{source.name}"
    shutil.copy2(source, snapshot)
    digest = sha256(snapshot)

    gross, ccy = load_existing_exposure(run)
    per_trade_max = float(config["risk"]["per_trade_max_leverage"])
    gross_cap = float(config["risk"]["portfolio_gross_cap"])
    currency_cap = float(config["risk"]["gross_currency_leg_cap"])

    allocations = {}
    for ts, group in df.groupby("expected_entry_timestamp", sort=True):
        group_alloc = pro_rata_group(
            group, gross, ccy, per_trade_max, gross_cap, currency_cap
        )
        allocations.update(group_alloc)

        for row in group.itertuples(index=False):
            lev = group_alloc[str(row.signal_id)]
            gross += lev
            for curr, val in gross_currency_legs(row.symbol, lev).items():
                ccy[curr] += val

    output_rows = []
    run_date = str(df["signal_timestamp"].dt.date.min())
    strategy_version = config["strategy_version"]

    for row in df.itertuples(index=False):
        lev = allocations[str(row.signal_id)]
        requested = per_trade_max
        if lev <= EPS:
            status = "rejected"
            reason = "pro_rata_capacity_exhausted"
        elif lev + EPS < requested:
            status = "resized"
            reason = "pro_rata_capacity_shared"
        else:
            status = "accepted"
            reason = ""

        mid = (float(row.observed_bid) + float(row.observed_ask)) / 2.0
        entry_slippage = float(row.executable_entry_price) - mid

        output_rows.append({
            "run_date": run_date,
            "signal_id": str(row.signal_id),
            "strategy_version": strategy_version,
            "symbol": row.symbol,
            "side": row.side,
            "signal_timestamp": row.signal_timestamp.isoformat(),
            "expected_entry_timestamp": row.expected_entry_timestamp.isoformat(),
            "model_entry_price": float(row.model_entry_price),
            "observed_bid": float(row.observed_bid),
            "observed_ask": float(row.observed_ask),
            "executable_entry_price": float(row.executable_entry_price),
            "entry_slippage": entry_slippage,
            "requested_leverage": requested,
            "assigned_leverage": lev,
            "allocation_status": status,
            "rejection_or_resize_reason": reason,
            "simultaneous_group_id": row.expected_entry_timestamp.isoformat(),
            "data_snapshot_hash": digest,
        })

    appended = pd.concat([existing, pd.DataFrame(output_rows)], ignore_index=True)
    appended.to_csv(run / "logs/signals.csv", index=False)

    print(f"Captured signals: {len(output_rows)}")
    print(f"Accepted: {sum(r['allocation_status']=='accepted' for r in output_rows)}")
    print(f"Resized: {sum(r['allocation_status']=='resized' for r in output_rows)}")
    print(f"Rejected: {sum(r['allocation_status']=='rejected' for r in output_rows)}")
    print(f"Snapshot: {snapshot}")
    print(f"Snapshot SHA256: {digest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
