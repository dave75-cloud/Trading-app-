import unittest

from rnd0066_fred_alfred_macro_provenance_backbone import (
    RND0066Error, FredVintageEvidence, TimingEvidence, ConsensusEvidence,
    backbone_record, compose_event, preserve_initial_actual, architecture_status,
)


def fred(**kw):
    d=dict(
        series_id='CPIAUCSL', link_key='US_CPI_HEADLINE',
        observation_date='2019-01-01', vintage_date='2019-02-13', value=252.561,
        unit='Index 1982-1984=100', reference_period='2019-01',
        economy='United States', currency='USD', raw_hash='fredhash',
        source_identity='FRED:CPIAUCSL:output_type=4', initial_release=True,
    )
    d.update(kw)
    return FredVintageEvidence(**d)


def timing(**kw):
    d=dict(
        provider='BLS_SCHEDULE', provider_event_id='BLS-CPI-2019-02',
        link_key='US_CPI_HEADLINE', event_series='CPI', economy='United States',
        currency='USD', reference_period='2019-01',
        scheduled_timestamp='2019-02-13T13:30:00Z', timestamp_precision='EXACT',
        raw_hash='timehash', source_identity='BLS release schedule',
    )
    d.update(kw)
    return TimingEvidence(**d)


def consensus(**kw):
    d=dict(
        provider='CONSENSUS_VENDOR', provider_event_id='CV-CPI-2019-02',
        link_key='US_CPI_HEADLINE', economy='United States', currency='USD',
        reference_period='2019-01', consensus=252.5,
        captured_at_utc='2019-02-13T13:00:00Z', semantic='MARKET_CONSENSUS',
        historical_point_in_time=True, raw_hash='conshash',
        source_identity='historical consensus snapshot',
    )
    d.update(kw)
    return ConsensusEvidence(**d)


class TestRND0066(unittest.TestCase):
    def test_01_fred_alone_is_backbone_only(self):
        out=backbone_record(fred())
        self.assertEqual(out['eligibility_state'],'BACKBONE_ONLY')
        self.assertFalse(out['surprise_eligible_inputs_present'])

    def test_02_fred_vintage_remains_date_only(self):
        out=backbone_record(fred())
        self.assertEqual(out['timestamp_precision'],'DATE_ONLY')
        self.assertFalse(out['exact_time_eligible'])

    def test_03_timestamp_in_fred_vintage_rejected(self):
        with self.assertRaises(RND0066Error): backbone_record(fred(vintage_date='2019-02-13T13:30:00Z'))

    def test_04_noninitial_vintage_not_actual_candidate(self):
        out=backbone_record(fred(initial_release=False,value=253.0,vintage_date='2019-03-12'))
        self.assertIsNone(out['actual_as_released_candidate'])

    def test_05_fred_cannot_supply_exact_timing(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(provider='FRED'),consensus())

    def test_06_nonexact_timing_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(timestamp_precision='ESTIMATED'),consensus())

    def test_07_fred_cannot_supply_consensus(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(provider='ALFRED'))

    def test_08_synthetic_consensus_semantic_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(semantic='MODEL_FORECAST'))

    def test_09_non_point_in_time_consensus_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(historical_point_in_time=False))

    def test_10_missing_consensus_rejected_not_imputed(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(consensus=None))

    def test_11_consensus_at_release_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(captured_at_utc='2019-02-13T13:30:00Z'))

    def test_12_consensus_after_release_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(captured_at_utc='2019-02-13T13:31:00Z'))

    def test_13_timing_link_mismatch_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(link_key='OTHER'),consensus())

    def test_14_consensus_link_mismatch_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(link_key='OTHER'))

    def test_15_economy_mismatch_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(economy='Canada'),consensus())

    def test_16_currency_mismatch_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(currency='EUR'))

    def test_17_reference_period_mismatch_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(reference_period='2018-12'),consensus())

    def test_18_composite_preserves_actual_and_consensus(self):
        out=compose_event(fred(),timing(),consensus())
        self.assertEqual(out['actual_as_released'],252.561)
        self.assertEqual(out['consensus'],252.5)

    def test_19_composite_is_exact_and_surprise_input_eligible(self):
        out=compose_event(fred(),timing(),consensus())
        self.assertTrue(out['exact_time_eligible'])
        self.assertTrue(out['surprise_eligible_inputs_present'])
        self.assertEqual(out['eligibility_state'],'SURPRISE_INPUT_ELIGIBLE')

    def test_20_field_level_provenance_survives(self):
        out=compose_event(fred(),timing(),consensus())
        self.assertEqual(out['field_provenance']['actual_as_released'],'FRED_ALFRED_INITIAL_RELEASE')
        self.assertEqual(out['field_provenance']['scheduled_timestamp_utc'],'BLS_SCHEDULE')
        self.assertEqual(out['field_provenance']['consensus'],'CONSENSUS_VENDOR')

    def test_21_duplicate_composite_identity_rejected(self):
        seen=set(); compose_event(fred(),timing(),consensus(),seen_ids=seen)
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(),seen_ids=seen)

    def test_22_market_outcome_field_rejected(self):
        with self.assertRaises(RND0066Error): compose_event(fred(),timing(),consensus(),extra_fields={'pnl':1.0})

    def test_23_later_revision_cannot_overwrite_initial(self):
        revised=fred(initial_release=False,value=253.2,vintage_date='2019-03-12')
        self.assertEqual(preserve_initial_actual(fred(),revised),252.561)

    def test_24_authority_and_access_firewall(self):
        s=architecture_status()
        self.assertEqual(s['canonical_schema'],'RND0064')
        self.assertFalse(s['fred_exact_intraday_timing_authority'])
        self.assertFalse(s['fred_market_consensus_authority'])
        for k in (
            'acquisition_authority','provider_purchase_authority','strategy_outcome_open',
            'validation_open','reserved_final_open','prospective_outcomes_open',
            'promotion_authority','broker_write_authority','capital_authority',
            'live_execution_authority','automatic_merge'):
            self.assertIs(s[k],False)


if __name__=='__main__':
    unittest.main()
