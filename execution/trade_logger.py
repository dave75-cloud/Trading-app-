import pandas as pd
from pathlib import Path


def log_trade(ts, symbol, side, price, filepath="data/live_trade_log.csv"):
    row = pd.DataFrame(
        [{
            "ts": ts,
            "symbol": symbol,
            "side": side,
            "price": price,
        }]
    )

    path = Path(filepath)

    if path.exists():
        row.to_csv(path, mode="a", header=False, index=False)
    else:
        row.to_csv(path, index=False)