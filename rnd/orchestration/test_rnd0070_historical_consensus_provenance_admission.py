import unittest

from rnd0070_historical_consensus_provenance_admission import (
    RND0070Error,
    ConsensusCandidate,
    admission_receipt,
    architecture_status,
    classify_source,
    trading_economics_semantic,
    validate_candidate,
    validate_no_market_outcomes,
)


def candidate(**kw):
    d = dict(
        provider='TRADING_ECONOMICS',
        field_name='Forecast',
        semantic='MARKET_CONSENSUS',
        historical_point_in_time=True,
        provider_event_id='TE-CPI-2019-02',
        link_key='US_CPI_HEADLINE',
        economy='United States',
        currency='USD',
        reference_period='2019-01',
        consensus=252.5,
        source_identity='TE point-in-time calendar snapshot',
        raw_hash='abc123',
        coverage_start_year=2015,
        coverage_end_year=2020,
        captured_at_utc='2019-02-13T13:00:00Z',
        point_in_time_mechanism='calendar point-in-time endpoint',
    )
    d.update(kw)
    return ConsensusCandidate(**d)


class TestRND0070(unittest.TestCase):
    def test_01_forecast_semantic_market_consensus(self):
        self.assertEqual(trading_economics_semantic('Forecast'), 'MARKET_CONSENSUS')

    def test_02_teforecast_semantic_model(self):
        self.assertEqual(trading_economics_semantic('TEForecast'), 'MODEL_FORECAST')

    def test_03_unknown_field_not_consensus(self):
        self.assertEqual(trading_economics_semantic('Previous'), 'UNKNOWN')

    def test_04_valid_candidate_pilot_eligible(self):
        self.assertEqual(classify_source(candidate(), release_timestamp_utc='2019-02-13T13:30:00Z'), 'PILOT_ELIGIBLE_CONSENSUS_SOURCE')

    def test_05_model_forecast_rejected(self):
        c = candidate(field_name='TEForecast', semantic='MODEL_FORECAST')
        self.assertEqual(classify_source(c), 'REJECT_SEMANTIC_MISMATCH')

    def test_06_non_point_in_time_rejected(self):
        c = candidate(historical_point_in_time=False)
        self.assertEqual(classify_source(c), 'REJECT_NOT_POINT_IN_TIME')

    def test_07_missing_consensus_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(consensus=None))

    def test_08_missing_provider_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(provider=''))

    def test_09_missing_provider_event_id_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(provider_event_id=''))

    def test_10_missing_link_key_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(link_key=''))

    def test_11_missing_economy_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(economy=''))

    def test_12_missing_currency_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(currency=''))

    def test_13_missing_reference_period_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(reference_period=''))

    def test_14_missing_source_identity_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(source_identity=''))

    def test_15_missing_raw_hash_rejected(self):
        with self.assertRaises(RND0070Error): validate_candidate(candidate(raw_hash=''))

    def test_16_consensus_at_release_rejected(self):
        c = candidate(captured_at_utc='2019-02-13T13:30:00Z')
        self.assertEqual(classify_source(c, release_timestamp_utc='2019-02-13T13:30:00Z'), 'REJECT_CHRONOLOGY_UNPROVEN')

    def test_17_consensus_after_release_rejected(self):
        c = candidate(captured_at_utc='2019-02-13T13:31:00Z')
        self.assertEqual(classify_source(c, release_timestamp_utc='2019-02-13T13:30:00Z'), 'REJECT_CHRONOLOGY_UNPROVEN')

    def test_18_pre_release_consensus_accepted(self):
        c = candidate(captured_at_utc='2019-02-13T13:29:59Z')
        self.assertEqual(classify_source(c, release_timestamp_utc='2019-02-13T13:30:00Z'), 'PILOT_ELIGIBLE_CONSENSUS_SOURCE')

    def test_19_mechanism_can_substitute_for_capture_timestamp(self):
        c = candidate(captured_at_utc=None, point_in_time_mechanism='documented historical snapshot semantics')
        self.assertEqual(classify_source(c), 'PILOT_ELIGIBLE_CONSENSUS_SOURCE')

    def test_20_late_coverage_rejected_for_full_development(self):
        c = candidate(coverage_start_year=2020, coverage_end_year=2024)
        self.assertEqual(classify_source(c, require_full_development=True), 'REJECT_DEVELOPMENT_COVERAGE')

    def test_21_full_2015_2020_coverage_eligible(self):
        self.assertEqual(classify_source(candidate(), require_full_development=True), 'FULL_DEVELOPMENT_CONSENSUS_SOURCE_ELIGIBLE')

    def test_22_market_outcome_contamination_rejected(self):
        with self.assertRaises(RND0070Error): validate_no_market_outcomes({'nested': {'pnl': 1.0}})

    def test_23_receipt_keeps_authorities_false(self):
        r = admission_receipt(candidate(), release_timestamp_utc='2019-02-13T13:30:00Z')
        self.assertTrue(r['outcome_blind'])
        for key in (
            'consensus_acquisition_authority','provider_purchase_authority','strategy_outcome_open',
            'validation_open','reserved_final_open','prospective_outcomes_open','promotion_authority',
            'broker_write_authority','capital_authority','live_execution_authority','automatic_merge'):
            self.assertIs(r[key], False)

    def test_24_architecture_status_preserves_separation(self):
        s = architecture_status()
        self.assertEqual(s['timing_dependency_status'], 'SOLVED_BY_RND0069_FOR_FROZEN_US_CPI_SAMPLE')
        self.assertEqual(s['consensus_dependency_status'], 'UNRESOLVED_PENDING_PROVIDER_PILOT')
        self.assertEqual(s['preferred_pilot_candidate'], 'TRADING_ECONOMICS')
        self.assertFalse(s['preferred_candidate_is_architecture_dependency'])
        self.assertEqual(s['te_forecast_semantic'], 'MARKET_CONSENSUS')
        self.assertEqual(s['te_teforecast_semantic'], 'MODEL_FORECAST')


if __name__ == '__main__':
    unittest.main()
