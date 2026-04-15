import pandas as pd


def generate_signal(
    df: pd.DataFrame,
    fast: int = 20,
    slow: int = 50,
    vol_window: int = 12,
    vol_threshold: float = 0.0005,
    start_hour: int = 11,
    end_hour: int = 12,
):
    x = df.copy()

    x["ts"] = pd.to_datetime(x["ts"], utc=True)
    x["hour"] = x["ts"].dt.hour
    x["fast_ma"] = x["c"].rolling(fast).mean()
    x["slow_ma"] = x["c"].rolling(slow).mean()
    x["ret"] = x["c"].pct_change().fillna(0)
    x["rolling_vol"] = x["ret"].rolling(vol_window).std()

    latest = x.iloc[-1]

    if not (start_hour <= latest["hour"] < end_hour):
        return 0

    if latest["rolling_vol"] <= vol_threshold:
        return 0

    if latest["fast_ma"] > latest["slow_ma"]:
        return 1

    if latest["fast_ma"] < latest["slow_ma"]:
        return -1

    return 0