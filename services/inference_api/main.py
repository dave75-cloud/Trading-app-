from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def signals_latest(h: str = "30m"):
    return {
        "status": "ok",
        "symbol": "GBPUSD",
        "horizon": h,
        "source": "debug_stub",
    }
