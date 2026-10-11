import unittest

from rnd0067_fred_alfred_outcome_blind_acquisition_pilot import (
    RND0067Error, PILOT_SERIES_ID, PILOT_SCOPE_ID,
    validate_api_key, build_metadata_url, build_initial_release_url, build_vintage_dates_url,
    redact_url, request_identity, process_metadata_payload, process_initial_release_payload,
    process_vintage_dates_payload, classify_bundle, build_bundle, bundle_receipt_dict,
    authority_firewall,
)

KEY_A = 'a' * 32
KEY_B = 'b' * 32
TS = '2026-10-11T14:00:00Z'


def metadata_payload(**kw):
    row = {
        'id': PILOT_SERIES_ID,
        'title': 'Consumer Price Index for All Urban Consumers: All Items in U.S. City Average',
        'frequency': 'Monthly',
        'units': 'Index 1982-1984=100',
        'seasonal_adjustment': 'Seasonally Adjusted',
    }
    row.update(kw)
    return {'seriess': [row]}


def observations_payload(rows=None):
    if rows is None:
        rows = [
            {'realtime_start':'2019-02-13','realtime_end':'9999-12-31','date':'2019-01-01','value':'252.561'},
            {'realtime_start':'2019-03-12','realtime_end':'9999-12-31','date':'2019-02-01','value':'253.319'},
            {'realtime_start':'2019-04-10','realtime_end':'9999-12-31','date':'2019-03-01','value':'254.202'},
        ]
    return {'observations': rows}


def vintage_payload(values=None):
    return {'vintage_dates': values or ['2019-02-13','2019-03-12','2019-04-10','2019-05-10']}


def prepared():
    mu = build_metadata_url(KEY_A)
    iu = build_initial_release_url(KEY_A)
    vu = build_vintage_dates_url(KEY_A)
    meta, r1 = process_metadata_payload(metadata_payload(), request_url=mu, acquisition_timestamp_utc=TS)
    initial, r2 = process_initial_release_payload(observations_payload(), metadata=meta, request_url=iu, acquisition_timestamp_utc=TS)
    vintages, r3 = process_vintage_dates_payload(vintage_payload(), request_url=vu, acquisition_timestamp_utc=TS)
    return meta, initial, vintages, [r1,r2,r3]


