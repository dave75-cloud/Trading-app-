from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


CANONICAL_COLUMNS = [
    "ts",
    "symbol",
    "timeframe",
    "o",
    "h",
    "l",
    "c",
    "v",
    "source",
]


@dataclass
class MarketDataLayout:
    root: Path

    def day_path(self, symbol: str, timeframe: str, day: pd.Timestamp) -> Path:
        day = pd.Timestamp(day).tz_convert("UTC") if pd.Timestamp(day).tzinfo else pd.Timestamp(day).tz_localize("UTC")
        return (
            self.root
            / symbol.upper()
            / timeframe
            / f"{day.year:04d}"
            / f"{day.month:02d}"
            / f"{day.day:02d}"
            / "data.csv"
        )


def normalize_market_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    out = df.copy()

    required = {"ts", "symbol", "timeframe", "o", "h", "l", "c", "v", "source"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out["ts"] = pd.to_datetime(out["ts"], utc=True, errors="coerce")
    out = out.dropna(subset=["ts"])

    for col in ["o", "h", "l", "c", "v"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["symbol"] = out["symbol"].astype(str).str.upper()
    out["timeframe"] = out["timeframe"].astype(str)
    out["source"] = out["source"].astype(str)

    out = out.dropna(subset=["o", "h", "l", "c"])
    out = out[CANONICAL_COLUMNS]
    out = out.sort_values("ts").drop_duplicates(subset=["ts", "symbol", "timeframe"], keep="last")
    out = out.reset_index(drop=True)
    return out


def append_day_parquet(
    root: Path | str,
    df: pd.DataFrame,
) -> list[Path]:
    layout = MarketDataLayout(Path(root))
    df = normalize_market_df(df)
    if df.empty:
        return []

    written: list[Path] = []
    df["day"] = df["ts"].dt.floor("D")

    for (symbol, timeframe, day), chunk in df.groupby(["symbol", "timeframe", "day"], sort=True):
        path = layout.day_path(symbol, timeframe, pd.Timestamp(day))
        path.parent.mkdir(parents=True, exist_ok=True)

        chunk = chunk.drop(columns=["day"]).copy()

        if path.exists():
            existing = pd.read_csv(path)
            merged = pd.concat([existing, chunk], ignore_index=True)
            merged = normalize_market_df(merged)
        else:
            merged = normalize_market_df(chunk)

        merged.to_csv(path, index=False)
        written.append(path)

    return written


def load_market_data(
    root: Path | str,
    symbol: str,
    timeframe: str,
    start: Optional[str | pd.Timestamp] = None,
    end: Optional[str | pd.Timestamp] = None,
) -> pd.DataFrame:
    base = Path(root) / symbol.upper() / timeframe
    if not base.exists():
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    files = sorted(base.rglob("*.csv"))
    if not files:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    dfs = [pd.read_parquet(f) for f in files]
    out = normalize_market_df(pd.concat(dfs, ignore_index=True))

    if start is not None:
        start_ts = pd.Timestamp(start, tz="UTC")
        out = out[out["ts"] >= start_ts]
    if end is not None:
        end_ts = pd.Timestamp(end, tz="UTC")
        out = out[out["ts"] <= end_ts]

    return out.reset_index(drop=True)


def expected_bar_delta(timeframe: str) -> pd.Timedelta:
    tf = timeframe.lower().strip()
    if tf.endswith("m"):
        return pd.Timedelta(minutes=int(tf[:-1]))
    if tf.endswith("h"):
        return pd.Timedelta(hours=int(tf[:-1]))
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def gap_report(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = normalize_market_df(df)
    if df.empty:
        return pd.DataFrame(columns=["prev_ts", "next_ts", "gap_minutes"])

    delta = expected_bar_delta(timeframe)
    ts = df["ts"].sort_values().reset_index(drop=True)
    prev = ts.shift(1)
    gaps = ts - prev
    mask = gaps > delta

    out = pd.DataFrame({
        "prev_ts": prev[mask],
        "next_ts": ts[mask],
        "gap_minutes": (gaps[mask] / pd.Timedelta(minutes=1)).astype(float),
    })
    return out.reset_index(drop=True)