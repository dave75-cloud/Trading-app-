import unittest

from rnd0072_te_point_in_time_consensus_offline_adapter import (
    RND0072Error, TEConsensusCandidate, RequestBudget, admit_candidate,
    reject_teforecast_fallback, validate_no_market_outcomes,
    validate_secret_free, canonical_raw_hash, authority_firewall,
)


def candidate(**kw):
    d = dict(
        calendar_id='TE-CPI-2019-02-13',
        country='United States',
        category='Consumer Price Index CPI',
        event='CPI',
        reference_period='2019-01',
        event_timestamp_utc='2019-02-13T13:30:00Z',
        date_span=0,
        forecast='252.5',
        te_forecast='252.6',
        point_in_time_snapshot_utc='2019-02-13T13:00:00Z',
        raw_hash='abc123',
        source_identity='TRADING_ECONOMICS_POINT_IN_TIME',
    )
    d.update(kw)
    return TEConsensusCandidate(**d)


class TestRND0072(unittest.TestCase):
    def test_01_happy_path_admits_forecast(self):
        out = admit_candidate(candidate(), expected_release_utc='2019-02-13T13:30:00Z')
        self.assertEqual(out['consensus_evidence']['consensus'], 252.5)
        self.assertEqual(out['eligibility_state'], 'CONSENSUS_INPUT_STRUCTURALLY_ADMISSIBLE')

    def test_02_teforecast_is_auxiliary_only(self):
        out = admit_candidate(candidate(), expected_release_utc='2019-02-13T13:30:00Z')
        self.assertEqual(out['te_forecast_auxiliary'], 252.6)
        self.assertFalse(out['te_forecast_admissible_as_consensus'])

    def test_03_missing_forecast_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(forecast=''), expected_release_utc='2019-02-13T13:30:00Z')

    def test_04_teforecast_cannot_fallback(self):
        with self.assertRaises(RND0072Error):
            reject_teforecast_fallback(candidate(forecast='', te_forecast='252.7'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_05_late_snapshot_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(point_in_time_snapshot_utc='2019-02-13T13:30:00Z'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_06_after_release_snapshot_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(point_in_time_snapshot_utc='2019-02-13T13:31:00Z'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_07_estimated_time_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(date_span=1), expected_release_utc='2019-02-13T13:30:00Z')

    def test_08_bls_time_mismatch_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(event_timestamp_utc='2019-02-13T13:31:00Z'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_09_country_mismatch_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(country='Canada'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_10_reference_period_outside_scope_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(reference_period='2019-04'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_11_non_cpi_event_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(category='Retail Sales', event='Retail Sales'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_12_missing_calendar_id_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(calendar_id=''), expected_release_utc='2019-02-13T13:30:00Z')

    def test_13_missing_raw_hash_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(raw_hash=''), expected_release_utc='2019-02-13T13:30:00Z')

    def test_14_missing_source_identity_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(source_identity=''), expected_release_utc='2019-02-13T13:30:00Z')

    def test_15_secret_bearing_source_identity_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(source_identity='https://x.test?c=SECRET'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_16_numeric_suffix_k_parses(self):
        out = admit_candidate(candidate(forecast='252K'), expected_release_utc='2019-02-13T13:30:00Z')
        self.assertEqual(out['consensus_evidence']['consensus'], 252000.0)

    def test_17_unparseable_forecast_rejected(self):
        with self.assertRaises(RND0072Error):
            admit_candidate(candidate(forecast='not-a-number'), expected_release_utc='2019-02-13T13:30:00Z')

    def test_18_market_outcome_payload_rejected(self):
        with self.assertRaises(RND0072Error):
            validate_no_market_outcomes({'nested': {'pnl': 1.0}})

    def test_19_clean_payload_hashes(self):
        h = canonical_raw_hash({'Forecast': '252.5', 'DateSpan': 0})
        self.assertEqual(len(h), 64)

    def test_20_request_budget_counts_to_ten(self):
        b = RequestBudget()
        for i in range(10):
            self.assertEqual(b.consume(), i + 1)
        self.assertEqual(b.used, 10)

    def test_21_request_eleven_rejected(self):
        b = RequestBudget()
        for _ in range(10):
            b.consume()
        with self.assertRaises(RND0072Error):
            b.consume()

    def test_22_nonfrozen_cap_rejected(self):
        b = RequestBudget(cap=9)
        with self.assertRaises(RND0072Error):
            b.consume()

    def test_23_secret_free_text_guard(self):
        self.assertEqual(validate_secret_free('REDACTED_REQUEST'), 'REDACTED_REQUEST')
        with self.assertRaises(RND0072Error):
            validate_secret_free('https://api.test/path?api_key=secret')

    def test_24_authority_firewall(self):
        s = authority_firewall()
        for key in (
            'provider_access_authority','provider_purchase_authority','strategy_outcome_open',
            'validation_open','reserved_final_open','prospective_outcomes_open',
            'promotion_authority','broker_write_authority','capital_authority',
            'live_execution_authority','automatic_merge'):
            self.assertIs(s[key], False)


if __name__ == '__main__':
    unittest.main()
