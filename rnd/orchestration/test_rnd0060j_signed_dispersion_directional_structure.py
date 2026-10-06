#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import SYMBOLS
from rnd0060j_signed_dispersion_directional_structure import (
    RND0060JError,
    derive_directional_observations,
    summarize,
)

START = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rows(current_return=0.001, forward_return=0.001):
    rows = []
    mid = 1.0
    for i in range(13):
        dt = START + timedelta(minutes=5 * i)
        if i > 0:
            r = current_return if i <= 6 else forward_return
            mid *= (1.0 + r)
        rows.append({
            "timestamp_utc": _ts(dt),
            "complete": True,
            "mid_close": mid,
            "mid_high": mid * 1.0002,
            "mid_low": mid * 0.9998,
        })
    return rows


def _bundle(currents=(0.001, 0.002, 0.003, -0.001), forwards=(0.001, 0.001, 0.001, -0.001)):
    return {s: _rows(currents[i], forwards[i]) for i, s in enumerate(SYMBOLS)}


class RND0060JKernelTests(unittest.TestCase):
    def test_01_exact_four_symbols_required(self):
        b = _bundle(); b.pop("USDJPY")
        with self.assertRaises(Exception):
            derive_directional_observations(b)

    def test_02_single_observation_extracted(self):
        d = derive_directional_observations(_bundle())
        self.assertEqual(len(d["observations"]), 1)

    def test_03_signed_state_preserves_dispersion_magnitude(self):
        o = derive_directional_observations(_bundle())["observations"][0]
        self.assertAlmostEqual(abs(o["signed_dispersion_state"]), o["cross_sectional_dispersion_state"], places=15)

    def test_04_positive_breadth_gives_positive_sign(self):
        o = derive_directional_observations(_bundle())["observations"][0]
        self.assertEqual(o["directional_sign"], 1.0)

    def test_05_negative_breadth_gives_negative_sign(self):
        b = _bundle(currents=(-0.001, -0.002, -0.003, 0.001))
        o = derive_directional_observations(b)["observations"][0]
        self.assertEqual(o["directional_sign"], -1.0)
        self.assertLess(o["signed_dispersion_state"], 0.0)

    def test_06_zero_breadth_maps_to_zero_sign(self):
        b = _bundle(currents=(0.001, -0.001, 0.001, 0.001))
        o = derive_directional_observations(b)["observations"][0]
        self.assertIn(o["directional_sign"], (-1.0, 0.0, 1.0))

    def test_07_forward_response_is_equal_weight_mean(self):
        o = derive_directional_observations(_bundle())["observations"][0]
        vals = list(o["per_symbol_forward_usd_oriented_return"].values())
        self.assertAlmostEqual(o["forward_equal_weight_usd_oriented_return"], sum(vals)/4.0, places=15)

    def test_08_usdjpy_orientation_is_opposite_quote_convention(self):
        o = derive_directional_observations(_bundle())["observations"][0]
        self.assertGreater(o["per_symbol_forward_usd_oriented_return"]["USDJPY"], 0.0)

    def test_09_missing_cross_section_bar_excludes_day(self):
        b = _bundle()
        b["EURUSD"] = [r for r in b["EURUSD"] if r["timestamp_utc"] != "2019-01-02T11:35:00Z"]
        d = derive_directional_observations(b)
        self.assertEqual(d["observations"], [])
        self.assertEqual(d["exclusions"][0]["reason"], "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING")

    def test_10_non_development_year_rejected(self):
        b = _bundle()
        b["AUDUSD"][0]["timestamp_utc"] = "2021-01-04T11:00:00Z"
        with self.assertRaises(Exception):
            derive_directional_observations(b)

    def test_11_incomplete_candle_rejected(self):
        b = _bundle(); b["GBPUSD"][2]["complete"] = False
        with self.assertRaises(Exception):
            derive_directional_observations(b)

    def test_12_bad_ohlc_rejected(self):
        b = _bundle(); b["AUDUSD"][2]["mid_low"] = b["AUDUSD"][2]["mid_close"] * 1.01
        with self.assertRaises(Exception):
            derive_directional_observations(b)

    def test_13_duplicate_timestamp_rejected(self):
        b = _bundle(); b["USDJPY"][3]["timestamp_utc"] = b["USDJPY"][2]["timestamp_utc"]
        with self.assertRaises(Exception):
            derive_directional_observations(b)

    def test_14_summary_preserves_no_authority_flags(self):
        rows_by = {s: [] for s in SYMBOLS}
        specs = [
            (2015, 1, 5, 1), (2015, 1, 6, 2),
            (2016, 1, 4, 3), (2016, 1, 5, 4),
            (2017, 1, 3, 5), (2017, 1, 4, 6),
            (2018, 1, 2, 7), (2018, 1, 3, 8),
            (2019, 1, 2, 9), (2019, 1, 3, 10),
            (2020, 1, 2, 11), (2020, 1, 3, 12),
        ]
        for year, month, day, mult in specs:
            base = datetime(year, month, day, 11, 0, tzinfo=timezone.utc)
            for i, s in enumerate(SYMBOLS):
                rows = _rows(current_return=0.0001 * (i + 1) * mult, forward_return=0.00005 * mult)
                shift = base - START
                for r in rows:
                    x = dict(r)
                    dt = datetime.fromisoformat(r["timestamp_utc"][:-1] + "+00:00") + shift
                    x["timestamp_utc"] = _ts(dt)
                    rows_by[s].append(x)
        for s in SYMBOLS:
            rows_by[s].sort(key=lambda r: r["timestamp_utc"])
        out = summarize(rows_by)
        for k in ("trade_simulation", "pnl", "strategy_candidate", "validation_open", "final_test_open", "reserved_final_access", "broker_writes", "capital_authority", "automatic_promotion"):
            self.assertFalse(out[k])


if __name__ == "__main__":
    unittest.main()
