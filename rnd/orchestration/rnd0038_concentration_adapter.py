#!/usr/bin/env python3
"""RND-0038 adapter for frozen RND-0035 concentration diagnostics.

The RND-0035 module is frozen to development years 2015-2019. RND-0038 adds
only the newly governed 2020 development year. This adapter temporarily widens
the module-level year guard, calls the unchanged diagnostic implementation,
and restores the frozen guard even if evaluation fails.
"""

from __future__ import annotations

from contextlib import contextmanager

import rnd0035_concentration_diagnostics as frozen

RND0038_YEARS = (2015, 2016, 2017, 2018, 2019, 2020)
FROZEN_YEARS = (2015, 2016, 2017, 2018, 2019)


class RND0038ConcentrationAdapterError(ValueError):
    pass


@contextmanager
def _full_development_year_guard():
    original = frozen.YEARS
    if tuple(original) != FROZEN_YEARS:
        raise RND0038ConcentrationAdapterError("frozen RND-0035 year guard drifted")
    frozen.YEARS = RND0038_YEARS
    try:
        yield
    finally:
        frozen.YEARS = original


def concentration_diagnostics_2015_2020(trades):
    with _full_development_year_guard():
        result = frozen.concentration_diagnostics(trades)
    if tuple(frozen.YEARS) != FROZEN_YEARS:
        raise RND0038ConcentrationAdapterError("frozen year guard was not restored")
    if set(result.get("year", {})) != {str(y) for y in RND0038_YEARS}:
        raise RND0038ConcentrationAdapterError("full-development year diagnostics incomplete")
    result = dict(result)
    result["adapter_contract_version"] = "RND0038-concentration-adapter-v1"
    result["authorized_development_years"] = list(RND0038_YEARS)
    result["frozen_rnd0035_module_modified"] = False
    result["strategy_selection_authority"] = False
    return result
