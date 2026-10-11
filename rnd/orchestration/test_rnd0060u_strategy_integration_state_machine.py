import unittest

from rnd0060u_strategy_integration_state_machine import (
    RND0060UError, validate_signal, provenance_check, activity_admissibility,
    risk_authorize, make_shadow_intent, simulate_shadow, reconcile,
    audit_commit, terminal_from
)


def signal():
    return {
        'signal_id':'sig-1','strategy_id':'strat-A','strategy_version':'1.0',
        'instrument':'EURUSD','direction':'LONG','requested_exposure':1.0,
        'signal_timestamp_utc':'2026-10-11T10:00:00Z',
        'source_evidence_identity':'evidence-sha','strategy_promotion_receipt':'promo-sha',
        'broker_write_authority':False,
    }

class TestRND0060U(unittest.TestCase):
    def test_01_valid_signal(self): self.assertEqual(validate_signal(signal())['signal_id'],'sig-1')
    def test_02_missing_provenance_fails_closed(self):
        s=signal(); del s['strategy_promotion_receipt']
        with self.assertRaises(RND0060UError): validate_signal(s)
    def test_03_duplicate_signal_rejected(self):
        r=provenance_check(signal(),seen_signal_ids=['sig-1'],approved_strategy_id='strat-A',approved_strategy_version='1.0')
        self.assertEqual(r['reason'],'DUPLICATE_SIGNAL_ID')
    def test_04_unapproved_strategy_rejected(self):
        r=provenance_check(signal(),seen_signal_ids=[],approved_strategy_id='strat-B',approved_strategy_version='1.0')
        self.assertEqual(r['decision'],'REJECT_PROVENANCE')
    def test_05_contamination_rejected(self):
        r=provenance_check(signal(),seen_signal_ids=[],approved_strategy_id='strat-A',approved_strategy_version='1.0',prohibited_contamination=True)
        self.assertEqual(r['reason'],'PROHIBITED_EVIDENCE_CONTAMINATION')
    def test_06_veto_cannot_expose(self):
        a=activity_admissibility(signal(),'VETO'); self.assertEqual(a['exposure'],0); self.assertEqual(a['terminal'],'ACTIVITY_VETOED')
    def test_07_defer_cannot_auto_release(self):
        a=activity_admissibility(signal(),'DEFER')
        with self.assertRaises(RND0060UError): risk_authorize(a,decision='AUTHORIZE_UNCHANGED')
    def test_08_admit_preserves_identity_and_size(self):
        a=activity_admissibility(signal(),'ADMIT')
        self.assertEqual((a['instrument'],a['direction'],a['requested_exposure']),('EURUSD','LONG',1.0))
    def test_09_risk_cannot_enlarge(self):
        a=activity_admissibility(signal(),'ADMIT')
        with self.assertRaises(RND0060UError): risk_authorize(a,decision='REDUCE',authorized_exposure=1.1)
    def test_10_risk_cannot_invert(self):
        a=activity_admissibility(signal(),'ADMIT')
        with self.assertRaises(RND0060UError): risk_authorize(a,decision='AUTHORIZE_UNCHANGED',direction='SHORT')
    def test_11_risk_can_reduce_only(self):
        a=activity_admissibility(signal(),'ADMIT'); r=risk_authorize(a,decision='REDUCE',authorized_exposure=0.4)
        self.assertEqual(r['authorized_exposure'],0.4)
    def test_12_stale_state_rejected(self):
        a=activity_admissibility(signal(),'ADMIT'); r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED',critical_state_stale=True)
        self.assertEqual(r['terminal'],'RISK_REJECTED')
    def test_13_shadow_only_mandatory(self):
        a=activity_admissibility(signal(),'ADMIT'); r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED')
        with self.assertRaises(RND0060UError): make_shadow_intent(r,admissibility_decision_id='a1',risk_decision_id='r1',intent_timestamp_utc='2026-10-11T10:00:01Z',mode='LIVE')
    def test_14_broker_write_authority_forbidden(self):
        a=activity_admissibility(signal(),'ADMIT'); r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED')
        with self.assertRaises(RND0060UError): make_shadow_intent(r,admissibility_decision_id='a1',risk_decision_id='r1',intent_timestamp_utc='2026-10-11T10:00:01Z',broker_write_authority=True)
    def test_15_simulation_never_calls_broker(self):
        a=activity_admissibility(signal(),'ADMIT'); r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED')
        i=make_shadow_intent(r,admissibility_decision_id='a1',risk_decision_id='r1',intent_timestamp_utc='2026-10-11T10:00:01Z')
        e=simulate_shadow(i); self.assertFalse(e['broker_endpoint_called'])
    def test_16_reconciliation_failure_blocks(self):
        s=signal(); a=activity_admissibility(s,'ADMIT'); r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED')
        i=make_shadow_intent(r,admissibility_decision_id='a1',risk_decision_id='r1',intent_timestamp_utc='2026-10-11T10:00:01Z'); e=simulate_shadow(i)
        q=reconcile(s,a,r,i,e,state='RECONCILIATION_FAILED'); self.assertTrue(q['blocks_new_intents']); self.assertEqual(q['terminal'],'RECONCILIATION_FAILED')
    def test_17_kill_precedence_dominates(self):
        a=activity_admissibility(signal(),'ADMIT')
        r=risk_authorize(a,decision='AUTHORIZE_UNCHANGED',kills=['RISK_LIMIT_KILL','GLOBAL_KILL'])
        self.assertEqual(r['kill'],'GLOBAL_KILL'); self.assertEqual(r['terminal'],'KILLED')
    def test_18_complete_audit_and_terminal(self):
        s=signal(); p=provenance_check(s,seen_signal_ids=[],approved_strategy_id='strat-A',approved_strategy_version='1.0')
        a=activity_admissibility(p['signal'],'ADMIT'); r=risk_authorize(a,decision='REDUCE',authorized_exposure=0.5)
        i=make_shadow_intent(r,admissibility_decision_id='a1',risk_decision_id='r1',intent_timestamp_utc='2026-10-11T10:00:01Z'); e=simulate_shadow(i)
        q=reconcile(s,a,r,i,e,state='RECONCILED')
        hashes={k:k+'-sha' for k in ('signal','activity','risk','intent','execution','reconciliation')}
        audit=audit_commit(signal=s,activity_decision_id='a1',risk_decision_id='r1',intent=i,execution=e,reconciliation=q,immutable_hashes=hashes)
        self.assertTrue(audit['append_only']); self.assertTrue(audit['reconstructable'])
        self.assertEqual(terminal_from(audit=audit)['terminal'],'SHADOW_CYCLE_RECONCILED')

if __name__=='__main__': unittest.main()
