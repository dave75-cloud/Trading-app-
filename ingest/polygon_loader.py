from __future__ import annotations
import pathlib
import pandas as pd, requests

# Base URL. We append /C:{symbol}/range/1/minute/{start}/{end}
POLY_BASE = "https://api.polygon.io/v2/aggs/ticker"

def _write_parquet_partition(df: pd.DataFrame, symbol: str, out_dir: pathlib.Path):
    df = df.copy()
    df['symbol'] = symbol
    df['timeframe'] = '1m'
    df['source'] = 'polygon_api'
    df['dt'] = df['ts'].dt.date
    for dt, part in df.groupby('dt'):
        day_dir = out_dir / symbol / "timeframe=1m" / f"dt={dt}"
        day_dir.mkdir(parents=True, exist_ok=True)
        part[['ts','symbol','timeframe','o','h','l','c','v','source']].to_parquet(day_dir / f"{dt}.parquet", index=False)

def download_range(api_key: str, date_from: str, date_to: str, out_dir: str, symbol: str = "GBPUSD"):
    out_path = pathlib.Path(out_dir); out_path.mkdir(parents=True, exist_ok=True)
    start = int(pd.Timestamp(date_from, tz='UTC').timestamp() * 1000)
    end   = int(pd.Timestamp(date_to, tz='UTC').timestamp() * 1000)
    url = f"{POLY_BASE}/C:{symbol}/range/1/minute/{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
    r = requests.get(url, timeout=60); r.raise_for_status()
    data = r.json()
    rows = data.get('results', [])
    if not rows: return 0
    df = pd.DataFrame(rows).rename(columns={'t':'timestamp','o':'o','h':'h','l':'l','c':'c','v':'v'})
    df['ts'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df[['ts','o','h','l','c','v']]
    _write_parquet_partition(df, symbol, out_path)
    return len(df)
