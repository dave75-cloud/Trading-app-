"""Synthetic bounded verification of RND-0074 calendar stratification and path checks."""
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import rnd0074_audusd_calendar_stratification as s
import rnd0074_shared_schedule_diagnostic as shared
from rnd0074_development_metadata_audit import PAIRS, AuditError
from rnd0074_session_clock_rehearsal import session_interval

def local_slot(d, offset):
    t=session_interval("NEW_YORK", d.isoformat()).close_utc
    return datetime.fromisoformat(t.replace("Z","+00:00"))+timedelta(minutes=offset)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.dates=(date(2019,1,2),date(2019,1,3))
        self.a=local_slot(self.dates[0],15)
        self.b=local_slot(self.dates[0],20)
        self.c=local_slot(self.dates[1],15)
        self.d=local_slot(self.dates[1],20)
        self.schedule={self.a,self.b,self.c,self.d}
        self.missing={p:set() for p in PAIRS}
        self.missing["AUDUSD"]={self.a,self.b,self.c}
        self.missing["EURUSD"]={self.b}

    def test_weekday_month_offset_and_date_union(self):
        x=s.cells_for_days(self.schedule,self.missing,self.dates)
        s.assert_consistency(x)
        self.assertEqual(x["audusd_missing_by_offset"],{"+15":2,"+20":1})
        self.assertEqual(x["audusd_distinct_affected_dates"],2)
        self.assertEqual(x["audusd_missing_timestamp_pair_membership"]["1"],2)
        self.assertEqual(x["audusd_missing_timestamp_pair_membership"]["2"],1)
        self.assertEqual(x["strata"]["month"]["01"]["eligible"],4)
        self.assertEqual(x["strata"]["month"]["01"]["missing"],3)
        self.assertEqual(x["strata"]["weekday"]["Wednesday"]["missing"],2)
        self.assertEqual(x["strata"]["weekday"]["Thursday"]["missing"],1)
        self.assertEqual(x["strata"]["offset"]["+20"]["present"],1)

    def test_unauthorized_weekend_rejected(self):
        with self.assertRaises(AuditError):
            s.cells_for_days(self.schedule,self.missing,[date(2019,1,5)])

    def test_wrong_year_rejected(self):
        with self.assertRaises(AuditError):
            s.cells_for_days(self.schedule,self.missing,[date(2018,1,2)])

    def test_stratum_mutation_detected(self):
        x=s.cells_for_days(self.schedule,self.missing,self.dates)
        x["strata"]["weekday"]["Wednesday"]["missing"] += 1
        with self.assertRaises(AuditError):
            s.assert_consistency(x)

    def test_sensitivity_holiday_exclusion(self):
        day=date(2019,12,25)
        slot=local_slot(day,15)
        schedule={slot}
        missing={p:set() for p in PAIRS}
        missing["AUDUSD"].add(slot)
        primary=s.cells_for_days(schedule,missing,[day])
        sensitivity=s.cells_for_days(schedule,missing,[])
        self.assertEqual(primary["audusd_missing_by_offset"]["+15"],1)
        self.assertEqual(sensitivity["audusd_missing_by_offset"]["+15"],0)

    def test_safe_file_rejects_symlink(self):
        a=self.root/"actual.json"
        a.write_text("[]")
        b=self.root/"link.json"
        b.symlink_to(a)
        with self.assertRaises(AuditError):
            shared.safe_file(b)

    def test_safe_directory_rejects_symlink(self):
        a=self.root/"real"
        a.mkdir()
        b=self.root/"dirlink"
        b.symlink_to(a,target_is_directory=True)
        with self.assertRaises(AuditError):
            shared.safe_directory(b)

    def test_verified_sources_rejects_symlinked_root(self):
        a=self.root/shared.ROOT_NAME
        a.mkdir()
        b=self.root/"link"
        b.symlink_to(a,target_is_directory=True)
        with self.assertRaises(AuditError):
            shared.verified_sources(b)

    def test_no_archive_mutation_or_admission(self):
        provenance={p:{"original_schedule_present":p=="AUDUSD"} for p in PAIRS}
        with patch.object(s,"verified_sources",return_value=(
            self.schedule,self.missing,provenance,"f"*64)):
            # Real full-year calendar loops, but only four eligible synthetic slots.
            out=s.analyze(self.root)
        self.assertFalse(out["admitted"])
        self.assertFalse(out["prices_parsed"])
        self.assertTrue(out["source_quarantine_unchanged"])
        self.assertFalse(out["limitations"]["original_source_restored"])
        self.assertEqual(out["exclude_jan1_dec25_sensitivity"]["audusd_distinct_affected_dates"],2)

if __name__=="__main__":
    unittest.main()
