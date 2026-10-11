import copy
import unittest

from rnd0060y_prospective_accumulation_health_monitor import (
    StructuralInput, RND0060YError, evaluate_health,
    validate_output_contract, compare_streams,
)


def q003(**kw):
    d=dict(stream_id='Q003',protocol_id='Q003-PROSPECTIVE-V1',evaluation_time_utc='2026-10-20T00:00:00Z',
           ledger_identity='QLEDGER1',ledger_hash='abc123',record_count=3,last_sealed_evidence_timestamp='2026-10-19T00:00:00Z',
           next_expected_acquisition_boundary='2026-10-26T00:00:00Z')
    d.update(kw); return StructuralInput(**d)

def qr(**kw):
    d=dict(stream_id='RND0060QR',protocol_id='RND0060Q-V1',evaluation_time_utc='2026-10-20T00:00:00Z',
           ledger_identity='RLEDGER1',ledger_hash='def456',record_count=8,eligible_non_defer_count=8,
           last_sealed_evidence_timestamp='2026-10-19T00:00:00Z',next_expected_acquisition_boundary='2026-10-20T12:00:00Z')
    d.update(kw); return StructuralInput(**d)

class TestRND0060Y(unittest.TestCase):
    def test_01_clean_q003_accumulating(self):
        self.assertEqual(evaluate_health(q003())['health_state'],'HEALTHY_ACCUMULATING')

    def test_02_clean_qr_accumulating(self):
        self.assertEqual(evaluate_health(qr())['health_state'],'HEALTHY_ACCUMULATING')

    def test_03_q003_time_progress_never_opens_economics(self):
        out=evaluate_health(q003(evaluation_time_utc='2027-04-03T07:25:00Z'))
        self.assertFalse(out['economic_fields_open'])

    def test_04_qr_structural_count_visible_without_economics(self):
        out=evaluate_health(qr(eligible_non_defer_count=42))
        self.assertEqual(out['eligible_non_defer_count'],42); self.assertFalse(out['economic_fields_open'])

    def test_05_stream_counters_independent(self):
        out=compare_streams(q003(record_count=5),qr(record_count=7,eligible_non_defer_count=6))
        self.assertEqual(out['Q003']['record_count'],5); self.assertEqual(out['RND0060QR']['eligible_non_defer_count'],6)
        self.assertNotIn('eligible_non_defer_count',out['Q003'])

    def test_06_prestart_contamination_remediation(self):
        self.assertEqual(evaluate_health(q003(pre_start_contamination_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_07_duplicate_identity_remediation(self):
        self.assertEqual(evaluate_health(q003(duplicate_identity_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_08_chronology_regression_remediation(self):
        self.assertEqual(evaluate_health(q003(chronology_regression_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_09_prohibited_partition_remediation(self):
        self.assertEqual(evaluate_health(qr(prohibited_partition_access_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_10_missing_provenance_remediation(self):
        self.assertEqual(evaluate_health(q003(missing_provenance_hash_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_11_evidence_mutation_remediation(self):
        self.assertEqual(evaluate_health(qr(evidence_mutation_count=1))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_12_recoverable_scheduler_delay_attention(self):
        self.assertEqual(evaluate_health(q003(recoverable_scheduler_delay=True))['health_state'],'ATTENTION_REQUIRED')

    def test_13_unexplained_gap_remediation(self):
        self.assertEqual(evaluate_health(qr(unexplained_gap_count=1,recovery_receipt_present=False))['health_state'],'STRUCTURAL_REMEDIATION_REQUIRED')

    def test_14_duplicate_scheduler_attention(self):
        self.assertEqual(evaluate_health(q003(duplicate_scheduler_acquisition=True))['health_state'],'ATTENTION_REQUIRED')

    def test_15_early_acquisition_attention_not_progress(self):
        out=evaluate_health(q003(acquisition_before_close_boundary=True,evaluation_time_utc='2027-04-03T07:25:00Z'))
        self.assertEqual(out['health_state'],'ATTENTION_REQUIRED')

    def test_16_q003_no_early_readout(self):
        self.assertNotEqual(evaluate_health(q003(evaluation_time_utc='2027-04-03T07:24:59Z'))['health_state'],'READOUT_ELIGIBLE_PENDING_HUMAN_GATE')

    def test_17_qr_no_early_readout(self):
        self.assertNotEqual(evaluate_health(qr(evaluation_time_utc='2027-04-07T02:33:49Z',eligible_non_defer_count=100))['health_state'],'READOUT_ELIGIBLE_PENDING_HUMAN_GATE')

    def test_18_qr_below_100_stays_accumulating(self):
        out=evaluate_health(qr(evaluation_time_utc='2027-04-08T00:00:00Z',eligible_non_defer_count=99))
        self.assertEqual(out['health_state'],'HEALTHY_ACCUMULATING')

    def test_19_q003_clean_at_minimum_readout_pending_human(self):
        out=evaluate_health(q003(evaluation_time_utc='2027-04-03T07:25:00Z'))
        self.assertEqual(out['health_state'],'READOUT_ELIGIBLE_PENDING_HUMAN_GATE'); self.assertFalse(out['economic_fields_open'])

    def test_20_qr_clean_at_minimum_and_100_readout_pending_human(self):
        out=evaluate_health(qr(evaluation_time_utc='2027-04-07T02:33:50Z',eligible_non_defer_count=100))
        self.assertEqual(out['health_state'],'READOUT_ELIGIBLE_PENDING_HUMAN_GATE'); self.assertFalse(out['economic_fields_open'])

    def test_21_prohibited_economic_output_fails_contract(self):
        out=evaluate_health(q003())
        bad=dict(out); bad['pnl']=1.0
        with self.assertRaises(RND0060YError): validate_output_contract(bad)

    def test_22_all_authority_fields_false(self):
        out=evaluate_health(q003())
        for k in ('economic_fields_open','promotion_authority','broker_write_authority','capital_authority','live_execution_authority','reserved_final_open','automatic_merge'):
            self.assertIs(out[k],False)

    def test_23_reserved_final_closed(self):
        out=evaluate_health(qr()); self.assertFalse(out['reserved_final_open'])

    def test_24_deterministic_replay(self):
        a=evaluate_health(qr(evaluation_time_utc='2026-12-01T00:00:00Z',eligible_non_defer_count=21))
        b=evaluate_health(qr(evaluation_time_utc='2026-12-01T00:00:00Z',eligible_non_defer_count=21))
        self.assertEqual(a,b)

if __name__=='__main__': unittest.main()
