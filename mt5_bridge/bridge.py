from typing import Tuple, Dict, Any
import os

try:
    import MetaTrader5 as mt5
except Exception:
    mt5 = None

def init() -> bool:
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package not available")
    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    return True

def shutdown():
    if mt5:
        mt5.shutdown()

def _order_type(side: str, entry_type: str):
    s = side.lower(); e = entry_type.lower()
    if e == "market": return mt5.ORDER_TYPE_BUY if s=="buy" else mt5.ORDER_TYPE_SELL
    if e == "limit":  return mt5.ORDER_TYPE_BUY_LIMIT if s=="buy" else mt5.ORDER_TYPE_SELL_LIMIT
    if e == "stop":   return mt5.ORDER_TYPE_BUY_STOP  if s=="buy" else mt5.ORDER_TYPE_SELL_STOP
    raise ValueError(f"Unsupported entry_type: {entry_type}")

def dry_run(symbol: str, side: str, entry_type: str, entry_px: float, sl_px: float, tp_px: float, volume: float) -> Tuple[bool, Dict[str, Any]]:
    if mt5 is None:
        return False, {"error": "MetaTrader5 package not available"}
    info = mt5.symbol_info_tick(symbol)
    if info is None:
        return False, {"error": f"Symbol {symbol} not available"}
    order_type = _order_type(side, entry_type)
    req = {
        "action": mt5.TRADE_ACTION_DEAL if entry_type=="market" else mt5.TRADE_ACTION_PENDING,
        "symbol": symbol, "type": order_type, "price": float(entry_px),
        "sl": float(sl_px), "tp": float(tp_px), "volume": float(volume),
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK,
        "deviation": 20, "magic": 27182818, "comment": "gbpusd-signal-assist"
    }
    bid, ask = info.bid, info.ask
    ok = True; msgs = []
    if entry_type == "limit":
        if side == "buy" and not (entry_px < bid): ok=False; msgs.append("buy-limit < Bid required")
        if side == "sell" and not (entry_px > ask): ok=False; msgs.append("sell-limit > Ask required")
    if entry_type == "stop":
        if side == "buy" and not (entry_px > ask): ok=False; msgs.append("buy-stop > Ask required")
        if side == "sell" and not (entry_px < bid): ok=False; msgs.append("sell-stop < Bid required")
    if sl_px and tp_px and ((side=="buy" and not (sl_px < entry_px < tp_px)) or (side=="sell" and not (tp_px < entry_px < sl_px))):
        ok=False; msgs.append("SL/TP inconsistent with side")
    return ok, {"request": req, "bid": bid, "ask": ask, "messages": msgs}

def place_order(symbol: str, side: str, entry_type: str, entry_px: float, sl_px: float, tp_px: float, volume: float, live: bool=False) -> Dict[str, Any]:
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package not available")
    ok, preview = dry_run(symbol, side, entry_type, entry_px, sl_px, tp_px, volume)
    if not ok:
        return {"accepted": False, "preview": preview}
    # Hard safety latch: requires BOTH live=True and MT5_LIVE_ENABLED=1/true/yes.
    live_enabled = os.getenv("MT5_LIVE_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    if not live or not live_enabled:
        return {"accepted": True, "preview": preview, "live": False}
    result = mt5.order_send(preview["request"])
    return {"accepted": result is not None and result.retcode == mt5.TRADE_RETCODE_DONE,
            "retcode": None if result is None else result.retcode,
            "result": None if result is None else result._asdict(),
            "request": preview["request"]}
