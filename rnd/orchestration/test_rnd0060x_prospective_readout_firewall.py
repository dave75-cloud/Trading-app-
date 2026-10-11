import copy
import unittest

from rnd0060x_prospective_readout_firewall import (
    Q003_STREAM, ACTIVITY_STREAM, ReadinessInput, HumanReadoutReceipt,
    RND0060XError, evaluate_readiness, authorize_economic_readout,
    promotion_firewall,
)


def q003(**kw):
    d = dict(
        stream_id=Q003_STREAM,
        prospective_start_utc='2026-10-05T07:25:00Z',
        evaluation_time_utc='2027-04-03T07:25:00Z',
        minimum_horizon_days=180,
        elapsed_calendar_days=180,
        minimum_observation_count=None,
        eligible_observation_count=None,
        provenance_integrity_pass=True,
        duplicate_check_pass=True,
        chronology_check_pass=True,
        pre_start_contamination_count=0,
        prohibited_partition_access_count=0,
        cross_stream_outcome_contamination=False,
        early_economic_access_count=0,
        expected_evidence_accounted_for=True,
        protocol_version_known=True,
        evidence_ledger_present=True,
        hashes_present=True,
        evidence_mutation_detected=False,
        economic_fields_open=False,
        human_readout_gate=False,
        promotion_authority=False,
        broker_write_authority=False,
        capital_authority=False,
        live_execution_authority=False,
        reserved_final_open=False,
    )
    d.update(kw)
    return ReadinessInput(**d)


def qr(**kw):
    d = dict(
        stream_id=ACTIVITY_STREAM,
        prospective_start_utc='2026-10-09T02:33:50Z',
        evaluation_time_utc='2027-04-07T02:33:50Z',
        minimum_horizon_days=180,
        elapsed_calendar_days=180,
        minimum_observation_count=100,
        eligible_observation_count=100,
        provenance_integrity_pass=True,
        duplicate_check_pass=True,
        chronology_check_pass=True,
        pre_start_contamination_count=0,
        prohibited_partition_access_count=0,
        cross_stream_outcome_contamination=False,
        early_economic_access_count=0,
        expected_evidence_accounted_for=True,
        admit_group_count=50,
        veto_group_count=50,
        minimum_group_count=20,
        protocol_version_known=True,
        evidence_ledger_present=True,
        hashes_present=True,
        evidence_mutation_detected=False,
        economic_fields_open=False,
        human_readout_gate=False,
        promotion_authority=False,
        broker_write_authority=False,
        capital_authority=False,
        live_execution_authority=False,
        reserved_final_open=False,
    )
    d.update(kw)
    return ReadinessInput(**d)


def receipt(stream):
    return HumanReadoutReceipt(
        stream_id=stream,
        evidence_ledger_version='ledger-v1',
        readout_protocol_version='protocol-v1',
        authorization_timestamp_utc='2027-04-08T00:00:00Z',
        tuning_authorized=False,
        reserved_final_remains_closed=True,
        automatic_promotion_authorized=False,
    )


