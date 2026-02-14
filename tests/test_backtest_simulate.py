import pandas as pd

from backtest.engine import simulate, session_costs


def _future(highs, lows, closes):
    return pd.DataFrame({"h": highs, "l": lows, "c": closes})


def test_long_tp_hit_includes_costs():
    # TP hit on first bar
    fut = _future(highs=[1.50], lows=[1.20], closes=[1.30])
    entry, sl, tp = 1.30, 1.25, 1.40
    spread, slip = session_costs("london")
    pnl = simulate(fut, entry=entry, sl=sl, tp=tp, sess="london", long=True)
    # Engine: entry adjusted by spread/2 + slip; then TP-exit minus spread/2 - slip
    expected_entry = entry + spread / 2 + slip
    expected = (tp - expected_entry) - spread / 2 - slip
    assert abs(pnl - expected) < 1e-12


def test_short_sl_hit_includes_costs():
    # SL hit on first bar
    fut = _future(highs=[1.55], lows=[1.20], closes=[1.30])
    entry, sl, tp = 1.40, 1.50, 1.30
    spread, slip = session_costs("newyork")
    pnl = simulate(fut, entry=entry, sl=sl, tp=tp, sess="newyork", long=False)
    expected_entry = entry - spread / 2 - slip
    expected = (expected_entry - sl) - spread / 2 - slip
    assert abs(pnl - expected) < 1e-12


def test_long_both_tp_and_sl_hit_tp_wins_by_convention():
    # For longs, both touched in-bar -> TP wins (O->H->L->C assumption).
    fut = _future(highs=[1.60], lows=[1.00], closes=[1.30])
    entry, sl, tp = 1.30, 1.20, 1.40
    pnl = simulate(fut, entry=entry, sl=sl, tp=tp, sess="tokyo", long=True)
    assert pnl > 0


def test_short_both_tp_and_sl_hit_sl_wins_by_convention():
    # For shorts, both touched in-bar -> SL wins (O->H->L->C => high-side first).
    fut = _future(highs=[1.60], lows=[1.00], closes=[1.30])
    entry, sl, tp = 1.30, 1.40, 1.20
    pnl = simulate(fut, entry=entry, sl=sl, tp=tp, sess="tokyo", long=False)
    assert pnl < 0


def test_mark_to_market_if_no_bracket_hit():
    fut = _future(highs=[1.31, 1.32], lows=[1.29, 1.28], closes=[1.30, 1.29])
    entry, sl, tp = 1.30, 1.20, 1.40
    pnl = simulate(fut, entry=entry, sl=sl, tp=tp, sess="off", long=True)
    assert isinstance(pnl, float)
