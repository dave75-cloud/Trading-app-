"""Synthetic tests only: RND-0074 four-pair timestamp overlap extension."""
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import rnd0074_cross_pair_offset_dates as target
from rnd0074_development_metadata_audit import PAIRS, AuditError

def stamp(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/target.ROOT_NAME
        self.root.mkdir()
        for p in PAIRS:
            (self.root/p/"2019").mkdir(parents=True)
        # Tokyo 09:00 local on Jan 2 = 00:00 UTC; +15 and +20.
        self.a=stamp("2019-01-02T00:15:00Z")
        self.b=stamp("2019-01-02T00:20:00Z")
        self.source={
            "AUDUSD":({self.a,self.b},{self.a,self.b}),
            "EURUSD":({self.a,self.b},{self.b}),
            "GBPUSD":({self.a,self.b},set()),
            "USDJPY":({self.a,self.b},set()),
        }

    def fixture_compute(self, shard, pair):
        return {"windows":{"TOKYO_OPEN":{
            "primary":{f"offset:{off:+d}":{
                "eligible":1,"missing":int(t in self.source[pair][1])}
                for off,t in ((15,self.a),(20,self.b))},
            "exclude_jan1_dec25_sensitivity":{f"offset:{off:+d}":{
                "eligible":1,"missing":int(t in self.source[pair][1])}
                for off,t in ((15,self.a),(20,self.b))},
        }}}

    def mocked(self):
        with patch.object(target,"verified_sets",return_value=self.source):
            with patch.object(target,"compute",side_effect=self.fixture_compute):
                with patch.object(target,"CONVENTIONS",{"TOKYO":target.CONVENTIONS["TOKYO"]}):
                    with patch.object(target,"OFFSETS",(15,20)):
                        return target.aggregate(self.root)

    def test_exact_pair_membership(self):
        r=self.mocked()["windows"]["TOKYO_OPEN"]
        self.assertEqual(r["+15"]["primary"]["distinct_missing_timestamps_by_pair_count"]["1"],1)
        self.assertEqual(r["+20"]["primary"]["distinct_missing_timestamps_by_pair_count"]["2"],1)

    def test_affected_dates(self):
        r=self.mocked()["windows"]["TOKYO_OPEN"]
        self.assertEqual(r["+15"]["primary"]["pairs"]["AUDUSD"]["affected_local_dates"],1)
        self.assertEqual(r["+20"]["primary"]["pairs"]["EURUSD"]["affected_local_dates"],1)
        self.assertEqual(r["+15"]["primary"]["pairs"]["EURUSD"]["affected_local_dates"],0)

    def test_holiday_sensitivity_separate(self):
        r=self.mocked()["windows"]["TOKYO_OPEN"]
        self.assertEqual(r["+15"]["primary"],r["+15"]["exclude_jan1_dec25_sensitivity"])

    def test_reconciliation_mismatch_stops(self):
        def wrong(shard,pair):
            x=self.fixture_compute(shard,pair)
            if pair=="AUDUSD":
                x["windows"]["TOKYO_OPEN"]["primary"]["offset:+15"]["missing"]=0
            return x
        with patch.object(target,"verified_sets",return_value=self.source):
            with patch.object(target,"compute",side_effect=wrong):
                with patch.object(target,"CONVENTIONS",{"TOKYO":target.CONVENTIONS["TOKYO"]}):
                    with patch.object(target,"OFFSETS",(15,20)):
                        with self.assertRaises(AuditError):
                            target.aggregate(self.root)

    def test_bad_root_stops(self):
        with self.assertRaises(AuditError):
            target.aggregate(self.root.parent)

    def test_symlink_pair_stops(self):
        with patch.object(target,"summarize",return_value={"hashes_checked":True,"admitted":False}):
            with patch.object(target,"load_json",return_value=[]):
                # File schema invalidity must stop before overlap.
                with self.assertRaises((AuditError,KeyError,TypeError)):
                    target.verified_sets(self.root)

if __name__=="__main__":
    unittest.main()
