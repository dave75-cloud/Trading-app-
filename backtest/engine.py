import pandas as pd, numpy as np

def atr(df, n=14):
    high_low = df.h - df.l
    high_close = (df.h - df.c.shift()).abs()
    low_close = (df.l - df.c.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()

def rsi(series, n=14):
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))

def session_label(ts):
    t = ts.time()
    if t >= pd.Timestamp("00:00").time() and t <= pd.Timestamp("09:00").time(): return "tokyo"
    if t >= pd.Timestamp("07:00").time() and t <= pd.Timestamp("16:00").time(): return "london"
    if t >= pd.Timestamp("12:00").time() and t <= pd.Timestamp("21:00").time(): return "newyork"
    return "off"

def session_costs(sess):
    if sess == 'london': return 0.00010, 0.00005
    if sess == 'newyork': return 0.00012, 0.00006
    if sess == 'tokyo': return 0.00016, 0.00008
    return 0.00020, 0.00010

def simulate(future, entry, sl, tp, sess, long):
    spread, slip = session_costs(sess)
    if long:
        entry += spread/2 + slip
        for _, bar in future.iterrows():
            hit_tp = bar.h >= tp
            hit_sl = bar.l <= sl
            if hit_tp and hit_sl:
                # Assume intrabar path O->H->L->C (common backtest convention):
                # for longs, TP (high-side) triggers before SL (low-side).
                return (tp - entry) - spread/2 - slip
            if hit_tp:
                return (tp - entry) - spread/2 - slip
            if hit_sl:
                return (sl - entry) - spread/2 - slip
        return (future.c.iloc[-1] - entry) - spread/2 - slip
    else:
        entry -= spread/2 + slip
        for _, bar in future.iterrows():
            hit_tp = bar.l <= tp
            hit_sl = bar.h >= sl
            if hit_tp and hit_sl:
                return (entry - sl) - spread/2 - slip
            if hit_tp:
                return (entry - tp) - spread/2 - slip
            if hit_sl:
                return (entry - sl) - spread/2 - slip
        return (entry - future.c.iloc[-1]) - spread/2 - slip

def monthly_walkforward(df, horizon_bars=6):
    x = df.copy().sort_values('ts')
    x['atr'] = atr(x, 14)
    x['rsi'] = rsi(x['c'], 14)
    x['rng'] = x['h']-x['l']
    x['month'] = x['ts'].dt.to_period('M')
    results=[]; trades=0; pnl=0; wins=0
    for m in sorted(x['month'].dropna().unique())[2:]:
        sub = x[x['month']==m]
        for i in range(sub.index.min(), sub.index.max()-horizon_bars-1):
            row = x.loc[i]
            if pd.isna(row['atr']) or pd.isna(row['rsi']): continue
            sess = session_label(row['ts'])
            price = row['c']; d_sl = max(row['atr']*0.8, 0.0008)
            # toy signal: RSI extreme + range
            if row['rsi'] < 30 and row['rng'] > row['atr']:
                long=True; entry=price-0.5*d_sl; sl=entry-d_sl; tp=entry+1.4*d_sl
            elif row['rsi'] > 70 and row['rng'] > row['atr']:
                long=False; entry=price+0.5*d_sl; sl=entry+d_sl; tp=entry-1.4*d_sl
            else:
                continue
            future = x.iloc[i+1:i+1+horizon_bars]
            res = simulate(future, entry, sl, tp, sess, long)
            trades+=1; pnl+=res; wins+=(res>0)
        if trades:
            results.append({'month': str(m)})
    return {'months': results, 'trades': trades, 'pnl': float(pnl), 'winrate': float(wins/max(trades,1))}
