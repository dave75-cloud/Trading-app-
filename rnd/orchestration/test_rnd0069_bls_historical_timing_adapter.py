import unittest

from rnd0069_bls_historical_timing_adapter import (
    RND0069Error,
    BLSScheduleEvidence,
    authority_firewall,
    eastern_to_utc,
    expected_utc_offset_hours,
    normalize_schedule_row,
    timing_receipt,
    validate_frozen_triplet,
    validate_record,
)


def row(period='2019-01', release_date='2019-02-13', local_time='08:30', **kw):
    d = dict(
        release='Consumer Price Index',
        release_date=release_date,
        local_time=local_time,
        reference_period=period,
        provider_event_id=f'BLS-CPI-{period}',
    )
    d.update(kw)
    return d


def ev(period='2019-01', release_date='2019-02-13', local_time='08:30', **kw):
    return normalize_schedule_row(
        row(period, release_date, local_time, **kw),
        raw_hash='hash-' + period,
        source_identity='BLS 2019 historical schedule',
    )


class TestRND0069(unittest.TestCase):
    def test_01_est_to_utc(self):
        self.assertEqual(eastern_to_utc('2019-02-13','08:30'),'2019-02-13T13:30:00Z')

    def test_02_edt_to_utc(self):
        self.assertEqual(eastern_to_utc('2019-03-12','08:30'),'2019-03-12T12:30:00Z')

    def test_03_april_edt_to_utc(self):
        self.assertEqual(eastern_to_utc('2019-04-10','08:30'),'2019-04-10T12:30:00Z')

    def test_04_est_offset(self):
        self.assertEqual(expected_utc_offset_hours('2019-02-13'),-5)

    def test_05_edt_offset(self):
        self.assertEqual(expected_utc_offset_hours('2019-03-12'),-4)

    def test_06_bad_date_rejected(self):
        with self.assertRaises(RND0069Error): eastern_to_utc('2019/02/13','08:30')

    def test_07_bad_time_rejected(self):
        with self.assertRaises(RND0069Error): eastern_to_utc('2019-02-13','8:30 AM')

    def test_08_wrong_release_family_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(release='PPI'), raw_hash='x', source_identity='y')

    def test_09_wrong_local_time_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(local_time='09:00'), raw_hash='x', source_identity='y')

    def test_10_outside_period_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(period='2019-04'), raw_hash='x', source_identity='y')

    def test_11_missing_id_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(provider_event_id=''), raw_hash='x', source_identity='y')

    def test_12_missing_hash_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(), raw_hash='', source_identity='y')

    def test_13_missing_source_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(), raw_hash='x', source_identity='')

    def test_14_consensus_field_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(consensus=1.0), raw_hash='x', source_identity='y')

    def test_15_actual_field_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(actual_as_released=1.0), raw_hash='x', source_identity='y')

    def test_16_market_outcome_field_rejected(self):
        with self.assertRaises(RND0069Error): normalize_schedule_row(row(pnl=1.0), raw_hash='x', source_identity='y')

    def test_17_provider_exact(self):
        self.assertEqual(ev().provider,'BLS_HISTORICAL_SCHEDULE')

    def test_18_precision_exact(self):
        self.assertEqual(ev().timestamp_precision,'EXACT')

    def test_19_timezone_preserved(self):
        self.assertEqual(ev().timezone_name,'America/New_York')

    def test_20_triplet_passes(self):
        rows=[ev('2019-01','2019-02-13'),ev('2019-02','2019-03-12'),ev('2019-03','2019-04-10')]
        self.assertEqual(len(validate_frozen_triplet(rows)),3)

    def test_21_duplicate_event_id_rejected(self):
        a=ev('2019-01','2019-02-13')
        b=ev('2019-02','2019-03-12', provider_event_id=a.provider_event_id)
        c=ev('2019-03','2019-04-10')
        with self.assertRaises(RND0069Error): validate_frozen_triplet([a,b,c])

    def test_22_missing_record_rejected(self):
        with self.assertRaises(RND0069Error): validate_frozen_triplet([ev('2019-01','2019-02-13'),ev('2019-02','2019-03-12')])

    def test_23_receipt_remains_timing_only(self):
        rows=[ev('2019-01','2019-02-13'),ev('2019-02','2019-03-12'),ev('2019-03','2019-04-10')]
        r=timing_receipt(rows)
        self.assertFalse(r['consensus_present'])
        self.assertFalse(r['actual_present'])
        self.assertFalse(r['fx_outcomes_present'])
        self.assertFalse(r['surprise_input_eligible'])

    def test_24_authority_firewall(self):
        s=authority_firewall()
        for k,v in s.items():
            self.assertIs(v,False,k)


if __name__ == '__main__':
    unittest.main()
