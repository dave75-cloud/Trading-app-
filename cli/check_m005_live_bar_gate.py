#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
REQUIRED = {"ts", "o", "h", "l", "c"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bars-dir", required=True)
    parser.add_argument("--max-staleness-minutes", type=float, default=20.0)
    parser.add_argument("--future-tolerance-minutes", type=float, default=1.0)
    parser.add_argument("--watermark-out", required=True)
    args = parser.parse_args()

    bars_dir = Path(args.bars_dir)
    watermark_out = Path(args.watermark_out)
    now = pd.Timestamp.now(tz="UTC")
    latest_by_pair = {}

    for pair in PAIRS:
        path = bars_dir / f"{pair}_5m.csv"
        if not path.exists():
            fail(f"{pair}: missing {path}")

        df = pd.read_csv(path)
        if df.empty:
            fail(f"{pair}: file is empty")

        missing = REQUIRED - set(df.columns)
        if missing:
            fail(f"{pair}: missing columns {sorted(missing)}")

        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
        if df["ts"].isna().any():
            fail(f"{pair}: invalid timestamp values")

        for col in ("o", "h", "l", "c"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if df[["o", "h", "l", "c"]].isna().any().any():
            fail(f"{pair}: invalid OHLC values")

        duplicates = int(df["ts"].duplicated().sum())
        if duplicates:
            fail(f"{pair}: {duplicates} duplicate timestamp(s)")

        malformed = df[
            (df[["o", "h", "l", "c"]] <= 0).any(axis=1)
            | (df["h"] < df[["o", "c", "l"]].max(axis=1))
            | (df["l"] > df[["o", "c", "h"]].min(axis=1))
        ]
        if not malformed.empty:
            fail(f"{pair}: {len(malformed)} malformed OHLC bar(s)")

        latest = df["ts"].max()
        age_minutes = (now - latest).total_seconds() / 60.0

        if age_minutes < -args.future_tolerance_minutes:
            fail(
                f"{pair}: latest bar is in the future: "
                f"{latest.isoformat()} (age {age_minutes:.1f} min)"
            )

        if age_minutes > args.max_staleness_minutes:
            fail(
                f"{pair}: stale latest bar {latest.isoformat()} "
                f"(age {age_minutes:.1f} min; limit "
                f"{args.max_staleness_minutes:.1f} min)"
            )

        latest_by_pair[pair] = latest.isoformat()
        print(
            f"PASS {pair}: rows={len(df)} "
            f"latest={latest.isoformat()} age_min={age_minutes:.1f}"
        )

    payload = {
        "checked_at_utc": now.isoformat(),
        "latest_by_pair": latest_by_pair,
    }

    watermark_out.parent.mkdir(parents=True, exist_ok=True)
    tmp = watermark_out.with_suffix(watermark_out.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(watermark_out)

    print("All live-bar checks passed")
    print(f"Watermark: {watermark_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
