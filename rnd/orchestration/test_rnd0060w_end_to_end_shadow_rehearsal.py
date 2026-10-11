import copy
import unittest
from unittest.mock import patch

from rnd0060w_end_to_end_shadow_rehearsal import run_rehearsal, RND0060WError


def base_case():
    return {
        'signal':{
            'signal_id':'SIG1','strategy_id':'STRAT1','strategy_version':'v1',
            'instrument':'EURUSD','direction':'LONG','requested_exposure':10.0,
            'signal_timestamp_utc':100.0,'source_evidence_identity':'E1',
            'strategy_promotion_receipt':'PROMO1','broker_write_authority':False,
        },
        'approved_strategy_id':'STRAT1','approved_strategy_version':'v1','seen_signal_ids':[],
        'valid_promotion_receipt':True,'prohibited_contamination':False,'timestamp_monotonic':True,
        'activity_decision':'ADMIT','activity_decision_id':'A1',
        'risk_decision':'AUTHORIZE_UNCHANGED','risk_decision_id':'R1','authorized_exposure':10.0,
        'critical_state_stale':False,'reconciliation_healthy':True,'kills':[],
        'intent_timestamp_utc':100.0,'intent_id':'I1','request_id':'X1','execution_id':'EX1',
        'quote':{
            'instrument':'EURUSD','bid':1.1000,'ask':1.1002,'quote_timestamp_utc':110.0,
            'quote_source_identity':'SRC','quote_sequence':1,'session_state':'OPEN',
            'provider_state':'CONNECTED','fresh':True,'degraded_integrity_pass':False,
        },
        'risk_state':{
            'risk_state_id':'RS1','portfolio_state_id':'P1','fresh':True,
            'reconciliation_state':'RECONCILED','kill_state':None,
            'mode':'SHADOW_ONLY','broker_write_authority':False,
        },
        'slippage':0.0001,'latency_seconds':5.0,'fill_fraction':1.0,
        'simulate_reject':False,'reconciliation_state':'RECONCILED',
        'reconciliation_event_id':'REC1',
    }

