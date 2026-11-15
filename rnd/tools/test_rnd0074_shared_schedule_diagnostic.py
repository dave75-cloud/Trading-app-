"""Synthetic gates for RND-0074 shared-reference diagnostic; no real archive reads."""
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import rnd0074_shared_schedule_diagnostic as diag
from rnd0074_development_metadata_audit import PAIRS, AuditError

def ts(value):
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/diag.ROOT_NAME
        self.root.mkdir()
        self.a=ts("2019-01-02T00:15:00Z")
        self.b=ts("2019-01-02T00:20:00Z")
        self.schedule={self.a,self.b}
        self.missing={
            "AUDUSD":{self.a,self.b},
            "EURUSD":{self.b},
            "GBPUSD":set(),
            "USDJPY":set(),
        }
        self.provenance={p:{
            "original_schedule_present":p=="AUDUSD",
            "schedule_reference":"original_file" if p=="AUDUSD" else
                "verified_AUDUSD_2019_shared_reference",
            "non_schedule_original_sha256_checked":True,
            "source_quarantine":"QUARANTINED_UNRESOLVED_DISCREPANCIES"} for p in PAIRS}

    def strict_fixture(self,*args):
        return {"windows":{
            "TOKYO_OPEN":{
                v:{f"offset:{off:+d}":{
                    "eligible":1,
                    "missing":1
                } for off in (15,20)}
                for v in ("primary","exclude_jan1_dec25_sensitivity")},
            "TOKYO_CLOSE":{
                v:{f"offset:{off:+d}":{
                    "eligible":0,
                    "missing":0
                } for off in (15,20)}
                for v in ("primary","exclude_jan1_dec25_sensitivity")},
        }}

    def run_fixture(self,strict=None):
        with patch.object(diag,"verified_sources",return_value=(
            self.schedule,self.missing,self.provenance,"a"*64)):
            with patch.object(diag,"compute",side_effect=strict or self.strict_fixture):
                with patch.object(diag,"CONVENTIONS",{"TOKYO":diag.CONVENTIONS["TOKYO"]}):
                    with patch.object(diag,"OFFSETS",(15,20)):
                        # The separately calculated union uses NEW_YORK close,
                        # but the mock M5 timestamps are Tokyo opening.
                        return diag.analyze(self.root)

    def test_cross_pair_membership(self):
        r=self.run_fixture()
        o=r["windows"]["TOKYO_OPEN"]["exclude_jan1_dec25_sensitivity"]
        self.assertEqual(o["+15"]["membership"]["1"],1)
        self.assertEqual(o["+20"]["membership"]["2"],1)
        self.assertEqual(o["+15"]["pairs"]["AUDUSD"]["affected_local_dates"],1)
        self.assertEqual(o["+20"]["pairs"]["EURUSD"]["missing"],1)

    def test_provenance_not_admitted(self):
        r=self.run_fixture()
        self.assertFalse(r["admitted"])
        self.assertFalse(r["original_schedule_files_verified_for_all_pairs"])
        self.assertFalse(r["original_source_restored"])
        self.assertFalse(r["prices_parsed"])
        self.assertEqual(r["source_provenance"]["GBPUSD"]["original_schedule_present"],False)

    def test_strict_reconciliation_rejects(self):
        def bad(*args):
            x=self.strict_fixture()
            x["windows"]["TOKYO_OPEN"]["primary"]["offset:+15"]["missing"]=0
            return x
        with self.assertRaises(AuditError):
            self.run_fixture(strict=bad)

    def test_missing_schedule_digest_rejected(self):
        # A manifest without the shared file hash is never accepted.
        with patch.object(diag,"summarize",return_value={
            "hashes_checked":True,"admitted":False}):
            with patch.object(diag,"load_json",side_effect=[
                ["2019-01-02T00:15:00Z"],
                {"standard_schedule_sha256":"a"*64},
                {"symbol":"AUDUSD",**diag.IDENTITY,
                 "standard_schedule_file_sha256":"incorrect",
                 "standard_schedule_sha256":"a"*64},
            ]):
                with patch.object(diag,"sha256_file",return_value="a"*64):
                    (self.root/"AUDUSD"/"2019").mkdir(parents=True)
                    for n in ("standard_schedule.json",
                              "quarantine_manifest.json",
                              "discrepancy_ledger.json"):
                        (self.root/"AUDUSD"/"2019"/n).touch()
                    with self.assertRaises(AuditError):
                        diag.verified_sources(self.root)

    def test_bad_root_rejected(self):
        with self.assertRaises(AuditError):
            diag.analyze(self.root.parent)

if __name__=="__main__":
    unittest.main()
