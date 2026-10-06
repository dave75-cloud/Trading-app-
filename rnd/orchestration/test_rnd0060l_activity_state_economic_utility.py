#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import SYMBOLS
from rnd0060l_activity_state_economic_utility import extract_utility_observations, summarize

START = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rows(drift=0.0005, forward=0.0003, spread=0.0002):
    rows=[]; mid=1.0
    for i in range(13):
        dt=START+timedelta(minutes=5*i)
        if i>0:
            mid *= 1.0 + (drift if i<=6 else forward)
        half = spread * mid / 2.0
        rows.append({
            "timestamp_utc":_ts(dt),
            "complete":True,
            "bid_close":mid-half,
            "ask_close":mid+half,
            "mid_close":mid,
            "mid_high":mid*1.0004,
            "mid_low":mid*0.9996,
        })
    return rows


def _bundle(drifts=(0.0005,0.0007,-0.0004,0.0006), forwards=(0.0003,0.0002,-0.0002,0.0004), spreads=(0.0002,0.00025,0.0003,0.0002)):
    return {s:_rows(drifts[i],forwards[i],spreads[i]) for i,s in enumerate(SYMBOLS)}


class RND0060LKernelTests(unittest.TestCase):
    def test_01_exact_four_symbols_required(self):
        b=_bundle(); b.pop("USDJPY")
        with self.assertRaises(Exception): extract_utility_observations(b)

    def test_02_single_market_observation_extracted(self):
        d=extract_utility_observations(_bundle())
        self.assertEqual(len(d["observations"]),1)

    def test_03_all_symbol_ratios_present(self):
        o=extract_utility_observations(_bundle())["observations"][0]
        self.assertEqual(set(o["per_symbol_movement_to_friction_ratio"]),set(SYMBOLS))

    def test_04_relative_spread_positive(self):
        o=extract_utility_observations(_bundle())["observations"][0]
        self.assertTrue(all(v>0.0 for v in o["per_symbol_contemporaneous_relative_spread"].values()))

    def test_05_forward_movement_nonnegative(self):
        o=extract_utility_observations(_bundle())["observations"][0]
        self.assertTrue(all(v>=0.0 for v in o["per_symbol_forward_relative_realized_movement"].values()))

    def test_06_market_response_is_equal_weight_mean(self):
        o=extract_utility_observations(_bundle())["observations"][0]
        vals=list(o["per_symbol_movement_to_friction_ratio"].values())
        self.assertAlmostEqual(o["market_wide_movement_to_friction_ratio"],sum(vals)/4.0,places=15)

    def test_07_zero_spread_excludes_day(self):
        b=_bundle()
        r=b["GBPUSD"][6]
        r["bid_close"]=r["mid_close"]; r["ask_close"]=r["mid_close"]
        d=extract_utility_observations(b)
        self.assertEqual(d["observations"],[])
        self.assertEqual(d["exclusions"][0]["reason"],"NON_POSITIVE_CONTEMPORANEOUS_RELATIVE_SPREAD")

    def test_08_bad_bid_ask_order_rejected(self):
        b=_bundle(); r=b["EURUSD"][2]; r["bid_close"]=r["mid_close"]*1.01
        with self.assertRaises(Exception): extract_utility_observations(b)

    def test_09_missing_cross_section_bar_excludes_day(self):
        b=_bundle(); b["EURUSD"]=[r for r in b["EURUSD"] if r["timestamp_utc"]!="2019-01-02T11:35:00Z"]
        d=extract_utility_observations(b)
        self.assertEqual(d["observations"],[])
        self.assertEqual(d["exclusions"][0]["reason"],"REQUIRED_CROSS_SECTION_OBSERVATION_MISSING")

    def test_10_incomplete_candle_rejected(self):
        b=_bundle(); b["GBPUSD"][2]["complete"]=False
        with self.assertRaises(Exception): extract_utility_observations(b)

    def test_11_duplicate_timestamp_rejected(self):
        b=_bundle(); b["USDJPY"][3]["timestamp_utc"]=b["USDJPY"][2]["timestamp_utc"]
        with self.assertRaises(Exception): extract_utility_observations(b)

    def test_12_non_development_year_rejected(self):
        b=_bundle(); b["AUDUSD"][0]["timestamp_utc"]="2021-01-04T11:00:00Z"
        with self.assertRaises(Exception): extract_utility_observations(b)

    def test_13_ratio_moves_inverse_to_spread_fixture(self):
        a=extract_utility_observations(_bundle(spreads=(0.0002,0.0002,0.0002,0.0002)))["observations"][0]
        b=extract_utility_observations(_bundle(spreads=(0.0004,0.0004,0.0004,0.0004)))["observations"][0]
        self.assertGreater(a["market_wide_movement_to_friction_ratio"],b["market_wide_movement_to_friction_ratio"])

    def test_14_summary_preserves_no_authority_flags(self):
        rows_by={s:[] for s in SYMBOLS}
        weekdays={2015:(5,6),2016:(4,5),2017:(3,4),2018:(2,3),2019:(2,3),2020:(2,3)}
        for year,(d1,d2) in weekdays.items():
            for mult,day in enumerate((d1,d2),start=1):
                base=datetime(year,1,day,11,0,tzinfo=timezone.utc)
                for i,s in enumerate(SYMBOLS):
                    rows=_rows(drift=(i+1)*0.0001*mult,forward=(i+1)*0.00005*mult,spread=0.0002+0.00001*i)
                    shift=base-START
                    for r in rows:
                        x=dict(r); dt=datetime.fromisoformat(r["timestamp_utc"][:-1]+"+00:00")+shift; x["timestamp_utc"]=_ts(dt); rows_by[s].append(x)
        for s in SYMBOLS: rows_by[s].sort(key=lambda r:r["timestamp_utc"])
        out=summarize(rows_by)
        for k in ("trade_simulation","pnl","strategy_candidate","validation_open","final_test_open","reserved_final_access","prospective_candidate_outcomes_open","broker_writes","capital_authority","automatic_promotion"):
            self.assertFalse(out[k])
        self.assertEqual(out["declared_trial_count"],1)
        self.assertFalse(out["parameter_search"])
        self.assertFalse(out["threshold_search"])


if __name__=="__main__": unittest.main()
