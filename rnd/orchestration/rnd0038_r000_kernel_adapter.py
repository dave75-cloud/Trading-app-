#!/usr/bin/env python3
"""RND-0038 adapter for the frozen RND-0034 R000 reconstruction kernel.

The frozen kernel intentionally hard-gates strategy evaluation to 2015-2019.
RND-0038 has separately authorized R000 over the complete DEVELOPMENT interval
through the truncated 2020 endpoint. This adapter changes only the in-memory
authorized-year guard for the duration of one pure-local call and restores the
frozen value in a finally block. No source file is modified.
"""

from __future__ import annotations

import gap_aware_m005_reconstruction as frozen

RND0038_AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
EXPECTED_FROZEN_YEARS = frozenset({2015, 2016, 2017, 2018, 2019})


class RND0038KernelAdapterError(ValueError):
    pass


def reconstruct_pair_2015_2020(symbol, rows):
    original = frozen.AUTHORIZED_YEARS
    if original != EXPECTED_FROZEN_YEARS:
        raise RND0038KernelAdapterError("frozen RND-0034 authorized-year guard drift")
    frozen.AUTHORIZED_YEARS = RND0038_AUTHORIZED_YEARS
    try:
        result = frozen.reconstruct_pair(symbol, rows)
    finally:
        frozen.AUTHORIZED_YEARS = original
    if result.get("authorized_years") != sorted(RND0038_AUTHORIZED_YEARS):
        raise RND0038KernelAdapterError("RND-0038 authorized-year output mismatch")
    return result
