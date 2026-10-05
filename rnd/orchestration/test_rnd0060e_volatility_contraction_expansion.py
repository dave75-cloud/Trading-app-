import unittest
from datetime import datetime, timedelta, timezone

from rnd0060e_volatility_contraction_expansion import RND0060EError, evaluate_symbol


def z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def row(dt, mid, high=None, low=None, spread=0.0002):
    high = mid if high is None else high
    low = mid if low is None else low
    return {"timestamp_utc": z(dt), "complete": True, "bid_close": mid-spread/2, "ask_close": mid+spread/2, "mid_close": mid, "mid_high": high, "mid_low": low}

def fixture(day=datetime(2019,1,2,tzinfo=timezone.utc), breakout="up", gap_entry=False, gap_hold=False, exact_ratio=False, no_contraction=False, equality_first=False):
    rows=[]
    start=datetime(day.year,day.month,day.day,9,35,tzinfo=timezone.utc)
    # baseline 18 bars: 09:35..11:00, range roughly .0060
    for n in range(18):
        dt=start+timedelta(minutes=5*n)
        mid=1.1000
        high=1.1030 if n==8 else 1.1005
        low=1.0970 if n==9 else 1.0995
        rows.append(row(dt,mid,high,low))
    # short 6 bars: 11:05..11:30. exact ratio .0020 when requested, otherwise .0018.
    short_half=0.0010 if exact_ratio else (0.0030 if no_contraction else 0.0009)
    for n in range(6):
        dt=start+timedelta(minutes=5*(18+n))
        rows.append(row(dt,1.1000,1.1000+short_half,1.1000-short_half))
    high=1.1000+short_half; low=1.1000-short_half
    # post-observation bars 11:35 onward
    mids=[]
    if breakout=="up":
        mids=[high if equality_first else 1.1000, high+0.0004, high+0.0005, high+0.0007, high+0.0009, high+0.0010]
    elif breakout=="down":
        mids=[1.1000, low-0.0004, low-0.0005, low-0.0007, low-0.0009, low-0.0010]
    else:
        mids=[1.1000]*6
    for n,mid in enumerate(mids):
        dt=datetime(day.year,day.month,day.day,11,35,tzinfo=timezone.utc)+timedelta(minutes=5*n)
        if gap_entry and n==2:
            continue
        if gap_hold and n==4:
            continue
        rows.append(row(dt,mid,mid+0.0001,mid-0.0001))
    if gap_hold:
        rows.append(row(datetime(day.year,day.month,day.day,12,5,tzinfo=timezone.utc), high+0.0012, high+0.0013, high+0.0011))
    return rows

class TestRND0060E(unittest.TestCase):
    def test_up_breakout_long(self):
        out=evaluate_symbol("EURUSD",fixture())
        self.assertEqual(out["trades"][0]["side"],"long")
    def test_down_breakout_short(self):
        out=evaluate_symbol("EURUSD",fixture(breakout="down"))
        self.assertEqual(out["trades"][0]["side"],"short")
    def test_exact_one_third_ratio_is_accepted(self):
        out=evaluate_symbol("EURUSD",fixture(exact_ratio=True))
        self.assertEqual(out["contraction_event_count"],1)
    def test_no_contraction_means_no_trade(self):
        out=evaluate_symbol("EURUSD",fixture(no_contraction=True))
        self.assertEqual(out["trade_count"],0)
    def test_boundary_equality_is_not_breakout(self):
        out=evaluate_symbol("EURUSD",fixture(equality_first=True))
        sig=[e for e in out["events"] if e["event_type"]=="BREAKOUT_SIGNAL"][0]
        self.assertEqual(sig["timestamp"],"2019-01-02T11:40:00Z")
    def test_no_breakout_means_no_trade(self):
        out=evaluate_symbol("EURUSD",fixture(breakout="none"))
        self.assertEqual(out["trade_count"],0)
    def test_entry_bar_not_holding_bar_one(self):
        out=evaluate_symbol("EURUSD",fixture())
        t=out["trades"][0]
        self.assertEqual(t["holding_bars"],3)
        self.assertEqual(t["entry_timestamp"],"2019-01-02T11:45:00Z")
        self.assertEqual(t["exit_timestamp"],"2019-01-02T12:00:00Z")
    def test_missing_entry_bar_cancels(self):
        rows=fixture()
        rows=[r for r in rows if r["timestamp_utc"]!="2019-01-02T11:45:00Z"]
        out=evaluate_symbol("EURUSD",rows)
        self.assertEqual(out["trade_count"],0)
        self.assertTrue(any(e["event_type"]=="PENDING_SIGNAL_CANCELLED" for e in out["events"]))
    def test_gap_during_open_position_survives(self):
        out=evaluate_symbol("EURUSD",fixture(gap_hold=True))
        t=out["trades"][0]
        self.assertEqual(t["gap_exposure_count"],1)
        self.assertEqual(t["holding_bars"],3)
    def test_cost_drag_positive(self):
        out=evaluate_symbol("GBPUSD",fixture())
        t=out["trades"][0]
        self.assertGreater(t["execution_cost_drag"],0)
        self.assertGreater(t["gross_return"],t["net_return"])
    def test_incomplete_state_window_skips(self):
        rows=fixture(); rows.pop(3)
        out=evaluate_symbol("EURUSD",rows)
        self.assertEqual(out["contraction_event_count"],0)
    def test_development_year_firewall(self):
        rows=fixture(); rows[0]=dict(rows[0],timestamp_utc="2021-01-02T09:35:00Z")
        with self.assertRaises(RND0060EError): evaluate_symbol("EURUSD",rows)
    def test_authority_closed(self):
        out=evaluate_symbol("EURUSD",fixture())
        self.assertTrue(out["development_only"]); self.assertFalse(out["reserved_final_access"]); self.assertFalse(out["broker_writes"]); self.assertFalse(out["capital_authority"])
    def test_one_trade_max_per_symbol_day(self):
        out=evaluate_symbol("EURUSD",fixture())
        self.assertLessEqual(out["trade_count"],1)

if __name__=="__main__": unittest.main()
