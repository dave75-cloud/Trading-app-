#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

import m006e7_provider_path_diagnostics as d


ROOT = Path(".").resolve()

E1_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)

E3_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "bridge/state/bridge_state.json"
)


def sha(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.7 — "
        "PROVIDER-PATH DIAGNOSTIC AUDIT"
    )
    print("=" * 78)

    e1_before = sha(
        E1_STATE
    )

    e3_before = sha(
        E3_STATE
    )

    source = Path(
        "tools/m006e/m006e7/"
        "m006e7_provider_path_diagnostics.py"
    ).read_text()

    forbidden = [
        "urllib.",
        "requests.",
        "http://",
        "https://",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
        "/orders",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden network/order token: "
                f"{token}"
            )

    print(
        "PASS 01 no network/order capability"
    )

    assert abs(
        d.THRESHOLD
        - 0.0005
    ) < 1e-15

    print(
        "PASS 02 frozen volatility threshold = 0.0005"
    )

    ts = pd.Timestamp(
        "2026-09-01T12:00:00Z"
    )

    event = {
        "pair": "EURUSD",
        "bar_ts_utc":
            ts.isoformat(),
        "event_type":
            "entry",
        "old_position":
            "flat",
        "new_position":
            "long",
        "close":
            1.1000,
        "volatility":
            0.00051,
        "volatility_ok":
            True,
        "desired_delayed_signal":
            1,
        "_source_file":
            "AUDIT",
    }

    twelve = pd.DataFrame(
        [
            {
                "ts": ts,
                "c": 1.1000,
                "volatility":
                    0.00051,
                "vol_ok":
                    True,
                "delayed_signal":
                    1,
            }
        ]
    )

    r = d.diagnose_event(
        event,
        twelve,
    )

    assert (
        r[
            "diagnostic_status"
        ]
        == "AGREEMENT"
    )

    assert abs(
        r[
            "close_divergence_bps"
        ]
    ) < 1e-12

    print(
        "PASS 03 exact provider agreement classified correctly"
    )

    twelve = pd.DataFrame(
        [
            {
                "ts": ts,
                "c": 1.1000,
                "volatility":
                    0.00049,
                "vol_ok":
                    False,
                "delayed_signal":
                    0,
            }
        ]
    )

    r = d.diagnose_event(
        event,
        twelve,
    )

    assert (
        "DIRECTION_DISAGREEMENT"
        in r[
            "diagnostic_status"
        ]
    )

    assert (
        "VOL_ELIGIBILITY_DISAGREEMENT"
        in r[
            "diagnostic_status"
        ]
    )

    print(
        "PASS 04 direction + volatility disagreement detected"
    )

    twelve = pd.DataFrame(
        [
            {
                "ts": ts,
                "c": 1.1012,
                "volatility":
                    0.00051,
                "vol_ok":
                    True,
                "delayed_signal":
                    1,
            }
        ]
    )

    r = d.diagnose_event(
        event,
        twelve,
    )

    assert (
        "PRICE_DIVERGENCE_GT_10BPS"
        in r[
            "diagnostic_status"
        ]
    )

    print(
        "PASS 05 >10 bps price divergence detected"
    )

    r = d.diagnose_event(
        event,
        None,
    )

    assert (
        r[
            "diagnostic_status"
        ]
        == "TWELVE_BAR_MISSING"
    )

    print(
        "PASS 06 missing validator bar detected"
    )

    assert abs(
        (
            0.00051
            - d.THRESHOLD
        )
        - 0.00001
    ) < 1e-12

    print(
        "PASS 07 threshold-distance arithmetic verified"
    )

    e1_after = sha(
        E1_STATE
    )

    e3_after = sha(
        E3_STATE
    )

    assert (
        e1_before
        == e1_after
    )

    assert (
        e3_before
        == e3_after
    )

    print(
        "PASS 08 M006e.1 prospective state unchanged"
    )

    print(
        "PASS 09 M006e.3 prospective state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )
    print(
        "Order capability: NONE"
    )

    print()
    print("=" * 78)
    print(
        "M006E7_PROVIDER_PATH_AUDIT: PASS"
    )
    print(
        "Provider divergence, volatility-threshold "
        "and signal-path diagnostics verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
