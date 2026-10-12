import unittest
from dataclasses import replace

from rnd0066_fred_alfred_macro_provenance_backbone import ConsensusEvidence, FredVintageEvidence
from rnd0069_bls_historical_timing_adapter import BLSScheduleEvidence
from rnd0073_canonical_macro_composition_rehearsal import (
    RND0073Error,
    authority_firewall,
    rehearse_composition,
    timing_from_bls,
    validate_no_market_outcomes,
    validate_triplet_alignment,
)


PERIODS = ('2019-01', '2019-02', '2019-03')
RELEASES = (
    ('2019-02-13', '2019-02-13T13:30:00Z'),
    ('2019-03-12', '2019-03-12T12:30:00Z'),
    ('2019-04-10', '2019-04-10T12:30:00Z'),
)


def actuals():
    out = []
    for i, p in enumerate(PERIODS, 1):
        out.append(FredVintageEvidence(
            series_id='CPIAUCSL', link_key='US_CPI_HEADLINE', observation_date=f'2019-{i:02d}-01',
            vintage_date=RELEASES[i-1][0], value=250.0+i, unit='Index 1982-1984=100',
            reference_period=p, economy='United States', currency='USD', raw_hash=f'a{i}'*32,
            source_identity=f'FRED:CPIAUCSL:{p}', initial_release=True,
        ))
    return out


def timings():
    out = []
    for i, (p, (release_date, utc)) in enumerate(zip(PERIODS, RELEASES), 1):
        out.append(BLSScheduleEvidence(
            provider='BLS_HISTORICAL_SCHEDULE', provider_event_id=f'BLS-CPI-{p}',
            link_key='US_CPI_HEADLINE', event_series='Consumer Price Index', economy='United States',
            currency='USD', reference_period=p, release_date=release_date, local_time='08:30',
            timezone_name='America/New_York', scheduled_timestamp_utc=utc, timestamp_precision='EXACT',
            source_identity=f'BLS:SCHEDULE:{p}', raw_hash=f'b{i}'*32,
        ))
    return out


def consensuses():
    out = []
    for i, (p, (_, utc)) in enumerate(zip(PERIODS, RELEASES), 1):
        day = int(utc[8:10]) - 1
        captured = utc[:8] + f'{day:02d}' + 'T18:00:00Z'
        out.append(ConsensusEvidence(
            provider='SYNTHETIC_CONSENSUS_FIXTURE', provider_event_id=f'SYN-{p}', link_key='US_CPI_HEADLINE',
            economy='United States', currency='USD', reference_period=p, consensus=251.0+i,
            captured_at_utc=captured, semantic='MARKET_CONSENSUS', historical_point_in_time=True,
            raw_hash=f'c{i}'*32, source_identity=f'SYNTHETIC:{p}',
        ))
    return out


class TestRND0073(unittest.TestCase):
    def test_01_happy_path_classification(self):
        self.assertEqual(rehearse_composition(actuals(), timings(), consensuses())['receipt']['classification'], 'CANONICAL_COMPOSITION_REHEARSAL_CONFIRMED')

    def test_02_three_records(self):
        self.assertEqual(rehearse_composition(actuals(), timings(), consensuses())['receipt']['record_count'], 3)

    def test_03_periods_preserved(self):
        self.assertEqual(rehearse_composition(actuals(), timings(), consensuses())['receipt']['reference_periods'], list(PERIODS))

    def test_04_canonical_schema(self):
        self.assertEqual(rehearse_composition(actuals(), timings(), consensuses())['receipt']['canonical_schema'], 'RND0064')

    def test_05_no_live_consensus(self):
        self.assertFalse(rehearse_composition(actuals(), timings(), consensuses())['receipt']['live_consensus_used'])

    def test_06_no_spend(self):
        self.assertFalse(rehearse_composition(actuals(), timings(), consensuses())['receipt']['provider_spend_incurred'])

    def test_07_no_fx_outcomes(self):
        self.assertFalse(rehearse_composition(actuals(), timings(), consensuses())['receipt']['fx_outcomes_present'])

    def test_08_authorities_false(self):
        self.assertTrue(all(v is False for v in authority_firewall().values()))

    def test_09_timing_conversion_wrapper(self):
        self.assertEqual(timing_from_bls(timings()[0]).scheduled_timestamp, '2019-02-13T13:30:00Z')

    def test_10_wrong_actual_count_rejected(self):
        with self.assertRaises(RND0073Error): validate_triplet_alignment(actuals()[:2], timings(), consensuses())

    def test_11_wrong_consensus_count_rejected(self):
        with self.assertRaises(RND0073Error): validate_triplet_alignment(actuals(), timings(), consensuses()[:2])

    def test_12_actual_order_rejected(self):
        a = actuals(); a[0], a[1] = a[1], a[0]
        with self.assertRaises(RND0073Error): validate_triplet_alignment(a, timings(), consensuses())

    def test_13_consensus_order_rejected(self):
        c = consensuses(); c[0], c[1] = c[1], c[0]
        with self.assertRaises(RND0073Error): validate_triplet_alignment(actuals(), timings(), c)

    def test_14_non_synthetic_consensus_rejected(self):
        c = consensuses(); c[0] = replace(c[0], provider='TRADING_ECONOMICS')
        with self.assertRaises(RND0073Error): rehearse_composition(actuals(), timings(), c)

    def test_15_post_release_consensus_rejected(self):
        c = consensuses(); c[0] = replace(c[0], captured_at_utc='2019-02-13T13:30:00Z')
        with self.assertRaises(Exception): rehearse_composition(actuals(), timings(), c)

    def test_16_link_key_mismatch_rejected(self):
        c = consensuses(); c[0] = replace(c[0], link_key='OTHER')
        with self.assertRaises(Exception): rehearse_composition(actuals(), timings(), c)

    def test_17_economy_mismatch_rejected(self):
        c = consensuses(); c[0] = replace(c[0], economy='Australia')
        with self.assertRaises(Exception): rehearse_composition(actuals(), timings(), c)

    def test_18_currency_mismatch_rejected(self):
        c = consensuses(); c[0] = replace(c[0], currency='AUD')
        with self.assertRaises(Exception): rehearse_composition(actuals(), timings(), c)

    def test_19_reference_period_mismatch_rejected(self):
        c = consensuses(); c[0] = replace(c[0], reference_period='2018-12')
        with self.assertRaises(RND0073Error): rehearse_composition(actuals(), timings(), c)

    def test_20_non_initial_actual_rejected(self):
        a = actuals(); a[0] = replace(a[0], initial_release=False)
        with self.assertRaises(Exception): rehearse_composition(a, timings(), consensuses())

    def test_21_market_field_rejected(self):
        with self.assertRaises(RND0073Error): validate_no_market_outcomes({'pnl': 1.0})

    def test_22_nested_market_field_rejected(self):
        with self.assertRaises(RND0073Error): validate_no_market_outcomes({'x': [{'strategy_signal': 1}]})

    def test_23_events_are_surprise_eligible_inputs_only(self):
        result = rehearse_composition(actuals(), timings(), consensuses())
        self.assertTrue(all(e['surprise_eligible_inputs_present'] for e in result['events']))

    def test_24_bundle_hash_stable(self):
        r1 = rehearse_composition(actuals(), timings(), consensuses())['receipt']['bundle_sha256']
        r2 = rehearse_composition(actuals(), timings(), consensuses())['receipt']['bundle_sha256']
        self.assertEqual(r1, r2)


if __name__ == '__main__':
    unittest.main()
