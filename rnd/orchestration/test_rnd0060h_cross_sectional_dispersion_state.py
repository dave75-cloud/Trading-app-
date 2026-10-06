#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta

from rnd0060h_cross_sectional_dispersion_state import (
    RND0060HError, SYMBOLS, extract_market_observations, spearman, validate_rows,
)

START = datetime(2019, 1, 2, 11, 0, tzinfo=timezone.utc)


def _ts(dt): return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def _rows(scale=1.0, fwd=0.001):
    rows=[]; mid=1.0
    for i in range(13):
        dt=START+timedelta(minutes=5*i)
        if i>0:
            r=(0.0003*scale if i<=6 else fwd)
            mid*=1+r
        rows.append({'timestamp_utc':_ts(dt),'complete':True,'mid_close':mid,'mid_high':mid*1.0002,'mid_low':mid*0.9998})
    return rows


def _bundle(scales=(1,2,3,4), fwd=0.001):
    return {s:_rows(scales[i],fwd) for i,s in enumerate(SYMBOLS)}


class RND0060HKernelTests(unittest.TestCase):
    def test_01_exact_four_symbols_required(self):
        b=_bundle(); b.pop('USDJPY')
        with self.assertRaises(RND0060HError): extract_market_observations(b)
    def test_02_rejects_empty_rows(self):
        with self.assertRaises(RND0060HError): validate_rows([])
    def test_03_rejects_non_development_year(self):
        r=_rows(); r[0]['timestamp_utc']='2021-01-04T11:00:00Z'
        with self.assertRaises(RND0060HError): validate_rows(r)
    def test_04_rejects_incomplete(self):
        r=_rows(); r[2]['complete']=False
        with self.assertRaises(RND0060HError): validate_rows(r)
    def test_05_rejects_duplicate_time(self):
        r=_rows(); r[3]['timestamp_utc']=r[2]['timestamp_utc']
        with self.assertRaises(RND0060HError): validate_rows(r)
    def test_06_rejects_missing_field(self):
        r=_rows(); del r[1]['mid_high']
        with self.assertRaises(RND0060HError): validate_rows(r)
    def test_07_rejects_bad_ohlc(self):
        r=_rows(); r[1]['mid_low']=r[1]['mid_close']*1.01
        with self.assertRaises(RND0060HError): validate_rows(r)
    def test_08_extracts_single_market_observation(self):
        out=extract_market_observations(_bundle())
        self.assertEqual(len(out['observations']),1)
        self.assertGreater(out['observations'][0]['cross_sectional_dispersion_state'],0)
    def test_09_missing_one_symbol_bar_excludes_day(self):
        b=_bundle(); b['EURUSD']=[r for r in b['EURUSD'] if r['timestamp_utc']!='2019-01-02T11:35:00Z']
        out=extract_market_observations(b)
        self.assertEqual(out['observations'],[])
        self.assertEqual(out['exclusions'][0]['reason'],'REQUIRED_CROSS_SECTION_OBSERVATION_MISSING')
    def test_10_forward_ranges_nonnegative(self):
        o=extract_market_observations(_bundle())['observations'][0]
        self.assertTrue(all(v>=0 for v in o['per_symbol_forward_relative_realized_range'].values()))
    def test_11_secondary_dispersion_nonnegative(self):
        o=extract_market_observations(_bundle())['observations'][0]
        self.assertGreaterEqual(o['secondary_forward_cross_sectional_return_dispersion'],0)
    def test_12_spearman_ties(self):
        v=spearman([1,1,2,3],[1,2,3,4]); self.assertGreater(v,0.9)
    def test_13_spearman_constant_rejected(self):
        with self.assertRaises(RND0060HError): spearman([1,1,1],[1,2,3])
    def test_14_kernel_emits_measurement_fields_only(self):
        o=extract_market_observations(_bundle())['observations'][0]
        joined=' '.join(o.keys()).lower()
        self.assertNotIn('trade',joined)
        self.assertNotIn('pnl',joined)
        self.assertNotIn('broker',joined)
        self.assertNotIn('capital',joined)

if __name__=='__main__': unittest.main()
