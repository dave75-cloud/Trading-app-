"""RND-0074 synthetic offset-coverage checks; no archive data."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from rnd0074_session_offset_coverage import compute, finalize
from rnd0074_development_metadata_audit import AuditError, validate_timestamp_strings
from rnd0074_session_clock_rehearsal import session_interval

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.shard=Path(self.tmp.name)
        start=datetime(2019,1,1,tzinfo=timezone.utc)
        self.schedule=[(start+timedelta(minutes=5*i)).strftime("%Y-%m-%dT%H:%M:%SZ")
                       for i in range(576)]
        self.ledger={"missing_timestamps":["2019-01-02T00:00:00Z"],"unexpected_timestamps":[]}

    def run_fixture(self):
        def reader(path):
            return self.ledger if Path(path).name=="discrepancy_ledger.json" else self.schedule
        with patch("rnd0074_session_offset_coverage.summarize",
                   return_value={"hashes_checked":True,"admitted":False}):
            with patch("rnd0074_session_offset_coverage.load_json",side_effect=reader):
                return compute(self.shard,"EURUSD")

    def test_six_boundaries(self):
        self.assertEqual(6,len(self.run_fixture()["windows"]))

    def test_twelve_offsets(self):
        rows=self.run_fixture()["windows"]["TOKYO_OPEN"]["primary"]
        self.assertEqual(12,sum(k.startswith("offset:") for k in rows))

    def test_expected_missing(self):
        row=self.run_fixture()["windows"]["TOKYO_OPEN"]["primary"]["total"]
        self.assertEqual(row["missing"],1)

    def test_primary_vs_sensitivity(self):
        rows=self.run_fixture()["windows"]["TOKYO_OPEN"]
        self.assertGreater(rows["primary"]["total"]["slots"],
                           rows["exclude_jan1_dec25_sensitivity"]["total"]["slots"])

    def test_year_and_pair_fail(self):
        for pair,year in (("EURUSD",2018),("USDCAD",2019)):
            with self.assertRaises(AuditError):
                compute(self.shard,pair,year)

    def test_hash_gate_fail(self):
        with patch("rnd0074_session_offset_coverage.summarize",
                   side_effect=AuditError("SHA mismatch")):
            with self.assertRaises(AuditError):
                compute(self.shard,"EURUSD")

    def test_unexpected_separate(self):
        self.ledger={"missing_timestamps":[],"unexpected_timestamps":["2019-01-02T00:00:00Z"]}
        self.schedule.remove("2019-01-02T00:00:00Z")
        row=self.run_fixture()["windows"]["TOKYO_OPEN"]["primary"]["total"]
        self.assertEqual(1,row["unexpected"])
        self.assertEqual(0,row["missing"])

    def test_bad_timestamp_lists(self):
        for x in (["2019-01-01T00:00:00Z"]*2,
                  ["2019-01-01T00:05:00Z","2019-01-01T00:00:00Z"],
                  ["2019-01-01T00:01:00Z"]):
            with self.assertRaises(AuditError):
                validate_timestamp_strings(x,"schedule",2019)

    def test_denominator_failure(self):
        with self.assertRaises(AuditError):
            finalize(dict(slots=1,eligible=1,present=0,missing=0,
                          unscheduled=0,out_of_year=0,unexpected=0))

    def test_london_dst(self):
        self.assertIn("08:00",session_interval("LONDON","2019-03-29").open_utc)
        self.assertIn("07:00",session_interval("LONDON","2019-04-01").open_utc)

if __name__=="__main__":
    unittest.main()
