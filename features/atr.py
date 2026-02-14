import pandas as pd
def atr(df: pd.DataFrame, period: int = 14):
    high_low = df['h'] - df['l']
    high_close = (df['h'] - df['c'].shift()).abs()
    low_close = (df['l'] - df['c'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=period).mean()
