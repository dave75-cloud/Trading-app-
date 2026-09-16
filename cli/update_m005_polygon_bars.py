#!/usr/bin/env python3
"""
KQTRL M005 v1.2a — Polygon prospective five-minute bar updater.

- Fetches only data available at runtime.
- Uses the last fully closed five-minute interval as the upper bound.
- Bootstraps enough recent bars for frozen indicators without reconstructing
  historical signals.
- Appends and deduplicates UTC OHLC bars.
- Rejects future/incomplete bars.
- Saves raw response snapshots and SHA256 hashes.
- Writes a retrieval manifest for every cycle.

Environment:
    POLYGON_API_KEY=<your key>

Polygon aggregate endpoint:
    /v2/aggs/ticker/C:{PAIR}/range/5/minute/{from}/{to}
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
from typing import Any, Dict, List

import pandas as pd


PAIRS = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]
BASE_URL = "https://api.polygon.io"
INTERVAL_MINUTES = 5


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


def last_fully_closed_bar_start(now: pd.Timestamp) -> pd.Timestamp:
    """
    Polygon aggregate timestamp is treated as the bar start.

    At 12:19 UTC, the 12:10 bar is fully closed and the 12:15 bar is still
    forming. Therefore:
        floor(now, 5m) - 5m
    """
    return now.floor(f"{INTERVAL_MINUTES}min") - pd.Timedelta(
        minutes=INTERVAL_MINUTES
    )


def request_json(url: str, timeout: int = 30) -> tuple[Dict[str, Any], bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KQTRL-M005/1.2a",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"Polygon HTTP {exc.code}: {body[:500]}"
        )
    except urllib.error.URLError as exc:
        raise SystemExit(f"Polygon connection failure: {exc}")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Polygon returned invalid JSON: {exc}")

    return payload, raw


def build_url(
    pair: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    api_key: str,
) -> str:
    ticker = f"C:{pair}"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(
        (end + pd.Timedelta(minutes=INTERVAL_MINUTES) - pd.Timedelta(milliseconds=1))
        .timestamp() * 1000
    )

    path = (
        f"/v2/aggs/ticker/{urllib.parse.quote(ticker, safe=':')}"
        f"/range/{INTERVAL_MINUTES}/minute/{start_ms}/{end_ms}"
    )
    query = urllib.parse.urlencode(
        {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": api_key,
        }
    )
    return BASE_URL + path + "?" + query


def parse_results(
    payload: Dict[str, Any],
    pair: str,
    latest_allowed_start: pd.Timestamp,
) -> pd.DataFrame:
    status = str(payload.get("status", "")).upper()
    if status not in {"OK", "DELAYED"}:
        error = payload.get("error") or payload.get("message") or payload
        raise SystemExit(f"{pair}: Polygon status {status!r}: {error}")

    results = payload.get("results") or []
    if not results:
        return pd.DataFrame(columns=["ts", "o", "h", "l", "c"])

    rows = []
    for item in results:
        needed = {"t", "o", "h", "l", "c"}
        if not needed.issubset(item):
            raise SystemExit(
                f"{pair}: aggregate missing fields {sorted(needed - set(item))}"
            )
        ts = pd.to_datetime(int(item["t"]), unit="ms", utc=True)
        rows.append(
            {
                "ts": ts,
                "o": float(item["o"]),
                "h": float(item["h"]),
                "l": float(item["l"]),
                "c": float(item["c"]),
            }
        )

    df = pd.DataFrame(rows).sort_values("ts").drop_duplicates("ts")

    future = df[df["ts"] > latest_allowed_start]
    if not future.empty:
        raise SystemExit(
            f"{pair}: received {len(future)} incomplete/future bars; "
            f"latest allowed start is {latest_allowed_start.isoformat()}"
        )

    malformed = df[
        (df["h"] < df[["o", "c", "l"]].max(axis=1))
        | (df["l"] > df[["o", "c", "h"]].min(axis=1))
        | (df[["o", "h", "l", "c"]] <= 0).any(axis=1)
    ]
    if not malformed.empty:
        raise SystemExit(
            f"{pair}: malformed OHLC bars detected:\n"
            + malformed.head().to_string(index=False)
        )

    return df.reset_index(drop=True)


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
    for col in ["o", "h", "l", "c"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df[["ts", "o", "h", "l", "c"]]


def choose_start(
    existing: pd.DataFrame,
    latest_closed: pd.Timestamp,
    bootstrap_hours: int,
) -> pd.Timestamp:
    if existing.empty:
        return latest_closed - pd.Timedelta(hours=bootstrap_hours)

    latest_existing = existing["ts"].max()
    # Re-fetch one interval of overlap to verify/deduplicate the boundary.
    return latest_existing


def atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(temp, index=False)
    temp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--audit-dir", required=True)
    ap.add_argument(
        "--bootstrap-hours",
        type=int,
        default=72,
        help="Recent warm-up history on the first run; default 72 hours.",
    )
    ap.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.25,
        help="Pause between Polygon requests.",
    )
    args = ap.parse_args()

    api_key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "POLYGON_API_KEY is not set. Example:\n"
            "export POLYGON_API_KEY='your_key_here'"
        )

    output_dir = Path(args.output_dir)
    audit_dir = Path(args.audit_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    retrieved_at = utc_now()
    latest_closed = last_fully_closed_bar_start(retrieved_at)
    cycle_id = retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    cycle_dir = audit_dir / f"polygon_cycle_{cycle_id}"
    cycle_dir.mkdir(parents=True, exist_ok=False)

    manifest_rows: List[dict] = []

    for index, pair in enumerate(PAIRS):
        target = output_dir / f"{pair}_5m.csv"
        existing = load_existing(target)
        start = choose_start(existing, latest_closed, args.bootstrap_hours)

        if start > latest_closed:
            raise SystemExit(
                f"{pair}: existing data timestamp {start.isoformat()} "
                f"is later than latest closed bar {latest_closed.isoformat()}"
            )

        url = build_url(pair, start, latest_closed, api_key)
        safe_url = url.replace(api_key, "***REDACTED***")

        payload, raw = request_json(url)
        raw_path = cycle_dir / f"{pair}_response.json"
        raw_path.write_bytes(raw)
        raw_hash = sha256_bytes(raw)

        incoming = parse_results(payload, pair, latest_closed)

        combined = pd.concat([existing, incoming], ignore_index=True)
        combined = (
            combined.sort_values("ts")
            .drop_duplicates("ts", keep="last")
            .reset_index(drop=True)
        )

        if not combined.empty and combined["ts"].max() > latest_closed:
            raise SystemExit(f"{pair}: combined output includes incomplete bar")

        atomic_write_csv(combined, target)

        manifest_rows.append(
            {
                "cycle_id": cycle_id,
                "pair": pair,
                "retrieved_at_utc": retrieved_at.isoformat(),
                "latest_closed_bar_start": latest_closed.isoformat(),
                "request_start": start.isoformat(),
                "request_url_redacted": safe_url,
                "polygon_status": payload.get("status"),
                "polygon_request_id": payload.get("request_id"),
                "incoming_rows": len(incoming),
                "existing_rows_before": len(existing),
                "rows_after": len(combined),
                "first_bar_after": (
                    combined["ts"].min().isoformat()
                    if not combined.empty else ""
                ),
                "last_bar_after": (
                    combined["ts"].max().isoformat()
                    if not combined.empty else ""
                ),
                "raw_response_file": str(raw_path),
                "raw_response_sha256": raw_hash,
            }
        )

        print(
            f"{pair}: incoming={len(incoming)} "
            f"total={len(combined)} "
            f"last={combined['ts'].max() if not combined.empty else 'NONE'}"
        )

        if index < len(PAIRS) - 1 and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = cycle_dir / "retrieval_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (cycle_dir / "retrieval_manifest.sha256").write_text(
        manifest_hash + "\n"
    )

    print(f"Polygon update completed: {cycle_dir}")
    print(f"Latest fully closed bar start: {latest_closed.isoformat()}")
    print(f"Manifest SHA256: {manifest_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