class TestRND0067(unittest.TestCase):
    def test_01_api_key_required(self):
        with self.assertRaises(RND0067Error): validate_api_key('')

    def test_02_api_key_format_frozen(self):
        with self.assertRaises(RND0067Error): validate_api_key('ABC' + 'a'*29)
        self.assertEqual(validate_api_key(KEY_A), KEY_A)

    def test_03_scope_frozen_to_cpi_series(self):
        u = build_initial_release_url(KEY_A)
        self.assertIn('series_id=CPIAUCSL', u)
        self.assertIn('observation_start=2019-01-01', u)
        self.assertIn('observation_end=2019-03-01', u)

    def test_04_initial_release_output_type_frozen(self):
        self.assertIn('output_type=4', build_initial_release_url(KEY_A))

    def test_05_vintage_window_frozen(self):
        u = build_vintage_dates_url(KEY_A)
        self.assertIn('realtime_start=2019-01-01', u)
        self.assertIn('realtime_end=2019-12-31', u)

    def test_06_url_redacts_key(self):
        r = redact_url(build_metadata_url(KEY_A))
        self.assertNotIn(KEY_A, r)
        self.assertIn('api_key=REDACTED', r)

    def test_07_request_identity_key_independent(self):
        self.assertEqual(request_identity(build_metadata_url(KEY_A)), request_identity(build_metadata_url(KEY_B)))

    def test_08_endpoint_request_identities_distinct(self):
        ids = {
            request_identity(build_metadata_url(KEY_A)),
            request_identity(build_initial_release_url(KEY_A)),
            request_identity(build_vintage_dates_url(KEY_A)),
        }
        self.assertEqual(len(ids), 3)

    def test_09_metadata_series_mismatch_rejected(self):
        with self.assertRaises(RND0067Error):
            process_metadata_payload(metadata_payload(id='OTHER'), request_url=build_metadata_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_10_metadata_required_fields_enforced(self):
        with self.assertRaises(RND0067Error):
            process_metadata_payload(metadata_payload(units=''), request_url=build_metadata_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_11_metadata_market_outcome_contamination_rejected(self):
        p = metadata_payload(); p['seriess'][0]['pnl'] = 1.0
        with self.assertRaises(RND0067Error):
            process_metadata_payload(p, request_url=build_metadata_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_12_initial_records_are_marked_initial_release(self):
        meta, _, _, _ = prepared()
        rows, _ = process_initial_release_payload(observations_payload(), metadata=meta, request_url=build_initial_release_url(KEY_A), acquisition_timestamp_utc=TS)
        self.assertTrue(rows)
        self.assertTrue(all(r.initial_release for r in rows))

    def test_13_initial_record_identity_and_reference_period(self):
        _, rows, _, _ = prepared()
        self.assertEqual(rows[0].series_id, PILOT_SERIES_ID)
        self.assertEqual(rows[0].reference_period, '2019-01')
        self.assertEqual(rows[0].vintage_date, '2019-02-13')

    def test_14_missing_initial_value_rejected(self):
        meta, _, _, _ = prepared()
        p = observations_payload([{'realtime_start':'2019-02-13','date':'2019-01-01','value':'.'}])
        with self.assertRaises(RND0067Error):
            process_initial_release_payload(p, metadata=meta, request_url=build_initial_release_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_15_out_of_scope_observation_rejected(self):
        meta, _, _, _ = prepared()
        p = observations_payload([{'realtime_start':'2019-05-10','date':'2019-04-01','value':'255.0'}])
        with self.assertRaises(RND0067Error):
            process_initial_release_payload(p, metadata=meta, request_url=build_initial_release_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_16_observation_payload_market_outcome_rejected(self):
        meta, _, _, _ = prepared()
        p = observations_payload(); p['fx_return'] = 0.1
        with self.assertRaises(RND0067Error):
            process_initial_release_payload(p, metadata=meta, request_url=build_initial_release_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_17_vintage_dates_must_be_ascending(self):
        with self.assertRaises(RND0067Error):
            process_vintage_dates_payload(vintage_payload(['2019-03-12','2019-02-13']), request_url=build_vintage_dates_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_18_duplicate_vintage_dates_rejected(self):
        with self.assertRaises(RND0067Error):
            process_vintage_dates_payload(vintage_payload(['2019-02-13','2019-02-13']), request_url=build_vintage_dates_url(KEY_A), acquisition_timestamp_utc=TS)

    def test_19_receipts_never_contain_api_key(self):
        _, _, _, receipts = prepared()
        for r in receipts:
            self.assertNotIn(KEY_A, r.request_url_redacted)
            self.assertEqual(r.pilot_scope_id, PILOT_SCOPE_ID)

    def test_20_raw_hash_deterministic(self):
        meta, _, _, _ = prepared()
        p = observations_payload()
        _, a = process_initial_release_payload(p, metadata=meta, request_url=build_initial_release_url(KEY_A), acquisition_timestamp_utc=TS)
        _, b = process_initial_release_payload(p, metadata=meta, request_url=build_initial_release_url(KEY_B), acquisition_timestamp_utc=TS)
        self.assertEqual(a.raw_sha256, b.raw_sha256)
        self.assertEqual(a.request_identity, b.request_identity)

    def test_21_structural_feasibility_classification(self):
        meta, initial, vintages, _ = prepared()
        self.assertEqual(classify_bundle(meta, initial, vintages), 'PILOT_STRUCTURAL_FEASIBILITY_CONFIRMED')

    def test_22_no_initial_rows_is_inconclusive(self):
        meta, _, vintages, _ = prepared()
        self.assertEqual(classify_bundle(meta, [], vintages), 'PILOT_INCONCLUSIVE_NO_INITIAL_RELEASE_ROWS')

    def test_23_bundle_requires_all_three_endpoint_receipts(self):
        meta, initial, vintages, receipts = prepared()
        with self.assertRaises(RND0067Error): build_bundle(meta, initial, vintages, receipts[:2])

    def test_24_bundle_receipt_keeps_all_authorities_false(self):
        meta, initial, vintages, receipts = prepared()
        bundle = build_bundle(meta, initial, vintages, receipts)
        out = bundle_receipt_dict(bundle)
        self.assertFalse(out['fred_exact_intraday_timing_authority'])
        self.assertFalse(out['fred_market_consensus_authority'])
        for v in authority_firewall().values():
            self.assertIs(v, False)


if __name__ == '__main__':
    unittest.main()
