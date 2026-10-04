#!/usr/bin/env python3
import math
import unittest
from datetime import datetime, timedelta

import gap_aware_m005_reconstruction as frozen
import rnd0043_signal_friction_kernel as r


def rows(start="2015-01-05T10:30:00Z", n=90, spread=0.00010, gap_at=None):
    dt=datetime.fromisoformat(start[:-1]+"+00:00")
    out=[]
    mid=1.0000
    for i in range(n):
        if gap_at is not None and i==gap_at:
            dt += timedelta(minutes=10)
        mid *= 1.0 + (0.00085 if i%2==0 else -0.00055)
        bid=mid-spread/2
        ask=mid+spread/2
        out.append({"timestamp_utc":dt.strftime("%Y-%m-%dT%H:%M:%SZ"),"complete":True,"bid_close":bid,"ask_close":ask,"mid_close":mid})
        dt += timedelta(minutes=5)
    return out


class TestRND0043SignalFrictionKernel(unittest.TestCase):
    def test_exact_predeclared_arms(self):
        self.assertEqual(r.AUTHORIZED_ARMS,{"F000":None,"F001":3.0,"F002":5.0,"F003":8.0})
        with self.assertRaises(r.RND0043KernelError):
            r.reconstruct_pair("AUDUSD",rows(),"F004")

    def test_ratio_uses_last_12_returns_and_current_spread(self):
        returns=[0.001,-0.001]*6 + [99.0]
        used=returns[-12:]
        bid, ask, mid = 0.9999, 1.0001, 1.0
        got=r.signal_to_friction_ratio(returns,bid,ask,mid)
        expected_spread=(ask-bid)/mid
        expected=frozen.population_std(used)/expected_spread
        self.assertTrue(math.isclose(got["relative_spread"],expected_spread,rel_tol=0,abs_tol=1e-18))
        self.assertTrue(math.isclose(got["signal_to_friction"],expected,rel_tol=0,abs_tol=1e-12))

    def test_zero_spread_fails_closed(self):
        with self.assertRaises(r.RND0043KernelError):
            r.signal_to_friction_ratio([0.001,-0.001]*6,1.0,1.0,1.0)

    def test_f000_matches_frozen_r000_on_2015_fixture(self):
        fixture=rows()
        old=frozen.reconstruct_pair("AUDUSD",fixture)
        new=r.reconstruct_pair("AUDUSD",fixture,"F000")
        self.assertEqual(new["completed_trade_count"],old["completed_trade_count"])
        self.assertTrue(math.isclose(new["completed_trade_net_equity_index"],old["completed_trade_net_equity_index"],rel_tol=0,abs_tol=1e-15))
        self.assertTrue(math.isclose(new["completed_trade_gross_equity_index"],old["completed_trade_gross_equity_index"],rel_tol=0,abs_tol=1e-15))
        self.assertEqual(new["gap_count"],old["gap_count"])

    def test_actual_entry_ratio_provenance(self):
        out=r.reconstruct_pair("AUDUSD",rows(n=120),"F000")
        for trade in out["trades"]:
            self.assertIsNotNone(trade["entry_signal_to_friction"])
        self.assertGreaterEqual(len(out["actual_entry_signal_to_friction_ratios"]),len(out["trades"]))

    def test_gate_is_entry_only_not_exit_override(self):
        fixture=rows(spread=0.00010)
        f000=r.reconstruct_pair("AUDUSD",fixture,"F000")
        f003=r.reconstruct_pair("AUDUSD",fixture,"F003")
        self.assertLessEqual(f003["completed_trade_count"],f000["completed_trade_count"])
        self.assertGreaterEqual(f003["rejected_entry_signal_count"],0)
        self.assertFalse(f003["authority"]["development_outcomes"])

    def test_gap_resets_contiguous_state(self):
        fixture=rows(n=120,gap_at=65)
        out=r.reconstruct_pair("AUDUSD",fixture,"F001")
        self.assertEqual(out["gap_count"],1)
        self.assertGreaterEqual(out["contiguous_episode_count"],2)

    def test_post_development_year_is_rejected(self):
        fixture=rows(start="2021-01-04T11:00:00Z",n=2)
        with self.assertRaises(r.RND0043KernelError):
            r.reconstruct_pair("AUDUSD",fixture,"F001")


if __name__=="__main__": unittest.main()
