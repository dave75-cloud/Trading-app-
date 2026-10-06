#!/usr/bin/env python3
import unittest
from rnd0060h_cross_sectional_dispersion_state import SYMBOLS
from rnd0060k_close_location_pressure_structure import classify_observations, RND0060KError


def _obs(reverse_years=(), symbol_signs=None):
    rows=[]; n=0
    symbol_signs=symbol_signs or {s:1 for s in SYMBOLS}
    for year in range(2015,2021):
        vals=[-0.8,-0.2,0.2,0.8]
        responses=[-0.004,-0.001,0.001,0.004]
        if year in reverse_years: responses=list(reversed(responses))
        for s in SYMBOLS:
            sign=symbol_signs[s]
            for j,x in enumerate(vals):
                y=responses[j] if sign>0 else -responses[j]
                rows.append({
                    'timestamp_utc':f'{year}-01-{2+j:02d}T11:30:00Z','year':year,'symbol':s,
                    'usd_oriented_close_location_pressure':x,
                    'forward_usd_oriented_return':y,
                    'cross_sectional_dispersion_context':0.001+n*1e-8,
                    'all_symbol_pressures':{q:x for q in SYMBOLS},
                    'all_symbol_forward_usd_returns':{q:y for q in SYMBOLS},
                })
        n+=1
    return rows


class RND0060KClassifierTests(unittest.TestCase):
    def test_01_pass_fixture_detects_structure(self):
        self.assertEqual(classify_observations(_obs())['classification'],'DIRECTIONAL_PRESSURE_STRUCTURE_DETECTED')
    def test_02_requires_observations(self):
        with self.assertRaises(RND0060KError): classify_observations([])
    def test_03_aggregate_gate_present(self):
        self.assertTrue(classify_observations(_obs())['criteria']['aggregate_primary_spearman_gte_0_05'])
    def test_04_annual_gate_can_fail(self):
        d=classify_observations(_obs(reverse_years={2015,2016,2017}))
        self.assertFalse(d['criteria']['at_least_4_of_6_annual_primary_spearman_positive'])
    def test_05_symbol_gate_can_fail(self):
        signs={'AUDUSD':1,'EURUSD':-1,'GBPUSD':-1,'USDJPY':-1}
        d=classify_observations(_obs(symbol_signs=signs))
        self.assertFalse(d['criteria']['at_least_3_of_4_symbol_primary_spearman_positive'])
    def test_06_quartile_gate_present(self):
        self.assertTrue(classify_observations(_obs())['criteria']['top_quartile_mean_primary_response_gt_bottom_quartile'])
    def test_07_integrity_gate_true(self):
        self.assertTrue(classify_observations(_obs())['criteria']['integrity_reconciliation_pass'])
    def test_08_activity_context_is_descriptive_only(self):
        d=classify_observations(_obs()); self.assertTrue(d['activity_context_descriptive_only']); self.assertIsNone(d['activity_threshold'])
    def test_09_no_trade_or_validation_authority(self):
        d=classify_observations(_obs())
        for k in ('trade_simulation','pnl','strategy_candidate','validation_open','final_test_open','reserved_final_access'):
            self.assertFalse(d[k])
    def test_10_no_broker_capital_or_promotion_authority(self):
        d=classify_observations(_obs())
        for k in ('broker_writes','capital_authority','automatic_promotion'):
            self.assertFalse(d[k])


if __name__=='__main__': unittest.main()
