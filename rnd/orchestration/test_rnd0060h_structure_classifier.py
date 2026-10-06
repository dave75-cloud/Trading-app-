#!/usr/bin/env python3
import unittest
from rnd0060h_cross_sectional_dispersion_state import SYMBOLS, RND0060HError
from rnd0060h_structure_classifier import classify_observations


def _obs(reverse_years=(), symbol_signs=None):
    rows=[]; n=0
    symbol_signs=symbol_signs or {s:1 for s in SYMBOLS}
    for year in range(2015,2021):
        vals=[n+1,n+2]
        prim=list(vals)
        if year in reverse_years: prim=prim[::-1]
        for j,state in enumerate(vals):
            p=float(prim[j])
            ranges={s:(p if symbol_signs[s]>0 else 20-p) + (i+1)*0.001 for i,s in enumerate(SYMBOLS)}
            rows.append({
                'timestamp_utc':f'{year}-01-{2+j:02d}T11:30:00Z','year':year,
                'cross_sectional_dispersion_state':float(state),
                'primary_mean_forward_relative_realized_range':p,
                'secondary_forward_cross_sectional_return_dispersion':float(state)+0.5,
                'per_symbol_forward_relative_realized_range':ranges,
            })
        n+=2
    return rows


class RND0060HClassifierTests(unittest.TestCase):
    def test_01_pass_fixture_detects_structure(self):
        d=classify_observations(_obs()); self.assertEqual(d['classification'],'CROSS_SECTIONAL_STRUCTURE_DETECTED')
    def test_02_requires_observations(self):
        with self.assertRaises(RND0060HError): classify_observations([])
    def test_03_annual_gate_can_fail(self):
        d=classify_observations(_obs(reverse_years={2015,2016,2017})); self.assertFalse(d['criteria']['at_least_4_of_6_annual_primary_spearman_positive'])
    def test_04_symbol_gate_can_fail(self):
        signs={'AUDUSD':1,'EURUSD':-1,'GBPUSD':-1,'USDJPY':-1}
        d=classify_observations(_obs(symbol_signs=signs)); self.assertFalse(d['criteria']['at_least_3_of_4_symbol_forward_range_spearman_positive'])
    def test_05_aggregate_gate_is_present(self):
        d=classify_observations(_obs()); self.assertTrue(d['criteria']['aggregate_primary_spearman_gte_0_05'])
    def test_06_quartile_gate_is_present(self):
        d=classify_observations(_obs()); self.assertTrue(d['criteria']['top_quartile_mean_primary_response_gt_bottom_quartile'])
    def test_07_integrity_gate_is_true(self):
        d=classify_observations(_obs()); self.assertTrue(d['criteria']['integrity_reconciliation_pass'])
    def test_08_no_trade_or_pnl_authority(self):
        d=classify_observations(_obs()); self.assertFalse(d['trade_simulation']); self.assertFalse(d['pnl']); self.assertFalse(d['strategy_candidate'])
    def test_09_no_validation_or_final_authority(self):
        d=classify_observations(_obs()); self.assertFalse(d['validation_open']); self.assertFalse(d['final_test_open']); self.assertFalse(d['reserved_final_access'])
    def test_10_no_broker_capital_or_promotion_authority(self):
        d=classify_observations(_obs()); self.assertFalse(d['broker_writes']); self.assertFalse(d['capital_authority']); self.assertFalse(d['automatic_promotion'])

if __name__=='__main__': unittest.main()