class TestRND0060X(unittest.TestCase):
    def test_01_q003_early_date_cannot_open(self):
        out = evaluate_readiness(q003(evaluation_time_utc='2027-04-03T07:24:59Z', elapsed_calendar_days=179))
        self.assertEqual(out['status'], 'ACCUMULATING_PROSPECTIVE_VALIDATION_EVIDENCE')

    def test_02_q003_exact_minimum_time_can_pass(self):
        out = evaluate_readiness(q003())
        self.assertEqual(out['status'], 'READOUT_ELIGIBLE_PENDING_HUMAN_GATE')

    def test_03_q003_prestart_contamination_fails_closed(self):
        out = evaluate_readiness(q003(pre_start_contamination_count=1))
        self.assertEqual(out['status'], 'INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE')

    def test_04_q003_duplicate_evidence_fails_closed(self):
        out = evaluate_readiness(q003(duplicate_check_pass=False))
        self.assertEqual(out['status'], 'INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE')

    def test_05_q003_economic_fields_need_human_receipt(self):
        ready = evaluate_readiness(q003())
        self.assertFalse(ready['economic_fields_open'])
        with self.assertRaises(RND0060XError):
            authorize_economic_readout({**ready, 'status':'ACCUMULATING_PROSPECTIVE_VALIDATION_EVIDENCE'}, receipt(Q003_STREAM))

    def test_06_activity_early_date_cannot_open(self):
        out = evaluate_readiness(qr(evaluation_time_utc='2027-04-07T02:33:49Z', elapsed_calendar_days=179))
        self.assertEqual(out['status'], 'ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE')

    def test_07_activity_180_days_but_lt100_stays_accumulating(self):
        out = evaluate_readiness(qr(eligible_observation_count=99))
        self.assertEqual(out['status'], 'ACCUMULATING_PROSPECTIVE_CONFIRMATION_EVIDENCE')

    def test_08_activity_180_and_100_can_be_human_gate_eligible(self):
        out = evaluate_readiness(qr())
        self.assertEqual(out['status'], 'READOUT_ELIGIBLE_PENDING_HUMAN_GATE')

    def test_09_activity_prestart_contamination_fails_closed(self):
        out = evaluate_readiness(qr(pre_start_contamination_count=1))
        self.assertEqual(out['status'], 'INCONCLUSIVE_EXTEND_CONFIRMATION')

    def test_10_duplicate_market_days_fail_closed(self):
        out = evaluate_readiness(qr(duplicate_check_pass=False))
        self.assertEqual(out['status'], 'INCONCLUSIVE_EXTEND_CONFIRMATION')

    def test_11_consumed_validation_reuse_fails_closed(self):
        out = evaluate_readiness(qr(prohibited_partition_access_count=1))
        self.assertEqual(out['status'], 'INCONCLUSIVE_EXTEND_CONFIRMATION')

    def test_12_reserved_final_access_fails_closed(self):
        with self.assertRaises(RND0060XError):
            evaluate_readiness(qr(reserved_final_open=True))

    def test_13_cross_stream_contamination_fails_closed(self):
        self.assertEqual(evaluate_readiness(q003(cross_stream_outcome_contamination=True))['status'], 'INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE')
        self.assertEqual(evaluate_readiness(qr(cross_stream_outcome_contamination=True))['status'], 'INCONCLUSIVE_EXTEND_CONFIRMATION')

    def test_14_chronology_regression_fails_closed(self):
        self.assertEqual(evaluate_readiness(q003(chronology_check_pass=False))['status'], 'INCONCLUSIVE_EXTEND_OR_REMEDIATE_STRUCTURE')
        self.assertEqual(evaluate_readiness(qr(chronology_check_pass=False))['status'], 'INCONCLUSIVE_EXTEND_CONFIRMATION')

    def test_15_missing_provenance_hash_identity_fails_closed(self):
        with self.assertRaises(RND0060XError):
            evaluate_readiness(q003(hashes_present=False))
        with self.assertRaises(RND0060XError):
            evaluate_readiness(qr(evidence_ledger_present=False))

    def test_16_human_receipt_is_stream_specific(self):
        ready = evaluate_readiness(q003())
        with self.assertRaises(RND0060XError):
            authorize_economic_readout(ready, receipt(ACTIVITY_STREAM))

    def test_17_receipt_cannot_authorize_tuning(self):
        ready = evaluate_readiness(q003())
        bad = HumanReadoutReceipt(Q003_STREAM,'ledger-v1','protocol-v1','2027-04-08T00:00:00Z',True,True,False)
        with self.assertRaises(RND0060XError):
            authorize_economic_readout(ready, bad)

    def test_18_positive_outcome_cannot_set_promotion_authority(self):
        opened = authorize_economic_readout(evaluate_readiness(q003()), receipt(Q003_STREAM))
        out = promotion_firewall(opened, positive_outcome=True)
        self.assertTrue(out['positive_outcome'])
        self.assertFalse(out['promotion_authority'])
        self.assertTrue(out['human_promotion_review_required'])

    def test_19_live_capital_broker_attempts_fail_closed(self):
        for kw in (
            {'broker_write_authority':True}, {'capital_authority':True}, {'live_execution_authority':True}
        ):
            with self.assertRaises(RND0060XError):
                evaluate_readiness(q003(**kw))
        opened = authorize_economic_readout(evaluate_readiness(q003()), receipt(Q003_STREAM))
        with self.assertRaises(RND0060XError):
            promotion_firewall(opened, positive_outcome=True, broker_write_authority=True)

    def test_20_reserved_final_remains_closed(self):
        ready = evaluate_readiness(q003())
        opened = authorize_economic_readout(ready, receipt(Q003_STREAM))
        promoted = promotion_firewall(opened, positive_outcome=True)
        self.assertFalse(ready['reserved_final_open'])
        self.assertFalse(opened['reserved_final_open'])
        self.assertFalse(promoted['reserved_final_open'])

    def test_21_deterministic_readiness(self):
        a = evaluate_readiness(qr())
        b = evaluate_readiness(qr())
        self.assertEqual(a, b)

    def test_22_stream_counters_remain_independent(self):
        with self.assertRaises(RND0060XError):
            evaluate_readiness(q003(minimum_observation_count=100, eligible_observation_count=100))
        out = evaluate_readiness(qr(eligible_observation_count=100))
        self.assertEqual(out['status'], 'READOUT_ELIGIBLE_PENDING_HUMAN_GATE')

    def test_23_structural_eligibility_not_economic_success(self):
        for inp in (q003(), qr()):
            out = evaluate_readiness(inp)
            self.assertTrue(out['structural_eligibility_only'])
            self.assertIsNone(out['economic_success'])

    def test_24_no_machine_path_direct_to_promotion(self):
        opened = authorize_economic_readout(evaluate_readiness(qr()), receipt(ACTIVITY_STREAM))
        with self.assertRaises(RND0060XError):
            promotion_firewall(opened, positive_outcome=True, request_promotion=True)


if __name__ == '__main__':
    unittest.main()
