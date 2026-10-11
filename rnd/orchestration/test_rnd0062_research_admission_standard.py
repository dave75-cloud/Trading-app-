import unittest

from rnd0062_research_admission_standard import (
    ResearchProposal, DevelopmentResult, classify_admission, classify_advancement
)


def proposal(**kw):
    d=dict(
        task_id='RND-TEST', hypothesis_family_id='FAM-1', family_trial_index=1,
        lifetime_related_trial_count=1, mechanism_statement='Economic mechanism',
        independence_statement='Independent from prior failed mechanisms',
        instruments_declared=True,timing_declared=True,signal_declared=True,direction_declared=True,
        lookback_declared=True,exit_declared=True,filters_declared=True,gap_semantics_declared=True,
        cost_model_declared=True,uses_midprice_executable_pnl=False,portfolio_rule_declared=True,
        missing_data_rule_declared=True,primary_metric_declared=True,secondary_diagnostics_declared=True,
        minimum_economic_effect_declared=True,sample_adequacy_rule_declared=True,
        degrees_of_freedom_declared=True,sibling_trials_declared=True,development_partition_only=True,
        prohibited_validation_access=False,prohibited_reserved_final_access=False,
        prospective_outcome_contamination=False,directional_strategy=True,
    )
    d.update(kw); return ResearchProposal(**d)


def result(**kw):
    d=dict(
        primary_criterion_pass=True,minimum_economic_effect_pass=True,integrity_pass=True,
        cost_model_valid=True,reproducible=True,single_year_dependence=False,
        frozen_regime_exception_for_year=False,single_instrument_dependence=False,
        frozen_regime_exception_for_instrument=False,leave_one_year_out_all_positive=True,
        leave_one_instrument_out_all_positive=True,multi_instrument=True,hidden_rescue_or_tuning=False,
        prohibited_partition_access=False,undeclared_specification_change=False,
    )
    d.update(kw); return DevelopmentResult(**d)


class TestRND0062(unittest.TestCase):
    def test_01_missing_mechanism_rejects(self):
        self.assertEqual(classify_admission(proposal(mechanism_statement=''))['classification'],'REJECTED_ADMISSION')

    def test_02_missing_independence_rejects(self):
        self.assertEqual(classify_admission(proposal(independence_statement=''))['classification'],'REJECTED_ADMISSION')

    def test_03_undeclared_parameter_rejects(self):
        self.assertEqual(classify_admission(proposal(lookback_declared=False))['classification'],'REJECTED_ADMISSION')

    def test_04_hidden_sibling_count_rejects(self):
        self.assertIn('HIDDEN_OR_INCONSISTENT_SIBLING_TRIAL_COUNT',classify_admission(proposal(family_trial_index=3,lifetime_related_trial_count=2))['reasons'])

    def test_05_invalid_family_trial_index_rejects(self):
        self.assertIn('INVALID_FAMILY_TRIAL_INDEX',classify_admission(proposal(family_trial_index=0,lifetime_related_trial_count=0))['reasons'])

    def test_06_validation_access_rejects(self):
        self.assertIn('PROHIBITED_VALIDATION_ACCESS',classify_admission(proposal(prohibited_validation_access=True))['reasons'])

    def test_07_reserved_final_access_rejects(self):
        self.assertIn('PROHIBITED_RESERVED_FINAL_ACCESS',classify_admission(proposal(prohibited_reserved_final_access=True))['reasons'])

    def test_08_prospective_contamination_rejects(self):
        self.assertIn('PROSPECTIVE_OUTCOME_CONTAMINATION',classify_admission(proposal(prospective_outcome_contamination=True))['reasons'])

    def test_09_missing_cost_model_rejects_directional(self):
        self.assertIn('MISSING_COST_MODEL',classify_admission(proposal(cost_model_declared=False))['reasons'])

    def test_10_midprice_executable_rejects(self):
        self.assertIn('MIDPRICE_EXECUTABLE_PNL_PROHIBITED',classify_admission(proposal(uses_midprice_executable_pnl=True))['reasons'])

    def test_11_missing_minimum_effect_rejects(self):
        self.assertIn('MISSING_MINIMUM_ECONOMIC_EFFECT',classify_admission(proposal(minimum_economic_effect_declared=False))['reasons'])

    def test_12_missing_sample_adequacy_rejects(self):
        self.assertIn('MISSING_SAMPLE_ADEQUACY_RULE',classify_admission(proposal(sample_adequacy_rule_declared=False))['reasons'])

    def test_13_clean_proposal_admissible(self):
        self.assertEqual(classify_admission(proposal())['classification'],'ADMISSIBLE_FOR_DEVELOPMENT_TEST')

    def test_14_failed_primary_cannot_advance(self):
        self.assertIn('PRIMARY_CRITERION_FAILED',classify_advancement(proposal(),result(primary_criterion_pass=False))['reasons'])

    def test_15_failed_minimum_effect_cannot_advance(self):
        self.assertIn('MINIMUM_ECONOMIC_EFFECT_FAILED',classify_advancement(proposal(),result(minimum_economic_effect_pass=False))['reasons'])

    def test_16_single_year_dependence_cannot_advance(self):
        self.assertIn('SINGLE_YEAR_DEPENDENCE',classify_advancement(proposal(),result(single_year_dependence=True))['reasons'])

    def test_17_single_instrument_dependence_cannot_advance(self):
        self.assertIn('SINGLE_INSTRUMENT_DEPENDENCE',classify_advancement(proposal(),result(single_instrument_dependence=True))['reasons'])

    def test_18_leave_one_year_out_failure_blocks(self):
        self.assertIn('LEAVE_ONE_YEAR_OUT_FAILED',classify_advancement(proposal(),result(leave_one_year_out_all_positive=False))['reasons'])

    def test_19_leave_one_instrument_out_failure_blocks(self):
        self.assertIn('LEAVE_ONE_INSTRUMENT_OUT_FAILED',classify_advancement(proposal(),result(leave_one_instrument_out_all_positive=False))['reasons'])

    def test_20_rescue_tuning_blocks(self):
        self.assertIn('RESCUE_OR_TUNING_DETECTED',classify_advancement(proposal(),result(hidden_rescue_or_tuning=True))['reasons'])

    def test_21_clean_robust_result_candidate_review_eligible(self):
        self.assertEqual(classify_advancement(proposal(),result())['classification'],'ELIGIBLE_FOR_CANDIDATE_REVIEW')

    def test_22_eligibility_not_candidate_freeze(self):
        out=classify_advancement(proposal(),result()); self.assertFalse(out['candidate_freeze']); self.assertTrue(out['candidate_review_human_only'])

    def test_23_authority_fields_false(self):
        for out in (classify_admission(proposal()),classify_advancement(proposal(),result())):
            for k in ('promotion_authority','broker_write_authority','capital_authority','live_execution_authority','automatic_merge'):
                self.assertIs(out[k],False)

    def test_24_deterministic_replay(self):
        a=classify_advancement(proposal(),result()); b=classify_advancement(proposal(),result()); self.assertEqual(a,b)


if __name__=='__main__': unittest.main()
