import unittest

from rnd0065_trading_economics_provider_pilot import (
    RND0065Error, build_request_url, redact_url, request_identity,
    normalize_te_row, process_payload, authority_firewall,
)


def row(**kw):
    d=dict(
        CalendarId='1001', Date='2019-01-10T13:30:00', Country='United States',
        Category='CPI', Event='CPI YoY', Reference='Dec', Source='BLS',
        SourceURL='https://bls.gov', Actual='1.9%', Previous='2.2%', Forecast='1.9%',
        TEForecast='2.0%', DateSpan='0', Importance=3,
        LastUpdate='2019-01-10T13:30:01', Revised='', Currency='USD', Unit='%',
        Ticker='USCPIYY', Symbol='USCPIYY'
    )
    d.update(kw)
    return d

class TestRND0065(unittest.TestCase):
    def test_01_requires_explicit_key(self):
        with self.assertRaises(RND0065Error): build_request_url('')

    def test_02_guest_key_rejected(self):
        with self.assertRaises(RND0065Error): build_request_url('guest:guest')

    def test_03_request_scope_frozen(self):
        u=build_request_url('abc123')
        self.assertIn('2019-01-01/2019-04-01',u)
        for name in ('United%20States','Australia','United%20Kingdom','Euro%20Area','Japan'):
            self.assertIn(name,u)

    def test_04_url_redacts_key(self):
        u=build_request_url('secret-key')
        r=redact_url(u)
        self.assertNotIn('secret-key',r); self.assertIn('c=REDACTED',r)

    def test_05_request_identity_key_independent(self):
        self.assertEqual(request_identity(build_request_url('a')),request_identity(build_request_url('b')))

    def test_06_exact_datespan_eligible(self):
        out=normalize_te_row(row(),raw_hash='h',seen_ids=set())
        self.assertTrue(out['exact_time_eligible'])

    def test_07_estimated_datespan_not_exact(self):
        out=normalize_te_row(row(DateSpan='1'),raw_hash='h',seen_ids=set())
        self.assertFalse(out['exact_time_eligible'])

    def test_08_out_of_scope_country_rejected(self):
        with self.assertRaises(RND0065Error): normalize_te_row(row(Country='Canada'),raw_hash='h',seen_ids=set())

    def test_09_out_of_window_date_rejected(self):
        with self.assertRaises(RND0065Error): normalize_te_row(row(Date='2019-04-01T00:00:00'),raw_hash='h',seen_ids=set())

    def test_10_missing_event_id_rejected(self):
        with self.assertRaises(RND0065Error): normalize_te_row(row(CalendarId=''),raw_hash='h',seen_ids=set())

    def test_11_missing_source_rejected(self):
        with self.assertRaises(RND0065Error): normalize_te_row(row(Source='',SourceURL=''),raw_hash='h',seen_ids=set())

    def test_12_duplicate_identity_rejected(self):
        seen=set(); normalize_te_row(row(),raw_hash='h',seen_ids=seen)
        with self.assertRaises(Exception): normalize_te_row(row(),raw_hash='h',seen_ids=seen)

    def test_13_numeric_suffix_k_parsed(self):
        out=normalize_te_row(row(Actual='200K',Forecast='198K',Previous='190K'),raw_hash='h',seen_ids=set())
        self.assertEqual(out['actual_as_released'],200000.0); self.assertEqual(out['consensus'],198000.0)

    def test_14_percentage_parsed(self):
        out=normalize_te_row(row(Actual='1.9%',Forecast='2.0%'),raw_hash='h',seen_ids=set())
        self.assertEqual(out['actual_as_released'],1.9); self.assertEqual(out['consensus'],2.0)

    def test_15_missing_consensus_allowed_but_flagged(self):
        out=normalize_te_row(row(Forecast=''),raw_hash='h',seen_ids=set())
        self.assertFalse(out['consensus_available']); self.assertFalse(out['surprise_eligible_inputs_present'])

    def test_16_missing_actual_allowed_but_flagged(self):
        out=normalize_te_row(row(Actual=''),raw_hash='h',seen_ids=set())
        self.assertFalse(out['actual_available']); self.assertFalse(out['surprise_eligible_inputs_present'])

    def test_17_revision_preserved_separately(self):
        out=normalize_te_row(row(Actual='5',Previous='4',Revised='3.5'),raw_hash='h',seen_ids=set())
        self.assertEqual(out['actual_as_released'],5.0); self.assertEqual(out['previous'],4.0); self.assertEqual(out['revised_previous'],3.5)

    def test_18_market_outcome_field_rejected(self):
        bad=row(); bad['pnl']=1.2
        with self.assertRaises(RND0065Error): normalize_te_row(bad,raw_hash='h',seen_ids=set())

    def test_19_payload_nonlist_rejected(self):
        with self.assertRaises(RND0065Error): process_payload({},request_url=build_request_url('x'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')

    def test_20_payload_receipt_counts(self):
        p=[row(CalendarId='1'),row(CalendarId='2',Forecast='')]
        n,rec,rej=process_payload(p,request_url=build_request_url('x'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')
        self.assertEqual(rec.raw_record_count,2); self.assertEqual(rec.normalized_record_count,2); self.assertEqual(rec.rejected_record_count,0); self.assertEqual(len(rej),0)

    def test_21_invalid_row_is_rejected_not_silently_counted(self):
        p=[row(CalendarId='1'),row(CalendarId='2',Country='Canada')]
        n,rec,rej=process_payload(p,request_url=build_request_url('x'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')
        self.assertEqual(len(n),1); self.assertEqual(rec.rejected_record_count,1); self.assertEqual(len(rej),1)

    def test_22_raw_hash_deterministic(self):
        p=[row(CalendarId='1')]
        _,a,_=process_payload(p,request_url=build_request_url('x'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')
        _,b,_=process_payload(p,request_url=build_request_url('y'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')
        self.assertEqual(a.raw_sha256,b.raw_sha256); self.assertEqual(a.request_identity,b.request_identity)

    def test_23_receipt_never_contains_key(self):
        _,rec,_=process_payload([row()],request_url=build_request_url('supersecret'),acquisition_timestamp_utc='2026-10-11T12:00:00Z')
        self.assertNotIn('supersecret',rec.request_url_redacted); self.assertIn('REDACTED',rec.request_url_redacted)

    def test_24_authority_firewall_all_false(self):
        for v in authority_firewall().values(): self.assertIs(v,False)

if __name__=='__main__': unittest.main()
