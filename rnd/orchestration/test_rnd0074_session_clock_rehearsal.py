import unittest
from dataclasses import replace

from rnd0074_session_clock_rehearsal import (
    RND0074Error, AUTHORITY_FALSE, CONVENTIONS, PARTITION,
    _date, _time, _zoned, _utc, clock_receipt, overlap_minutes,
    reject_outcome_fields, session_interval,
)
from datetime import date, time
from zoneinfo import ZoneInfo


class TestRND0074(unittest.TestCase):
    def test_01_three_frozen_sessions(self):
        self.assertEqual(tuple(CONVENTIONS), ("TOKYO", "LONDON", "NEW_YORK"))

    def test_02_tokyo_winter_utc(self):
        self.assertEqual(session_interval("TOKYO", "2019-02-13").open_utc, "2019-02-13T00:00:00Z")

    def test_03_tokyo_summer_utc(self):
        self.assertEqual(session_interval("TOKYO", "2019-07-15").open_utc, "2019-07-15T00:00:00Z")

    def test_04_london_winter_utc(self):
        self.assertEqual(session_interval("LONDON", "2019-02-13").open_utc, "2019-02-13T08:00:00Z")

    def test_05_london_summer_utc(self):
        self.assertEqual(session_interval("LONDON", "2019-07-15").open_utc, "2019-07-15T07:00:00Z")

    def test_06_new_york_winter_utc(self):
        self.assertEqual(session_interval("NEW_YORK", "2019-02-13").open_utc, "2019-02-13T13:00:00Z")

    def test_07_new_york_summer_utc(self):
        self.assertEqual(session_interval("NEW_YORK", "2019-07-15").open_utc, "2019-07-15T12:00:00Z")

    def test_08_us_uk_dst_mismatch(self):
        day = "2019-03-11"
        self.assertEqual(overlap_minutes(session_interval("LONDON",day), session_interval("NEW_YORK",day)), 240)

    def test_09_ordinary_london_ny_overlap(self):
        day = "2019-07-15"
        self.assertEqual(overlap_minutes(session_interval("LONDON",day), session_interval("NEW_YORK",day)), 180)

    def test_10_tokyo_london_summer_overlap(self):
        day = "2019-07-15"
        self.assertEqual(overlap_minutes(session_interval("TOKYO",day), session_interval("LONDON",day)), 60)

    def test_11_tokyo_london_winter_no_overlap(self):
        day = "2019-02-13"
        self.assertEqual(overlap_minutes(session_interval("TOKYO",day), session_interval("LONDON",day)), 0)

    def test_12_weekends_rejected(self):
        with self.assertRaises(RND0074Error):
            session_interval("LONDON", "2019-07-13")

    def test_13_outside_frozen_year(self):
        with self.assertRaises(RND0074Error):
            session_interval("LONDON", "2023-07-14")

    def test_14_wrong_partition(self):
        with self.assertRaises(RND0074Error):
            session_interval("TOKYO", "2019-07-15", partition="RESERVED_FINAL_2023_2024")

    def test_15_bad_session(self):
        with self.assertRaises(RND0074Error):
            session_interval("SYDNEY", "2019-07-15")

    def test_16_override_forbidden(self):
        with self.assertRaises(RND0074Error):
            session_interval("TOKYO", "2019-07-15", overrides={"open":"08:00"})

    def test_17_outcome_field_rejected(self):
        with self.assertRaises(RND0074Error):
            reject_outcome_fields({"meta":{"Fx_ReTuRn":0.12}})

    def test_18_consensus_field_rejected(self):
        with self.assertRaises(RND0074Error):
            reject_outcome_fields({"events":[{"consensus":1.2}]})

    def test_19_frozen_interval_tampering(self):
        d = "2019-07-15"
        a = replace(session_interval("TOKYO",d), open_utc="2019-07-15T01:00:00Z")
        b = session_interval("LONDON",d)
        with self.assertRaises(RND0074Error):
            overlap_minutes(a,b)

    def test_20_same_session_rejected(self):
        a = session_interval("TOKYO","2019-07-15")
        with self.assertRaises(RND0074Error):
            overlap_minutes(a,a)

    def test_21_dst_ambiguous_local_time_rejected(self):
        with self.assertRaises(RND0074Error):
            _zoned(date(2019,11,3),time(1,30),ZoneInfo("America/New_York"))

    def test_22_dst_nonexistent_local_time_rejected(self):
        with self.assertRaises(RND0074Error):
            _zoned(date(2019,3,10),time(2,30),ZoneInfo("America/New_York"))

    def test_23_deterministic_receipt_and_no_market_claim(self):
        a = clock_receipt("2019-07-15")
        b = clock_receipt("2019-07-15")
        self.assertEqual(a,b)
        self.assertEqual(a["record_count"],3)
        for k in ("market_data_present","dealer_handoff_verified","predictive_edge_verified","holiday_calendar_verified"):
            self.assertIs(a[k],False)

    def test_24_authority_firewall(self):
        a = clock_receipt("2019-07-15")
        for key in AUTHORITY_FALSE:
            self.assertIs(a[key],False,key)


if __name__ == "__main__":
    unittest.main()
