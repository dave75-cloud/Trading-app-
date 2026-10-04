#!/usr/bin/env python3
import json, tempfile, unittest
from pathlib import Path
import rnd0042_validation_candidate as r

class TestRND0042ValidationCandidate(unittest.TestCase):
    def test_authorization_is_fixed_candidate_only(self):
        a=r.authorization()
        self.assertEqual(a["candidate_threshold"],0.0006)
        self.assertTrue(a["validation_outcomes_authorized"])
        self.assertFalse(a["alternate_thresholds"])
        self.assertFalse(a["reserved_final_open"])
    def test_load_rows_rejects_final_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"AUDUSD"/"validation"; p.mkdir(parents=True)
            (p/"canonical_rows.json").write_text(json.dumps([{"timestamp_utc":"2023-01-01T09:40:00Z"}]))
            with self.assertRaises(r.RND0042Error): r.load_rows(tmp,"AUDUSD")
    def test_load_rows_accepts_fractional_validation_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"AUDUSD"/"validation"; p.mkdir(parents=True)
            (p/"canonical_rows.json").write_text(json.dumps([{"timestamp_utc":"2021-01-04T00:00:00.000000000Z"}]))
            self.assertEqual(len(r.load_rows(tmp,"AUDUSD")),1)
    def base(self):
        return {"1_terminal_equity_positive":True,"2_realized_net_positive":True,"3_at_least_3_pairs_nonnegative":True,"4_pair_concentration_ok":True,"5_year_concentration_ok":True,"6_drawdown_ok":True,"7_identity_boundary_warmup_ok":True}
    def test_classification_supported(self):
        self.assertEqual(r.classify(self.base()),"VALIDATION_SUPPORTED")
    def test_classification_rejected_on_primary_failure(self):
        c=self.base(); c["1_terminal_equity_positive"]=False
        self.assertEqual(r.classify(c),"VALIDATION_REJECTED")
    def test_classification_inconclusive_on_concentration_failure(self):
        c=self.base(); c["4_pair_concentration_ok"]=False
        self.assertEqual(r.classify(c),"VALIDATION_INCONCLUSIVE_CONCENTRATED")

if __name__=="__main__": unittest.main()
