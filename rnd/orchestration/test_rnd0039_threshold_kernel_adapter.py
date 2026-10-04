#!/usr/bin/env python3

import unittest

import gap_aware_m005_reconstruction as frozen
from rnd0038_r000_kernel_adapter import reconstruct_pair_2015_2020
from rnd0039_threshold_kernel_adapter import (
    EXPECTED_FROZEN_THRESHOLD,
    EXPECTED_FROZEN_YEARS,
    RND0039KernelAdapterError,
    reconstruct_pair_threshold_2015_2020,
)


def rows_2019_2020():
    # Sufficient contiguous synthetic rows for semantic/parity testing only.
    out = []
    from datetime import datetime, timedelta, timezone
    start = datetime(2019, 12, 31, 9, 0, tzinfo=timezone.utc)
    for i in range(700):
        dt = start + timedelta(minutes=5 * i)
        base = 1.1000 + (i % 80) * 0.00002
        out.append({
            "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": base - 0.00005,
            "ask_close": base + 0.00005,
            "mid_close": base,
        })
    return out


class TestRND0039ThresholdKernelAdapter(unittest.TestCase):
    def test_reference_threshold_matches_rnd0038_adapter(self):
        rows = rows_2019_2020()
        a = reconstruct_pair_2015_2020("EURUSD", rows)
        b = reconstruct_pair_threshold_2015_2020("EURUSD", rows, 0.0005)
        self.assertEqual(a, b)

    def test_treatment_threshold_is_admitted_and_frozen_globals_restored(self):
        rows = rows_2019_2020()
        original_years = frozen.AUTHORIZED_YEARS
        original_threshold = frozen.VOL_THRESHOLD
        result = reconstruct_pair_threshold_2015_2020("EURUSD", rows, 0.0006)
        self.assertEqual(result["authorized_years"], [2015, 2016, 2017, 2018, 2019, 2020])
        self.assertEqual(frozen.AUTHORIZED_YEARS, original_years)
        self.assertEqual(frozen.VOL_THRESHOLD, original_threshold)
        self.assertEqual(original_years, EXPECTED_FROZEN_YEARS)
        self.assertAlmostEqual(original_threshold, EXPECTED_FROZEN_THRESHOLD)

    def test_third_threshold_rejected(self):
        with self.assertRaises(RND0039KernelAdapterError):
            reconstruct_pair_threshold_2015_2020("EURUSD", rows_2019_2020(), 0.00055)
        with self.assertRaises(RND0039KernelAdapterError):
            reconstruct_pair_threshold_2015_2020("EURUSD", rows_2019_2020(), 0.0007)


if __name__ == "__main__":
    unittest.main()
