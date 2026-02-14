import os

import types

import mt5_bridge.bridge as b


class _FakeTick:
    def __init__(self, bid=1.0, ask=1.1):
        self.bid = bid
        self.ask = ask


class _FakeMT5:
    # constants used in code
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    TRADE_ACTION_DEAL = 10
    TRADE_ACTION_PENDING = 11
    ORDER_TIME_GTC = 20
    ORDER_FILLING_FOK = 21
    TRADE_RETCODE_DONE = 100

    def __init__(self):
        self.order_send_calls = 0

    def symbol_info_tick(self, _symbol):
        return _FakeTick()

    def order_send(self, _req):
        self.order_send_calls += 1
        return types.SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, _asdict=lambda: {"ok": True})


def test_mt5_live_requires_env_latch(monkeypatch):
    fake = _FakeMT5()
    monkeypatch.setattr(b, "mt5", fake)
    monkeypatch.delenv("MT5_LIVE_ENABLED", raising=False)

    out = b.place_order(
        symbol="GBPUSD",
        side="buy",
        entry_type="market",
        entry_px=1.05,
        sl_px=1.0,
        tp_px=1.1,
        volume=0.01,
        live=True,
    )

    assert out["accepted"] is True
    assert out["live"] is False
    assert fake.order_send_calls == 0

    monkeypatch.setenv("MT5_LIVE_ENABLED", "1")
    out2 = b.place_order(
        symbol="GBPUSD",
        side="buy",
        entry_type="market",
        entry_px=1.05,
        sl_px=1.0,
        tp_px=1.1,
        volume=0.01,
        live=True,
    )
    assert out2["accepted"] is True
    assert out2["retcode"] == fake.TRADE_RETCODE_DONE
    assert fake.order_send_calls == 1
