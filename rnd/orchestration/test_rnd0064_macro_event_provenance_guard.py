import copy
import unittest

from rnd0064_macro_event_provenance_guard import (
    RawEvent, RND0064Error, normalize_event, validate_revision_lineage,
    classify_source_pilot,
)


def ev(**kw):
    d=dict(
        provider='TEST',provider_event_id='E1',event_series='CPI',economy='US',currency='USD',
        scheduled_timestamp='2018-01-12T13:30:00Z',timestamp_precision='EXACT',
        actual_as_released=2.1,consensus=2.0,previous=1.9,revised_previous=1.8,
        unit='%',reference_period='2017-12',raw_hash='raw123',source_identity='SRC1'
    )
    d.update(kw)
    return RawEvent(**d)

class TestRND0064(unittest.TestCase):
    def test_01_missing_consensus_stays_missing(self):
        out=normalize_event(ev(consensus=None))
        self.assertIsNone(out['consensus']); self.assertFalse(out['consensus_available'])

    def test_02_revision_cannot_overwrite_actual(self):
        self.assertTrue(validate_revision_lineage(2.1,2.2,2.1))
        with self.assertRaises(RND0064Error): validate_revision_lineage(2.1,2.2,2.2)

    def test_03_timezone_normalization_deterministic(self):
        a=normalize_event(ev(scheduled_timestamp='2018-01-12T08:30:00-05:00'))
        b=normalize_event(ev(provider_event_id='E2',scheduled_timestamp='2018-01-12T13:30:00Z'))
        self.assertEqual(a['scheduled_timestamp_utc'],b['scheduled_timestamp_utc'])

    def test_04_nonexact_time_ineligible(self):
        for i,p in enumerate(['ESTIMATED','TENTATIVE','NON_TIMED'],2):
            self.assertFalse(normalize_event(ev(provider_event_id=f'E{i}',timestamp_precision=p))['exact_time_eligible'])

    def test_05_cancelled_preserved_and_ineligible(self):
        out=normalize_event(ev(cancelled=True)); self.assertTrue(out['cancelled']); self.assertFalse(out['exact_time_eligible'])

    def test_06_reschedule_lineage_preserved(self):
        out=normalize_event(ev(rescheduled_from='2018-01-11T13:30:00Z'))
        self.assertEqual(out['rescheduled_from'],'2018-01-11T13:30:00Z')

    def test_07_duplicate_detected(self):
        seen=set(); normalize_event(ev(),seen_ids=seen)
        with self.assertRaises(RND0064Error): normalize_event(ev(),seen_ids=seen)

    def test_08_unknown_precision_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(timestamp_precision='MAYBE'))

    def test_09_missing_source_identity_fails(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(source_identity=''))

    def test_10_raw_hash_lineage_retained(self):
        out=normalize_event(ev()); self.assertEqual(out['raw_hash'],'raw123'); self.assertTrue(out['normalized_hash'])

    def test_11_market_outcomes_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(),extra_fields={'pnl':1.0})

    def test_12_provider_selection_has_no_market_fields(self):
        out=classify_source_pilot(total_events=100,exact_timed=100,consensus_count=90,actual_count=100,provenance_failures=0,duplicate_count=0,unexplained_gaps=0)
        for k in ('pnl','fx_return','hit_rate','pair_rank'): self.assertNotIn(k,out)

    def test_13_validation_partition_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(partition='VALIDATION_2021_2022'))

    def test_14_reserved_final_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(partition='RESERVED_FINAL_2023_2024'))

    def test_15_q003_contamination_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(prospective_source='Q003'))

    def test_16_qr_contamination_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(prospective_source='RND0060QR'))

    def test_17_deterministic_replay(self):
        a=normalize_event(ev()); b=normalize_event(ev()); self.assertEqual(a,b)

    def test_18_all_authority_fields_false(self):
        out=normalize_event(ev())
        for k in ('promotion_authority','broker_write_authority','capital_authority','live_execution_authority','automatic_merge'):
            self.assertIs(out[k],False)

    def test_19_missing_actual_preserved(self):
        out=normalize_event(ev(actual_as_released=None)); self.assertIsNone(out['actual_as_released']); self.assertFalse(out['actual_available'])

    def test_20_naive_timestamp_rejected(self):
        with self.assertRaises(RND0064Error): normalize_event(ev(scheduled_timestamp='2018-01-12T13:30:00'))

    def test_21_good_source_admissible(self):
        out=classify_source_pilot(total_events=100,exact_timed=98,consensus_count=85,actual_count=99,provenance_failures=0,duplicate_count=0,unexplained_gaps=0)
        self.assertEqual(out['classification'],'SOURCE_ADMISSIBLE_FOR_STRUCTURAL_NORMALIZATION')

    def test_22_structural_fail_source_not_admissible(self):
        out=classify_source_pilot(total_events=100,exact_timed=100,consensus_count=100,actual_count=100,provenance_failures=1,duplicate_count=0,unexplained_gaps=0)
        self.assertEqual(out['classification'],'SOURCE_NOT_ADMISSIBLE_FOR_POINT_IN_TIME_RESEARCH')

    def test_23_partial_source_documented_limitations(self):
        out=classify_source_pilot(total_events=100,exact_timed=85,consensus_count=65,actual_count=95,provenance_failures=0,duplicate_count=0,unexplained_gaps=2)
        self.assertEqual(out['classification'],'SOURCE_ADMISSIBLE_WITH_DOCUMENTED_LIMITATIONS')

    def test_24_empty_pilot_inconclusive(self):
        out=classify_source_pilot(total_events=0,exact_timed=0,consensus_count=0,actual_count=0,provenance_failures=0,duplicate_count=0,unexplained_gaps=0)
        self.assertEqual(out['classification'],'SOURCE_EVALUATION_INCONCLUSIVE')

if __name__=='__main__': unittest.main()
