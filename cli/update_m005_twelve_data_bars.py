#!/usr/bin/env python3
"""
KQTRL M005 v1.2d — Twelve Data live M5 bar adapter.

- Fetches recent 5-minute forex candles from Twelve Data.
- Keeps only fully closed bars.
- Writes provider-specific CSV files separate from Polygon.
- Appends and deduplicates by UTC timestamp.
- Saves raw responses and a retrieval manifest.
- Does not generate signals, positions, trades, or M005 eligibility counts.

Required environment:
    TWELVE_DATA_API_KEY
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
INTERVAL_MINUTES = 5
BASE_URL = "https://api.twelvedata.com/time_series"


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


def latest_closed_start(now: pd.Timestamp) -> pd.Timestamp:
    return now.floor("5min") - pd.Timedelta(minutes=5)


def request_json(url: str, timeout: int = 30) -> tuple[int, bytes, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "KQTRL-M005-v1.2d"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    except urllib.error.URLError as exc:
        raise SystemExit(f"Twelve Data connection failure: {exc}")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Twelve Data returned invalid JSON: {exc}")

    return status, raw, payload


def build_url(pair: str, api_key: str, outputsize: int) -> str:
    symbol = f"{pair[:3]}/{pair[3:]}"
    query = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "interval": "5min",
            "outputsize": outputsize,
            "timezone": "UTC",
            "order": "ASC",
            "format": "JSON",
            "apikey": api_key,
        }
    )
    return f"{BASE_URL}?{query}"


def parse_payload(
    pair: str,
    payload: dict[str, Any],
    latest_allowed: pd.Timestamp,
) -> pd.DataFrame:
    if str(payload.get("status", "")).lower() == "error":
        raise SystemExit(
            f"{pair}: Twelve Data error: "
            f"{payload.get('message') or payload}"
        )

    values = payload.get("values") or []
    if not values:
        raise SystemExit(f"{pair}: Twelve Data returned no values")

    rows = []
    for item in values:
        ts = pd.Timestamp(item["datetime"], tz="UTC")
        if ts > latest_allowed:
            continue
        rows.append(
            {
                "ts": ts,
                "o": float(item["open"]),
                "h": float(item["high"]),
                "l": float(item["low"]),
                "c": float(item["close"]),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["ts", "o", "h", "l", "c"])

    df = (
        pd.DataFrame(rows)
        .sort_values("ts")
        .drop_duplicates("ts", keep="last")
        .reset_index(drop=True)
    )

    malformed = df[
        (df[["o", "h", "l", "c"]] <= 0).any(axis=1)
        | (df["h"] < df[["o", "c", "l"]].max(axis=1))
        | (df["l"] > df[["o", "c", "h"]].min(axis=1))
    ]
    if not malformed.empty:
        raise SystemExit(f"{pair}: malformed OHLC bars detected")

    return df


def load_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["ts", "o", "h", "l", "c"])
    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=["ts", "o", "h", "l", "c"])
    required = {"ts", "o", "h", "l", "c"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path} missing columns: {sorted(missing)}")
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="raise")
    for col in ("o", "h", "l", "c"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df[["ts", "o", "h", "l", "c"]]


def atomic_write(df: pd.DataFrame, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audit-dir", required=True)
    parser.add_argument("--outputsize", type=int, default=1000)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    args = parser.parse_args()

    api_key = os.environ.get("TWELVE_DATA_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("TWELVE_DATA_API_KEY is not set")

    output_dir = Path(args.output_dir)
    audit_root = Path(args.audit_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_root.mkdir(parents=True, exist_ok=True)

    now = utc_now()
    latest_allowed = latest_closed_start(now)
    cycle_id = now.strftime("%Y%m%dT%H%M%SZ")
    cycle_dir = audit_root / f"twelve_data_cycle_{cycle_id}"
    cycle_dir.mkdir(parents=True, exist_ok=False)

    manifest_rows = []

    for idx, pair in enumerate(PAIRS):
        url = build_url(pair, api_key, args.outputsize)
        status, raw, payload = request_json(url)
        raw_path = cycle_dir / f"{pair}_response.json"
        raw_path.write_bytes(raw)
        raw_hash = hashlib.sha256(raw).hexdigest()

        if status != 200:
            raise SystemExit(
                f"{pair}: Twelve Data HTTP {status}: "
                f"{payload.get('message') or payload}"
            )

        incoming = parse_payload(pair, payload, latest_allowed)
        target = output_dir / f"{pair}_5m.csv"
        existing = load_existing(target)

        combined = (
            pd.concat([existing, incoming], ignore_index=True)
            .sort_values("ts")
            .drop_duplicates("ts", keep="last")
            .reset_index(drop=True)
        )
        atomic_write(combined, target)

        meta = payload.get("meta") or {}
        manifest_rows.append(
            {
                "cycle_id": cycle_id,
                "provider": "twelve_data",
                "pair": pair,
                "retrieved_at_utc": now.isoformat(),
                "latest_allowed_bar_start": latest_allowed.isoformat(),
                "incoming_rows": len(incoming),
                "rows_after": len(combined),
                "first_bar_after": (
                    combined["ts"].min().isoformat() if not combined.empty else ""
                ),
                "last_bar_after": (
                    combined["ts"].max().isoformat() if not combined.empty else ""
                ),
                "exchange_timezone": meta.get("exchange_timezone", ""),
                "interval": meta.get("interval", ""),
                "raw_response_file": str(raw_path),
                "raw_response_sha256": raw_hash,
            }
        )

        latest = combined["ts"].max() if not combined.empty else "NONE"
        print(
            f"{pair}: incoming={len(incoming)} total={len(combined)} "
            f"last={latest}"
        )

        if idx < len(PAIRS) - 1 and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = cycle_dir / "retrieval_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (cycle_dir / "retrieval_manifest.sha256").write_text(
        digest + "\n", encoding="utf-8"
    )

    print(f"Twelve Data update completed: {cycle_dir}")
    print(f"Latest fully closed bar start: {latest_allowed.isoformat()}")
    print(f"Manifest SHA256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
