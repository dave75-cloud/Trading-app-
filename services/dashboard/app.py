import os
import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


DEFAULT_API = os.getenv("API_BASE_URL", "http://localhost:8080")


def fetch_latest_signal(api_base: str, horizon: str) -> dict:
    r = requests.get(f"{api_base}/signals/latest", params={"h": horizon}, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_backtest(api_base: str, horizon: str, days: int) -> dict:
    r = requests.post(
        f"{api_base}/backtest/run",
        json={"horizon": horizon, "days": days},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def fetch_history(api_base: str, horizon: str, days: int) -> dict:
    r = requests.get(
        f"{api_base}/signals/history",
        params={"h": horizon, "days": int(days), "limit": 5000},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def fetch_evaluate(api_base: str, horizon: str, days: int) -> dict:
    r = requests.get(
        f"{api_base}/signals/evaluate",
        params={"h": horizon, "days": int(days), "limit": 5000},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


st.set_page_config(page_title="GBPUSD Signal Dashboard", layout="wide")

st.title("GBPUSD Signal Dashboard")

with st.sidebar:
    st.header("Controls")
    api_base = st.text_input("API base URL", value=DEFAULT_API)
    horizon = st.selectbox("Horizon", options=["30m", "2h"], index=0)
    days = st.slider("Backtest lookback (days)", min_value=10, max_value=365, value=90, step=5)
    hist_days = st.slider("Signal history window (days)", min_value=1, max_value=180, value=30, step=1)
    do_backtest = st.checkbox("Run backtest", value=True)
    st.caption("Tip: use docker-compose 'up' to run API + dashboard together.")

col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.subheader("Latest signal")
    try:
        payload = fetch_latest_signal(api_base, horizon)
        st.success("Fetched")
    except Exception as e:
        st.error(f"Failed to fetch signal: {e}")
        st.stop()

    now = payload.get("now") or datetime.utcnow().isoformat()
    st.write(f"As of: **{now}**")

    side = payload.get("side", "?")
    prob = payload.get("prob_up", payload.get("p", None))
    sess = payload.get("session")
    suggestion = payload.get("suggestion", {})

    m1, m2, m3 = st.columns(3)
    m1.metric("Side", str(side).upper())
    if prob is not None:
        m2.metric("P(up)", f"{float(prob):.3f}")
    else:
        m2.metric("P(up)", "n/a")
    m3.metric("Session", json.dumps(sess) if sess is not None else "n/a")

    st.markdown("### Suggested order")
    if suggestion:
        st.json(suggestion)
    else:
        st.info("No suggestion returned.")

with col2:
    st.subheader("Backtest summary")
    if do_backtest:
        try:
            bt = fetch_backtest(api_base, horizon, int(days))
            st.success("Ran backtest")
            st.json(bt.get("summary", bt))
        except Exception as e:
            st.error(f"Backtest failed: {e}")
    else:
        st.info("Backtest disabled.")

st.divider()

st.subheader("Signal history")
try:
    hist = fetch_history(api_base, horizon, int(hist_days))
    rows = hist.get("rows", [])
    if rows:
        dfh = pd.DataFrame(rows)
        dfh["asof_ts"] = pd.to_datetime(dfh["asof_ts"], utc=True, errors="coerce")
        dfh = dfh.sort_values("asof_ts")
        c1, c2 = st.columns([0.65, 0.35])
        with c1:
            st.write("P(up) over time")
            if "prob_up" in dfh.columns:
                st.line_chart(dfh.set_index("asof_ts")["prob_up"])
            else:
                st.info("No prob_up in stored rows.")
        with c2:
            st.write("Side counts")
            st.dataframe(dfh["side"].value_counts(dropna=False).rename("count").to_frame())
        st.write("Latest stored rows")
        st.dataframe(dfh.tail(25), use_container_width=True)
    else:
        st.info("No stored signals yet. Refresh 'Latest signal' a few times.")
except Exception as e:
    st.error(f"Failed to load history: {e}")

st.subheader("Live vs realized (directional)")
try:
    ev = fetch_evaluate(api_base, horizon, int(hist_days))
    s = ev.get("summary", {})
    st.json(s)
    ev_rows = ev.get("rows", [])
    if ev_rows:
        dfe = pd.DataFrame(ev_rows)
        dfe["asof_ts"] = pd.to_datetime(dfe["asof_ts"], utc=True, errors="coerce")
        dfe = dfe.sort_values("asof_ts")
        if "hit" in dfe.columns:
            st.line_chart(dfe.set_index("asof_ts")["hit"].rolling(20, min_periods=1).mean())
        st.dataframe(dfe.tail(25), use_container_width=True)
except Exception as e:
    st.error(f"Evaluate failed: {e}")

st.caption(
    "This dashboard is read-only and safe: it does not place live trades. "
    "Execution remains behind the MT5 live latch."
)
