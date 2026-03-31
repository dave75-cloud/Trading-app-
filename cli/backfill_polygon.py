from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from storage.market_data import append_day_parquet, normalize_market_df

logger = logging.getLogger("backfill_polygon")


def utc_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "gbpusd-signal-backfill/1.0"})
    return s


def daterange(start: datetime, end: datetime):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def fetch_polygon_forex_day(
    session: requests.Session,
    api_key: str,
    symbol: str,
    day: datetime,
    adjusted: str = "true",
    retries: int = 3,
    timeout: int = 30,
) -> pd.DataFrame:
    # NOTE:
    # Polygon forex aggregates syntax may vary by plan/product.
    # Replace endpoint details if your exact endpoint differs.
    pair = symbol.upper()
    from_date = day.strftime("%Y-%m-%d")
    to_date = from_date

    url = f"https://api.polygon.io/v2/aggs/ticker/C:{pair}/range/1/minute/{from_date}/{to_date}"
    params = {
        "adjusted": adjusted,
        "sort": "asc",
        "limit": 50000,
        "apiKey": api_key,
    }

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            payload: dict[str, Any] = r.json()

            results = payload.get("results", [])
            if not results:
                return pd.DataFrame(columns=["ts", "symbol", "timeframe", "o", "h", "l", "c", "v", "source"])

            rows = []
            for x in results:
                rows.append(
                    {
                        "ts": pd.to_datetime(x["t"], unit="ms", utc=True),
                        "symbol": pair,
                        "timeframe": "1m",
                        "o": x.get("o"),
                        "h": x.get("h"),
                        "l": x.get("l"),
                        "c": x.get("c"),
                        "v": x.get("v", 0),
                        "source": "polygon",
                    }
                )

            return normalize_market_df(pd.DataFrame(rows))

        except Exception as e:
            last_err = e

            wait_s = min(2**attempt, 8)
            status_code = None

            if isinstance(e, requests.HTTPError) and e.response is not None:
                status_code = e.response.status_code

                if status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_s = int(retry_after)
                    else:
                        wait_s = 30 * attempt

            logger.warning(
                "Fetch failed for %s attempt %s/%s status=%s: %s",
                from_date,
                attempt,
                retries,
                status_code,
                e,
            )
            logger.warning("Sleeping %s seconds before retry", wait_s)
            time.sleep(wait_s)

    raise RuntimeError(f"Polygon fetch failed for {from_date}: {last_err}") from last_err


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", required=True, help="YYYY-MM-DD")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--out", default="./data/market_candles")
    p.add_argument("--api_key", required=True)
    p.add_argument("--log_level", default="INFO")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.timeframe != "1m":
        raise SystemExit("Initial implementation supports only --timeframe 1m")

    start = utc_date(args.date_from)
    end = utc_date(args.date_to)
    if end < start:
        raise SystemExit("--to must be >= --from")

    out_root = Path(args.out)
    session = build_session()

    total_rows = 0
    written_files = 0

    for day in daterange(start, end):
    logger.info("Fetching %s %s", args.symbol, day.date())
    df = fetch_polygon_forex_day(session, args.api_key, args.symbol, day)
    if df.empty:
        logger.info("No rows for %s", day.date())
        continue

    written = append_day_parquet(out_root, df)
    total_rows += len(df)
    written_files += len(written)
    logger.info("Stored %s rows into %s files for %s", len(df), len(written), day.date())
    time.sleep(2)

    logger.info("Done. total_rows=%s written_files=%s out=%s", total_rows, written_files, out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())