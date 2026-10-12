import unittest

from rnd0071_consensus_provider_access_decision import (
    RND0071Error,
    ProviderEvidence,
    classify_provider,
    provider_catalogue,
    decision_summary,
    assert_offline_first,
)


class TestRND0071(unittest.TestCase):
    def test_01_catalogue_has_four_candidates(self):
        self.assertEqual(set(provider_catalogue()), {'FMP','FINNHUB','EODHD','TRADING_ECONOMICS'})

    def test_02_fmp_not_admissible(self):
        self.assertEqual(classify_provider(provider_catalogue()['FMP']), 'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')

    def test_03_finnhub_rejected_for_history_boundary(self):
        self.assertEqual(classify_provider(provider_catalogue()['FINNHUB']), 'REJECT_INSUFFICIENT_HISTORY_FOR_DEVELOPMENT_2015_2020')

    def test_04_eodhd_rejected_for_history_boundary(self):
        self.assertEqual(classify_provider(provider_catalogue()['EODHD']), 'REJECT_INSUFFICIENT_HISTORY_FOR_DEVELOPMENT_2015_2020')

    def test_05_te_preferred(self):
        self.assertEqual(classify_provider(provider_catalogue()['TRADING_ECONOMICS']), 'PREFERRED_BOUNDED_PROVENANCE_PILOT_CANDIDATE')

    def test_06_missing_provider_name_rejected(self):
        with self.assertRaises(RND0071Error):
            classify_provider(ProviderEvidence('',True,True,True,True,True,True))

    def test_07_missing_point_in_time_rejected(self):
        p=ProviderEvidence('X',False,True,True,True,True,True)
        self.assertEqual(classify_provider(p),'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')

    def test_08_missing_consensus_semantic_rejected(self):
        p=ProviderEvidence('X',True,False,True,True,True,True)
        self.assertEqual(classify_provider(p),'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')

    def test_09_missing_capture_proof_rejected(self):
        p=ProviderEvidence('X',True,True,True,True,False,True)
        self.assertEqual(classify_provider(p),'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')

    def test_10_model_forecast_not_separate_rejected(self):
        p=ProviderEvidence('X',True,True,False,True,True,True)
        self.assertEqual(classify_provider(p),'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')

    def test_11_insufficient_history_beats_other_merits(self):
        p=ProviderEvidence('X',True,True,True,False,True,True)
        self.assertEqual(classify_provider(p),'REJECT_INSUFFICIENT_HISTORY_FOR_DEVELOPMENT_2015_2020')

    def test_12_purchase_required_now_rejected(self):
        p=ProviderEvidence('X',True,True,True,True,True,True,True)
        with self.assertRaises(RND0071Error): classify_provider(p)

    def test_13_admissible_noncheap_is_not_cost_preferred(self):
        p=ProviderEvidence('X',True,True,True,True,True,False)
        self.assertEqual(classify_provider(p),'ADMISSIBLE_BUT_NOT_COST_PREFERRED')

    def test_14_summary_prefers_te(self):
        self.assertEqual(decision_summary()['preferred_provider'],'TRADING_ECONOMICS')

    def test_15_summary_freezes_trial_path(self):
        self.assertEqual(decision_summary()['preferred_access_path'],'STANDARD_USD49_ONE_WEEK_TRIAL_AFTER_OFFLINE_ADAPTER_VERIFICATION')

    def test_16_summary_request_budget_is_ten(self):
        self.assertEqual(decision_summary()['pilot_request_budget_max'],10)

    def test_17_summary_scope_is_frozen(self):
        self.assertEqual(decision_summary()['pilot_scope'],'US_CPI_2019Q1_STRUCTURE_ONLY')

    def test_18_no_purchase_before_adapter(self):
        self.assertFalse(decision_summary()['purchase_before_adapter_verification'])

    def test_19_purchase_attempt_before_adapter_rejected(self):
        with self.assertRaises(RND0071Error):
            assert_offline_first(adapter_verified=False,purchase_requested=True)

    def test_20_verified_adapter_still_requires_human(self):
        self.assertEqual(assert_offline_first(adapter_verified=True,purchase_requested=True),'HUMAN_DECISION_REQUIRED_FOR_TRIAL_ACTIVATION')

    def test_21_no_purchase_request_authorizes_nothing(self):
        self.assertEqual(assert_offline_first(adapter_verified=False,purchase_requested=False),'NO_PROVIDER_SPEND_AUTHORIZED')

    def test_22_all_authorities_false(self):
        s=decision_summary()
        for k in ('provider_purchase_authority','trial_activation_authority','strategy_outcome_open','validation_open','reserved_final_open','prospective_outcomes_open','broker_write_authority','capital_authority','live_execution_authority','automatic_merge'):
            self.assertIs(s[k],False)

    def test_23_te_model_and_consensus_are_distinct_requirements(self):
        te=provider_catalogue()['TRADING_ECONOMICS']
        self.assertTrue(te.consensus_semantic_documented)
        self.assertTrue(te.model_forecast_separate)

    def test_24_fmp_low_cost_does_not_override_provenance(self):
        fmp=provider_catalogue()['FMP']
        self.assertTrue(fmp.trial_or_low_cost)
        self.assertEqual(classify_provider(fmp),'NOT_ADMISSIBLE_WITH_CURRENT_PUBLIC_PROOF')


if __name__ == '__main__':
    unittest.main()