class TestRND0060W(unittest.TestCase):
    def test_01_happy_path_reconciles(self):
        out=run_rehearsal(base_case())
        self.assertEqual(out['terminal_state'],'SHADOW_CYCLE_RECONCILED')
        self.assertEqual(out['filled_exposure'],10.0)

    def test_02_provenance_rejection_halts(self):
        c=base_case(); c['valid_promotion_receipt']=False
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'PROVENANCE_REJECTED')
        self.assertEqual(out['filled_exposure'],0.0)
        self.assertNotIn('RISK_AUTHORIZATION',out['stage_trace'])

    def test_03_veto_halts_before_risk_execution(self):
        c=base_case(); c['activity_decision']='VETO'
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'ACTIVITY_VETOED')
        self.assertEqual(out['filled_exposure'],0.0)
        self.assertNotIn('RISK_AUTHORIZATION',out['stage_trace'])

    def test_04_defer_cannot_auto_release(self):
        c=base_case(); c['activity_decision']='DEFER'
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'ACTIVITY_DEFERRED')
        self.assertNotIn('SHADOW_EXECUTION_INTENT',out['stage_trace'])

    def test_05_risk_reduce_propagates_exactly(self):
        c=base_case(); c['risk_decision']='REDUCE'; c['authorized_exposure']=6.0
        out=run_rehearsal(c)
        self.assertEqual(out['intent']['authorized_exposure'],6.0)
        self.assertEqual(out['execution']['authorized_exposure'],6.0)
        self.assertEqual(out['filled_exposure'],6.0)

    def test_06_risk_reject_creates_no_execution_intent(self):
        c=base_case(); c['risk_decision']='REJECT'; c['authorized_exposure']=None
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'RISK_REJECTED')
        self.assertNotIn('SHADOW_EXECUTION_INTENT',out['stage_trace'])

    def test_07_stale_risk_state_blocks(self):
        c=base_case(); c['critical_state_stale']=True
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'RISK_REJECTED')
        self.assertEqual(out['filled_exposure'],0.0)

    def test_08_stale_quote_blocks_execution(self):
        c=base_case(); c['quote']['fresh']=False
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'SHADOW_EXECUTION_REJECTED')
        self.assertEqual(out['execution']['rejection_code'],'STALE_QUOTE')

    def test_09_disconnected_provider_blocks(self):
        c=base_case(); c['quote']['provider_state']='DISCONNECTED'
        out=run_rehearsal(c)
        self.assertEqual(out['execution']['rejection_code'],'PROVIDER_DISCONNECTED')

    def test_10_closed_session_blocks(self):
        c=base_case(); c['quote']['session_state']='CLOSED'
        out=run_rehearsal(c)
        self.assertEqual(out['execution']['rejection_code'],'SESSION_CLOSED')

    def test_11_partial_fill_respects_authorization(self):
        c=base_case(); c['risk_decision']='REDUCE'; c['authorized_exposure']=8.0; c['fill_fraction']=0.5
        out=run_rehearsal(c)
        self.assertEqual(out['filled_exposure'],4.0)
        self.assertLessEqual(out['filled_exposure'],out['execution']['authorized_exposure'])

    def test_12_rejected_fill_zero_exposure(self):
        c=base_case(); c['simulate_reject']=True
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'SHADOW_EXECUTION_REJECTED')
        self.assertEqual(out['filled_exposure'],0.0)

    def test_13_duplicate_request_cannot_double_apply(self):
        seen=set()
        first=run_rehearsal(base_case(),seen_request_ids=seen)
        second=run_rehearsal(base_case(),seen_request_ids=seen)
        self.assertEqual(first['terminal_state'],'SHADOW_CYCLE_RECONCILED')
        self.assertEqual(second['terminal_state'],'SHADOW_EXECUTION_REJECTED')
        self.assertEqual(second['execution']['rejection_code'],'DUPLICATE_REQUEST')

    def test_14_direction_cannot_invert_across_layers(self):
        c=base_case(); c['signal']['direction']='SHORT'
        out=run_rehearsal(c)
        self.assertEqual(out['signal']['direction'],'SHORT')
        self.assertEqual(out['intent']['direction'],'SHORT')
        self.assertEqual(out['terminal_state'],'SHADOW_CYCLE_RECONCILED')

    def test_15_instrument_cannot_substitute(self):
        c=base_case(); c['quote']['instrument']='GBPUSD'
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'SHADOW_EXECUTION_REJECTED')
        self.assertIn('instrument mismatch',out['reason'])

    def test_16_kill_state_dominates(self):
        c=base_case(); c['kills']=['GLOBAL_KILL']
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'KILLED')
        self.assertEqual(out['filled_exposure'],0.0)

    def test_17_reconciliation_pending_blocks(self):
        c=base_case(); c['reconciliation_state']='RECONCILIATION_PENDING'
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'RECONCILIATION_PENDING')
        self.assertTrue(out['blocks_new_intents'])
        with self.assertRaises(RND0060WError):
            run_rehearsal(base_case(),prior_reconciliation_block=True)

    def test_18_reconciliation_failed_blocks(self):
        c=base_case(); c['reconciliation_state']='RECONCILIATION_FAILED'
        out=run_rehearsal(c)
        self.assertEqual(out['terminal_state'],'RECONCILIATION_FAILED')
        self.assertTrue(out['blocks_new_intents'])

    def test_19_malformed_audit_lineage_fails_closed(self):
        with patch('rnd0060w_end_to_end_shadow_rehearsal.audit_lineage',return_value=False):
            with self.assertRaises(RND0060WError):
                run_rehearsal(base_case())

    def test_20_shadow_only_is_immutable(self):
        c=base_case(); c['risk_state']['mode']='LIVE'
        with self.assertRaises(RND0060WError):
            run_rehearsal(c)

    def test_21_broker_write_authority_remains_false(self):
        c=base_case(); c['risk_state']['broker_write_authority']=True
        with self.assertRaises(RND0060WError):
            run_rehearsal(c)
        out=run_rehearsal(base_case())
        self.assertFalse(out['broker_write_authority'])
        self.assertFalse(out['execution']['broker_write_authority'])

    def test_22_prohibited_evidence_authority_fields_rejected(self):
        for key in ('q003_outcomes','rnd0060r_outcomes','validation_data','reserved_final_data','broker_credentials','live_order_id','capital_authority'):
            c=base_case(); c[key]='FORBIDDEN'
            with self.assertRaises(RND0060WError):
                run_rehearsal(c)

    def test_23_exposure_monotonicity_end_to_end(self):
        c=base_case(); c['risk_decision']='REDUCE'; c['authorized_exposure']=7.0; c['fill_fraction']=0.5
        out=run_rehearsal(c)
        self.assertLessEqual(out['execution']['filled_exposure'],out['execution']['authorized_exposure'])
        self.assertLessEqual(out['execution']['authorized_exposure'],out['signal']['requested_exposure'])

    def test_24_deterministic_replay_identical(self):
        a=run_rehearsal(copy.deepcopy(base_case()))
        b=run_rehearsal(copy.deepcopy(base_case()))
        self.assertEqual(a,b)

if __name__=='__main__': unittest.main()
