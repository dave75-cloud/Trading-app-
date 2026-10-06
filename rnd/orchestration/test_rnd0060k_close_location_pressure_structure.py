#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import SYMBOLS
from rnd0060k_close_location_pressure_structure import extract_pressure_observations, summarize

START = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rows(drift=0.0005, forward=0.0003, flat_range=False):
    rows=[]; mid=1.0
    for i in range(13):
        dt=START+timedelta(minutes=5*i)
        if i>0:
            mid *= 1.0 + (drift if i<=6 else forward)
        if flat_range:
            high=low=mid
        else:
            high=mid*1.0004; low=mid*0.9996
        rows.append({"timestamp_utc":_ts(dt),"complete":True,"mid_close":mid,"mid_high":high,"mid_low":low})
    return rows


def _bundle(drifts=(0.0005,0.0007,-0.0004,0.0006), forwards=(0.0003,0.0002,-0.0002,0.0004)):
    return {s:_rows(drifts[i],forwards[i]) for i,s in enumerate(SYMBOLS)}


class RND0060KKernelTests(unittest.TestCase):
    def test_01_exact_four_symbols_required(self):
        b=_bundle(); b.pop("USDJPY")
        with self.assertRaises(Exception): extract_pressure_observations(b)

    def test_02_four_symbol_rows_per_day(self):
        d=extract_pressure_observations(_bundle())
        self.assertEqual(len(d["observations"]),4)

    def test_03_pressure_is_bounded_for_fixture(self):
        d=extract_pressure_observations(_bundle())
        for r in d["observations"]: self.assertTrue(-1.0 <= r["usd_oriented_close_location_pressure"] <= 1.0)

    def test_04_audusd_positive_quote_drift_is_usd_negative_pressure(self):
        r=[x for x in extract_pressure_observations(_bundle())["observations"] if x["symbol"]=="AUDUSD"][0]
        self.assertLess(r["usd_oriented_close_location_pressure"],0.0)

    def test_05_usdjpy_positive_quote_drift_is_usd_positive_pressure(self):
        r=[x for x in extract_pressure_observations(_bundle())["observations"] if x["symbol"]=="USDJPY"][0]
        self.assertGreater(r["usd_oriented_close_location_pressure"],0.0)

    def test_06_forward_usd_orientation_audusd(self):
        r=[x for x in extract_pressure_observations(_bundle())["observations"] if x["symbol"]=="AUDUSD"][0]
        self.assertLess(r["forward_usd_oriented_return"],0.0)

    def test_07_forward_usd_orientation_usdjpy(self):
        r=[x for x in extract_pressure_observations(_bundle())["observations"] if x["symbol"]=="USDJPY"][0]
        self.assertGreater(r["forward_usd_oriented_return"],0.0)

    def test_08_dispersion_context_same_for_all_four_symbol_rows(self):
        d=extract_pressure_observations(_bundle())
        self.assertEqual(len({r["cross_sectional_dispersion_context"] for r in d["observations"]}),1)

    def test_09_missing_cross_section_bar_excludes_day(self):
        b=_bundle(); b["EURUSD"]=[r for r in b["EURUSD"] if r["timestamp_utc"]!="2019-01-02T11:35:00Z"]
        d=extract_pressure_observations(b)
        self.assertEqual(d["observations"],[])
        self.assertEqual(d["exclusions"][0]["reason"],"REQUIRED_CROSS_SECTION_OBSERVATION_MISSING")

    def test_10_degenerate_range_excludes_day(self):
        b=_bundle(); b["GBPUSD"]=_rows(drift=0.0, forward=0.0, flat_range=True)
        d=extract_pressure_observations(b)
        self.assertEqual(d["observations"],[])
        self.assertEqual(d["exclusions"][0]["reason"],"DEGENERATE_CURRENT_30M_RANGE")

    def test_11_incomplete_candle_rejected(self):
        b=_bundle(); b["GBPUSD"][2]["complete"]=False
        with self.assertRaises(Exception): extract_pressure_observations(b)

    def test_12_duplicate_timestamp_rejected(self):
        b=_bundle(); b["USDJPY"][3]["timestamp_utc"]=b["USDJPY"][2]["timestamp_utc"]
        with self.assertRaises(Exception): extract_pressure_observations(b)

    def test_13_non_development_year_rejected(self):
        b=_bundle(); b["AUDUSD"][0]["timestamp_utc"]="2021-01-04T11:00:00Z"
        with self.assertRaises(Exception): extract_pressure_observations(b)

    def test_14_summary_preserves_no_authority_flags(self):
        rows_by={s:[] for s in SYMBOLS}
        specs=[
            (2015,1,5,1),(2015,1,6,2),
            (2016,1,4,1),(2016,1,5,2),
            (2017,1,2,1),(2017,1,3,2),
            (2018,1,2,1),(2018,1,3,2),
            (2019,1,2,1),(2019,1,3,2),
            (2020,1,2,1),(2020,1,3,2),
        ]
        for year,month,day,mult in specs:
            base=datetime(year,month,day,11,0,tzinfo=timezone.utc)
            for i,s in enumerate(SYMBOLS):
                rows=_rows(drift=(i+1)*0.0001*mult,forward=(i+1)*0.00005*mult)
                shift=base-START
                for r in rows:
                    x=dict(r); dt=datetime.fromisoformat(r["timestamp_utc"][:-1]+"+00:00")+shift; x["timestamp_utc"]=_ts(dt); rows_by[s].append(x)
        for s in SYMBOLS: rows_by[s].sort(key=lambda r:r["timestamp_utc"])
        out=summarize(rows_by)
        for k in ("trade_simulation","pnl","strategy_candidate","validation_open","final_test_open","reserved_final_access","broker_writes","capital_authority","automatic_promotion"):
            self.assertFalse(out[k])
        self.assertTrue(out["activity_context_descriptive_only"])
        self.assertIsNone(out["activity_threshold"])


if __name__=="__main__": unittest.main()
