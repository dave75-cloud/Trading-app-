#!/usr/bin/env python3

import unittest
from datetime import datetime, timedelta, timezone

import gap_aware_m005_reconstruction as frozen
from rnd0038_r000_kernel_adapter import (
    EXPECTED_FROZEN_YEARS,
    RND0038_AUTHORIZED_YEARS,
    reconstruct_pair_2015_2020,
)


def rows(start, count=80):
    out = []
    dt = start
    for i in range(count):
        mid = 1.0 + i * 0.00001
        out.append({
            "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": mid - 0.00005,
            "ask_close": mid + 0.00005,
            "mid_close": mid,
        })
        dt += timedelta(minutes=5)
    return out


class TestRND0038R000KernelAdapter(unittest.TestCase):
    def test_2019_semantics_match_frozen_kernel_except_authorized_year_label(self):
        sample = rows(datetime(2019, 6, 3, 11, 0, tzinfo=timezone.utc))
        baseline = frozen.reconstruct_pair("EURUSD", sample)
        adapted = reconstruct_pair_2015_2020("EURUSD", sample)
        self.assertEqual(frozen.AUTHORIZED_YEARS, EXPECTED_FROZEN_YEARS)
        baseline = dict(baseline)
        adapted = dict(adapted)
        baseline.pop("authorized_years")
        adapted.pop("authorized_years")
        self.assertEqual(baseline, adapted)

    def test_2020_is_accepted_only_through_adapter(self):
        sample = rows(datetime(2020, 6, 1, 11, 0, tzinfo=timezone.utc))
        with self.assertRaises(frozen.GapAwareM005Error):
            frozen.reconstruct_pair("EURUSD", sample)
        adapted = reconstruct_pair_2015_2020("EURUSD", sample)
        self.assertEqual(adapted["authorized_years"], sorted(RND0038_AUTHORIZED_YEARS))
        self.assertEqual(frozen.AUTHORIZED_YEARS, EXPECTED_FROZEN_YEARS)

    def test_guard_restores_after_failure(self):
        with self.assertRaises(Exception):
            reconstruct_pair_2015_2020("BAD", rows(datetime(2020, 6, 1, 11, 0, tzinfo=timezone.utc)))
        self.assertEqual(frozen.AUTHORIZED_YEARS, EXPECTED_FROZEN_YEARS)


if __name__ == "__main__":
    unittest.main()
