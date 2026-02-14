import argparse, pathlib, json, numpy as np, pandas as pd, joblib
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

def rsi(series, n=14):
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))

def build_features(df):
    x = df.copy().sort_values('ts')
    x['ret1'] = x['c'].pct_change()
    x['ret5'] = x['c'].pct_change(5)
    x['vol20'] = x['c'].pct_change().rolling(20).std()
    x['rng'] = x['h']-x['l']
    x['atr14'] = x['rng'].rolling(14).mean()
    x['rsi14'] = rsi(x['c'],14)
    x['tokyo'] = x['ts'].dt.hour.between(0,9).astype(int)
    x['london'] = x['ts'].dt.hour.between(7,16).astype(int)
    x['newyork'] = x['ts'].dt.hour.between(12,21).astype(int)
    x = x.dropna().reset_index(drop=True)
    return x

def target(df, horizon_bars):
    fut = df['c'].shift(-horizon_bars)
    return (fut > df['c']).astype(int)

def load_parquet_dir(data_dir: pathlib.Path, symbol: str) -> pd.DataFrame:
    base = data_dir / symbol
    parts = list(base.rglob("*.parquet"))
    if not parts:
        raise FileNotFoundError(f"No Parquet under {base}")
    dfs = [pd.read_parquet(p) for p in sorted(parts)]
    return pd.concat(dfs, ignore_index=True).sort_values("ts")

def train_one(df, horizon_bars):
    x = build_features(df)
    y = target(x, horizon_bars)
    x = x.iloc[:-horizon_bars]; y = y.iloc[:-horizon_bars]
    feats = [c for c in x.columns if c not in ('ts','o','h','l','c','v')]
    X = x[feats].values; yv = y.values
    best_auc=-1; best=None; best_pipe=None
    for name, clf in [
        ("xgb", XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, subsample=0.8)),
        ("lgbm", LGBMClassifier(n_estimators=400, learning_rate=0.05, subsample=0.8)),
    ]:
        pipe = Pipeline([("scaler", StandardScaler(with_mean=False)), ("clf", clf)])
        tscv = TimeSeriesSplit(n_splits=5)
        aucs=[]
        for tr, te in tscv.split(X):
            pipe.fit(X[tr], yv[tr]); p=pipe.predict_proba(X[te])[:,1]; aucs.append(roc_auc_score(yv[te], p))
        auc=float(np.mean(aucs))
        if auc>best_auc: best_auc=auc; best=name; best_pipe=pipe
    best_pipe.fit(X, yv)
    p = best_pipe.predict_proba(X)[:,1]
    brier=float(brier_score_loss(yv, p))
    meta={"model":best,"auc":best_auc,"brier":brier,"features":feats}
    return best_pipe, meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--out_dir", default="./models_registry/gbpusd")
    args = ap.parse_args()
    df = load_parquet_dir(pathlib.Path(args.data_dir), args.symbol)
    for h, bars in [("30m",6),("2h",24)]:
        model, meta = train_one(df, bars)
        out = pathlib.Path(args.out_dir) / h / pd.Timestamp.utcnow().date().isoformat()
        out.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, out/"model.pkl")
        (out/"feature_spec.json").write_text(json.dumps({"horizon":h, **meta}, indent=2))
        (out/"metadata.json").write_text(json.dumps({"horizon":h, **meta}, indent=2))
        print("Saved", out)

if __name__ == "__main__":
    main()
