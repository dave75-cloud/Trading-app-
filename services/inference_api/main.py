from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest(h: str = "30m"):
<<<<<<< HEAD
=======
<<<<<<< HEAD
    try:
        now = datetime.utcnow()
        sess = session_flags(now)

        h = h if h in ("30m", "2h") else "30m"
        model_pkl, meta_json = _latest_artifacts(h)
        df = _load_recent_parquet()
        asof_ts = df.sort_values("ts")["ts"].iloc[-1]
        timeframe = f"{BAR_MINUTES}m"

        if not model_pkl:
            s = score_dummy(df.tail(200), horizon=h)
            payload = {
                "now": now.isoformat(),
                "asof_ts": asof_ts.isoformat(),
                "symbol": SYMBOL,
                "timeframe": timeframe,
                "horizon": h,
                **s,
                "session": sess,
                "source": "toy",
            }
            try:
                _store().upsert_signal(payload)
            except Exception:
                logger.exception("upsert_signal failed")
            return payload

        return {"status": "ok", "note": "model path not yet exercised"}

    except Exception as e:
        logger.exception("signals_latest failed")
        return {
            "status": "error",
            "message": str(e),
            "horizon": h,
        }
=======
>>>>>>> Restore real signals latest route
    return {
        "status": "ok",
        "note": "THIS IS NEW CODE",
        "horizon": h
    }
<<<<<<< HEAD
=======
>>>>>>> Restore real signals latest route
>>>>>>> Restore real signals latest route
