import numpy as np, pandas as pd
def score_dummy(df: pd.DataFrame, horizon: str = "30m"):
    if len(df)<20: return {"p_up":0.5,"exp_move":0.0,"regime":{"mr":0.5,"bo":0.5}}
    ret1 = df['c'].pct_change().tail(5).sum()
    vol = df['c'].pct_change().tail(20).std() + 1e-9
    p = 0.5 + np.tanh(ret1/vol)*0.2
    exp = np.sign(ret1)*float(df['c'].iloc[-1])*(vol*(2 if horizon=='2h' else 1))
    mr = float(max(0.0, 1-abs(ret1)/vol)); bo=1.0-mr
    return {"p_up": float(np.clip(p,0.05,0.95)), "exp_move": float(exp), "regime": {"mr":mr,"bo":bo}}
