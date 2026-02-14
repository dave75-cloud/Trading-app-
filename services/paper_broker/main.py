from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
app = FastAPI(title="Paper Broker Simulator")
class PlaceOrder(BaseModel):
    side: str; entry_type: str; entry_px: float; sl_px: float; tp_px: float; size: int; tif: str
@app.get("/health")
def health():
    return {"status":"ok", "time": datetime.utcnow().isoformat()}
@app.post("/papertrades/place")
def place(o: PlaceOrder):
    return {"status":"accepted", "outcome": "open", "pnl": 0.0, "received_at": datetime.utcnow().isoformat()}
