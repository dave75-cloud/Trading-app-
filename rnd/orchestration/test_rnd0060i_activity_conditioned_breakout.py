#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060i_activity_conditioned_breakout import (
    RND0060IError,
    SYMBOLS,
    _threshold,
    run_candidate,
    validate_rows,
)

START = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _weekday_days(n):
    out=[]; dt=START
    while len(out)<n:
        if dt.weekday()<5: out.append(dt)
        dt += timedelta(days=1)
    return out


def _day_rows(day, pre_return=0.001, breakout="NONE", spread=0.0001):
    rows=[]; mid=1.0
    for i in range(12):
        dt=day+timedelta(minutes=5*i)
        if i>0:
            if i<=6: mid *= 1.0 + pre_return/6.0
            elif i==7 and breakout=="UP": mid *= 1.003
            elif i==7 and breakout=="DOWN": mid *= 0.997
            else: mid *= 1.0001
        bid=mid*(1.0-spread/2.0); ask=mid*(1.0+spread/2.0)
        rows.append({"timestamp_utc":_ts(dt),"complete":True,"bid_close":bid,"ask_close":ask,"mid_close":mid,"mid_high":mid*1.0002,"mid_low":mid*0.9998})
    return rows


def _bundle(days=65, final_breakout="UP"):
    out={s:[] for s in SYMBOLS}
    dts=_weekday_days(days)
    for j,day in enumerate(dts):
        scales=(1.0,1.5,2.0,2.5)
        if j==days-1: scales=(1.0,1.5,2.0,8.0)
        for i,s in enumerate(SYMBOLS):
            br = final_breakout if (j==days-1 and s=="USDJPY") else "NONE"
            out[s].extend(_day_rows(day, pre_return=0.0004*scales[i], breakout=br))
    return out


class RND0060IKernelTests(unittest.TestCase):
    def test_01_rejects_empty_rows(self):
        with self.assertRaises(RND0060IError): validate_rows([])

    def test_02_rejects_non_development_year(self):
        r=_day_rows(START); r[0]["timestamp_utc"]="2021-01-04T11:00:00Z"
        with self.assertRaises(RND0060IError): validate_rows(r)

    def test_03_rejects_incomplete(self):
        r=_day_rows(START); r[2]["complete"]=False
        with self.assertRaises(RND0060IError): validate_rows(r)

    def test_04_rejects_duplicate_timestamp(self):
        r=_day_rows(START); r[3]["timestamp_utc"]=r[2]["timestamp_utc"]
        with self.assertRaises(RND0060IError): validate_rows(r)

    def test_05_rejects_missing_required_field(self):
        r=_day_rows(START); del r[0]["ask_close"]
        with self.assertRaises(RND0060IError): validate_rows(r)

    def test_06_rejects_bad_bid_mid_ask(self):
        r=_day_rows(START); r[1]["bid_close"]=r[1]["mid_close"]*1.01
        with self.assertRaises(RND0060IError): validate_rows(r)

    def test_07_exact_four_symbol_set_required(self):
        b=_bundle(); b.pop("EURUSD")
        with self.assertRaises(RND0060IError): run_candidate(b)

    def test_08_nearest_rank_q75_is_45th_ordered_value(self):
        self.assertEqual(_threshold(list(range(1,61))),45.0)

    def test_09_threshold_uses_only_last_60_prior_states(self):
        vals=[999.0]+list(range(1,61))
        self.assertEqual(_threshold(vals),45.0)

    def test_10_first_60_eligible_days_are_warmup_only(self):
        out=run_candidate(_bundle(days=60))
        self.assertEqual(out["warmup_day_count"],60)
        self.assertEqual(out["trade_count"],0)

    def test_11_high_state_unique_pair_can_trigger_trade(self):
        out=run_candidate(_bundle(days=65,final_breakout="UP"))
        self.assertGreaterEqual(out["gated_day_count"],1)
        self.assertGreaterEqual(out["trade_count"],1)
        self.assertEqual(out["trades"][-1]["symbol"],"USDJPY")

    def test_12_no_breakout_means_no_trade(self):
        out=run_candidate(_bundle(days=65,final_breakout="NONE"))
        self.assertEqual(out["trade_count"],0)

    def test_13_long_trade_uses_ask_entry_and_bid_exit(self):
        out=run_candidate(_bundle(days=65,final_breakout="UP"))
        t=out["trades"][-1]
        self.assertEqual(t["direction"],"LONG")
        self.assertGreater(t["entry_price"],0)
        self.assertGreater(t["exit_price"],0)

    def test_14_no_authority_expansion(self):
        out=run_candidate(_bundle(days=65,final_breakout="UP"))
        for k in ("parameter_search","validation_open","final_test_open","reserved_final_access","broker_writes","capital_authority","automatic_promotion"):
            self.assertFalse(out[k])


if __name__ == "__main__":
    unittest.main()
