#!/usr/bin/env python3
"""RND-0039 adapter for the frozen RND-0034 M005 reconstruction kernel.

RND-0039 is a two-point development-only falsification study. This adapter
changes only the in-memory authorized-year guard and volatility threshold for
one pure-local reconstruction call, then restores both frozen globals in a
finally block. The frozen source file is never modified.
"""

from __future__ import annotations

import math
import gap_aware_m005_reconstruction as frozen

RND0039_AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
EXPECTED_FROZEN_YEARS = frozenset({2015, 2016, 2017, 2018, 2019})
EXPECTED_FROZEN_THRESHOLD = 0.0005
AUTHORIZED_THRESHOLDS = (0.0005, 0.0006)


class RND0039KernelAdapterError(ValueError):
    pass


def reconstruct_pair_threshold_2015_2020(symbol, rows, threshold):
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise RND0039KernelAdapterError("numeric threshold required")
    threshold = float(threshold)
    if not math.isfinite(threshold) or threshold not in AUTHORIZED_THRESHOLDS:
        raise RND0039KernelAdapterError("threshold outside predeclared RND-0039 set")

    original_years = frozen.AUTHORIZED_YEARS
    original_threshold = frozen.VOL_THRESHOLD
    if original_years != EXPECTED_FROZEN_YEARS:
        raise RND0039KernelAdapterError("frozen RND-0034 authorized-year guard drift")
    if abs(float(original_threshold) - EXPECTED_FROZEN_THRESHOLD) > 1e-15:
        raise RND0039KernelAdapterError("frozen RND-0034 volatility threshold drift")

    frozen.AUTHORIZED_YEARS = RND0039_AUTHORIZED_YEARS
    frozen.VOL_THRESHOLD = threshold
    try:
        result = frozen.reconstruct_pair(symbol, rows)
    finally:
        frozen.AUTHORIZED_YEARS = original_years
        frozen.VOL_THRESHOLD = original_threshold

    if result.get("authorized_years") != sorted(RND0039_AUTHORIZED_YEARS):
        raise RND0039KernelAdapterError("RND-0039 authorized-year output mismatch")
    return result
