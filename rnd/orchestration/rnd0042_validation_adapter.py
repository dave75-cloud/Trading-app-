#!/usr/bin/env python3
from __future__ import annotations

import gap_aware_m005_reconstruction as frozen

EXPECTED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019})
VALIDATION_YEARS = frozenset({2020, 2021, 2022})
EXPECTED_THRESHOLD = 0.0005
CANDIDATE_THRESHOLD = 0.0006

class RND0042AdapterError(ValueError):
    pass

def reconstruct_validation_candidate(symbol, rows):
    oy = frozen.AUTHORIZED_YEARS
    ot = frozen.VOL_THRESHOLD
    if oy != EXPECTED_YEARS:
        raise RND0042AdapterError("frozen authorized-year guard drift")
    if abs(float(ot) - EXPECTED_THRESHOLD) > 1e-15:
        raise RND0042AdapterError("frozen threshold drift")
    frozen.AUTHORIZED_YEARS = VALIDATION_YEARS
    frozen.VOL_THRESHOLD = CANDIDATE_THRESHOLD
    try:
        result = frozen.reconstruct_pair(symbol, rows)
    finally:
        frozen.AUTHORIZED_YEARS = oy
        frozen.VOL_THRESHOLD = ot
    if result.get("authorized_years") != sorted(VALIDATION_YEARS):
        raise RND0042AdapterError("validation year output mismatch")
    return result
