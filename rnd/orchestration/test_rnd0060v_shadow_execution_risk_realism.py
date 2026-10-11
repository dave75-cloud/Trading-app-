import copy
import unittest

from rnd0060v_shadow_execution_risk_realism import (
    QuoteSnapshot, RiskState, ShadowRequest, RND0060VError,
    simulate_shadow_execution, validate_replacement, audit_lineage,
)


def q(**kw):
    d=dict(instrument='EURUSD',bid=1.1000,ask=1.1002,quote_timestamp_utc=110.0,
           quote_source_identity='SRC',quote_sequence=1,session_state='OPEN',provider_state='CONNECTED',fresh=True,degraded_integrity_pass=False)
    d.update(kw); return QuoteSnapshot(**d)

def r(**kw):
    d=dict(risk_state_id='R1',portfolio_state_id='P1',fresh=True,reconciliation_state='RECONCILED',kill_state=None,
           mode='SHADOW_ONLY',broker_write_authority=False)
    d.update(kw); return RiskState(**d)

def s(**kw):
    d=dict(request_id='X1',parent_intent_id='I1',parent_risk_id='RD1',parent_admissibility_id='A1',parent_signal_id='S1',
           instrument='EURUSD',direction='LONG',requested_exposure=10.0,authorized_exposure=8.0,intent_timestamp_utc=100.0,
           slippage=0.0001,latency_seconds=5.0,fill_fraction=1.0,simulate_reject=False,mode='SHADOW_ONLY',broker_write_authority=False,replacement_of=None)
    d.update(kw); return ShadowRequest(**d)

class TestRND0060V(unittest.TestCase):
    def test_01_long_uses_ask(self):
        out=simulate_shadow_execution(s(direction='LONG'),q(),r())
        self.assertEqual(out['reference_executable_side'],'ASK'); self.assertGreaterEqual(out['simulated_fill_price'],1.1002)

    def test_02_short_uses_bid(self):
        out=simulate_shadow_execution(s(direction='SHORT'),q(),r())
        self.assertEqual(out['reference_executable_side'],'BID'); self.assertLessEqual(out['simulated_fill_price'],1.1000)

    def test_03_adverse_slippage_sign(self):
        lo=simulate_shadow_execution(s(direction='LONG',slippage=0.0003),q(),r())
        sh=simulate_shadow_execution(s(direction='SHORT',slippage=0.0003,request_id='X2'),q(),r())
        self.assertAlmostEqual(lo['simulated_fill_price'],1.1005,places=12); self.assertAlmostEqual(sh['simulated_fill_price'],1.0997,places=12)

    def test_04_negative_slippage_fails(self):
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(slippage=-0.1),q(),r())

    def test_05_stale_quote_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(),q(fresh=False),r())['rejection_code'],'STALE_QUOTE')

    def test_06_crossed_or_invalid_quote_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(),q(bid=1.2,ask=1.1),r())['rejection_code'],'INVALID_QUOTE')

    def test_07_closed_unknown_session_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(),q(session_state='CLOSED'),r())['rejection_code'],'SESSION_CLOSED')
        self.assertEqual(simulate_shadow_execution(s(request_id='X2'),q(session_state='UNKNOWN'),r())['rejection_code'],'UNKNOWN_SESSION')

    def test_08_disconnected_unknown_provider_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(),q(provider_state='DISCONNECTED'),r())['rejection_code'],'PROVIDER_DISCONNECTED')
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(request_id='X2'),q(provider_state='MYSTERY'),r())

    def test_09_partial_fill_cannot_exceed_authorization(self):
        out=simulate_shadow_execution(s(fill_fraction=0.5),q(),r()); self.assertEqual(out['filled_exposure'],4.0)
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(request_id='X2',fill_fraction=1.1),q(),r())

    def test_10_rejected_fill_zero_exposure(self):
        out=simulate_shadow_execution(s(simulate_reject=True),q(),r()); self.assertEqual(out['filled_exposure'],0.0)

    def test_11_duplicate_request_cannot_double_fill(self):
        seen=set(); a=simulate_shadow_execution(s(),q(),r(),seen); b=simulate_shadow_execution(s(),q(),r(),seen)
        self.assertEqual(a['simulated_status'],'FILLED'); self.assertEqual(b['rejection_code'],'DUPLICATE_REQUEST')

    def test_12_replace_cannot_enlarge_invert_substitute(self):
        orig=s()
        self.assertTrue(validate_replacement(orig,s(request_id='X2',replacement_of='X1',authorized_exposure=7.0)))
        for bad in [s(request_id='X3',replacement_of='X1',authorized_exposure=9.0),s(request_id='X4',replacement_of='X1',direction='SHORT'),s(request_id='X5',replacement_of='X1',instrument='GBPUSD')]:
            with self.assertRaises(RND0060VError): validate_replacement(orig,bad)

    def test_13_timestamp_latency_violation_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(latency_seconds=20),q(quote_timestamp_utc=110),r())['rejection_code'],'LATENCY_VIOLATION')

    def test_14_stale_risk_state_rejects(self):
        self.assertEqual(simulate_shadow_execution(s(),q(),r(fresh=False))['rejection_code'],'RISK_STATE_STALE')

    def test_15_reconciliation_pending_failed_block(self):
        for i,state in enumerate(['RECONCILIATION_PENDING','RECONCILIATION_FAILED'],2):
            self.assertEqual(simulate_shadow_execution(s(request_id=f'X{i}'),q(),r(reconciliation_state=state))['rejection_code'],'RECONCILIATION_BLOCK')

    def test_16_kill_dominates(self):
        self.assertEqual(simulate_shadow_execution(s(),q(),r(kill_state='GLOBAL_KILL'))['rejection_code'],'KILL_ACTIVE')

    def test_17_exposure_monotonicity(self):
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(authorized_exposure=11.0),q(),r())
        out=simulate_shadow_execution(s(fill_fraction=.75),q(),r()); self.assertLessEqual(out['filled_exposure'],out['authorized_exposure']); self.assertLessEqual(out['authorized_exposure'],out['requested_exposure'])

    def test_18_shadow_only_and_no_broker_write_immutable(self):
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(mode='LIVE'),q(),r())
        with self.assertRaises(RND0060VError): simulate_shadow_execution(s(request_id='X2',broker_write_authority=True),q(),r())

    def test_19_audit_lineage_complete(self):
        out=simulate_shadow_execution(s(),q(),r()); self.assertTrue(audit_lineage(out))
        broken=dict(out); broken['parent_signal_id']=''; self.assertFalse(audit_lineage(broken))

    def test_20_deterministic_replay(self):
        a=simulate_shadow_execution(s(),q(),r())
        b=simulate_shadow_execution(s(),q(),r())
        self.assertEqual(a,b)

if __name__=='__main__': unittest.main()
