import unittest

from rnd0068_timing_consensus_source_feasibility import (
    RND0068Error, SourceEvidence, timing_classification, consensus_classification,
    provider_registry, preferred_timing_source, consensus_pilot_candidates,
    selection_firewall, assert_no_outcome_fields, architecture_status,
)


class TestRND0068(unittest.TestCase):
    def test_01_bls_primary_timing_admissible(self):
        e = provider_registry()['BLS_HISTORICAL_SCHEDULE']
        self.assertEqual(timing_classification(e), 'TIMING_ADMISSIBLE_PRIMARY_SOURCE')

    def test_02_timing_role_required(self):
        with self.assertRaises(RND0068Error): timing_classification(provider_registry()['TRADING_ECONOMICS'])

    def test_03_timing_requires_exact_time(self):
        e = SourceEvidence('X','TIMING',True,False,True,2015,2020,False,False,False,True,True,True,False)
        self.assertEqual(timing_classification(e), 'TIMING_REJECT_NOT_EXACT')

    def test_04_timing_requires_timezone_context(self):
        e = SourceEvidence('X','TIMING',True,True,False,2015,2020,False,False,False,True,True,True,False)
        self.assertEqual(timing_classification(e), 'TIMING_REJECT_TIMEZONE_CONTEXT_MISSING')

    def test_05_timing_requires_identity(self):
        e = SourceEvidence('X','TIMING',True,True,True,2015,2020,False,False,False,False,True,True,False)
        self.assertEqual(timing_classification(e), 'TIMING_REJECT_IDENTITY_INSUFFICIENT')

    def test_06_secondary_exact_timing_not_primary(self):
        e = SourceEvidence('X','TIMING',False,True,True,2015,2020,False,False,False,True,True,True,True)
        self.assertEqual(timing_classification(e), 'TIMING_ADMISSIBLE_SECONDARY_SOURCE_REQUIRES_PROVENANCE_REVIEW')

    def test_07_te_consensus_pilot_admissible(self):
        e = provider_registry()['TRADING_ECONOMICS']
        self.assertEqual(consensus_classification(e), 'CONSENSUS_PILOT_ADMISSIBLE')

    def test_08_consensus_role_required(self):
        with self.assertRaises(RND0068Error): consensus_classification(provider_registry()['BLS_HISTORICAL_SCHEDULE'])

    def test_09_eodhd_coverage_rejected(self):
        e = provider_registry()['EODHD']
        self.assertEqual(consensus_classification(e), 'CONSENSUS_REJECT_PRIMARY_COVERAGE_INSUFFICIENT')

    def test_10_fmp_point_in_time_unresolved(self):
        e = provider_registry()['FMP']
        self.assertEqual(consensus_classification(e), 'CONSENSUS_UNRESOLVED_POINT_IN_TIME')

    def test_11_finnhub_coverage_unresolved(self):
        e = provider_registry()['FINNHUB']
        self.assertEqual(consensus_classification(e), 'CONSENSUS_UNRESOLVED_COVERAGE')

    def test_12_market_survey_required(self):
        e = SourceEvidence('X','CONSENSUS',False,True,True,2015,2020,False,True,True,True,True,True,False)
        self.assertEqual(consensus_classification(e), 'CONSENSUS_REJECT_NOT_MARKET_SURVEY')

    def test_13_point_in_time_required(self):
        e = SourceEvidence('X','CONSENSUS',False,True,True,2015,2020,True,False,True,True,True,True,False)
        self.assertEqual(consensus_classification(e), 'CONSENSUS_UNRESOLVED_POINT_IN_TIME')

    def test_14_consensus_identity_required(self):
        e = SourceEvidence('X','CONSENSUS',False,True,True,2015,2020,True,True,True,False,True,True,False)
        self.assertEqual(consensus_classification(e), 'CONSENSUS_REJECT_IDENTITY_INSUFFICIENT')

    def test_15_reference_period_required(self):
        e = SourceEvidence('X','CONSENSUS',False,True,True,2015,2020,True,True,True,True,False,True,False)
        self.assertEqual(consensus_classification(e), 'CONSENSUS_REJECT_IDENTITY_INSUFFICIENT')

    def test_16_pre_release_proof_required(self):
        e = SourceEvidence('X','CONSENSUS',False,True,True,2015,2020,True,True,True,True,True,False,False)
        self.assertEqual(consensus_classification(e), 'CONSENSUS_REJECT_PRE_RELEASE_PROOF_MISSING')

    def test_17_preferred_timing_is_bls(self):
        self.assertEqual(preferred_timing_source(), 'BLS_HISTORICAL_SCHEDULE')

    def test_18_te_only_consensus_pilot_candidate(self):
        self.assertEqual(consensus_pilot_candidates(), ('TRADING_ECONOMICS',))

    def test_19_fx_outcome_selection_rejected(self):
        with self.assertRaises(RND0068Error): selection_firewall('TRADING_ECONOMICS', based_on_fx_outcomes=True)

    def test_20_purchase_authority_rejected(self):
        with self.assertRaises(RND0068Error): selection_firewall('TRADING_ECONOMICS', based_on_fx_outcomes=False, purchase_authorized=True)

    def test_21_selection_basis_non_economic(self):
        out = selection_firewall('TRADING_ECONOMICS', based_on_fx_outcomes=False)
        self.assertEqual(out['selection_basis'], 'PROVENANCE_COVERAGE_POINT_IN_TIME_COST_ONLY')

    def test_22_market_outcome_fields_rejected(self):
        with self.assertRaises(RND0068Error): assert_no_outcome_fields(['provider','pnl'])

    def test_23_clean_fields_allowed(self):
        assert_no_outcome_fields(['provider','calendar_id','reference_period','consensus'])

    def test_24_authority_firewall(self):
        s = architecture_status()
        self.assertEqual(s['preferred_us_timing_source'], 'BLS_HISTORICAL_SCHEDULE')
        self.assertEqual(s['consensus_pilot_candidates'], ('TRADING_ECONOMICS',))
        for k in (
            'strategy_outcome_open','validation_open','reserved_final_open','prospective_outcomes_open',
            'promotion_authority','provider_purchase_authority','broker_write_authority',
            'capital_authority','live_execution_authority','automatic_merge'):
            self.assertIs(s[k], False)


if __name__ == '__main__':
    unittest.main()
