#!/usr/bin/env python3
"""
KQTRL M006e.3 — OANDA-authoritative integrated ZERO-WRITE dry-run bridge.

Pipeline:
    M006e.1 OANDA authoritative event
        -> M006e.2 Twelve validator
        -> M006d.1 execution policy
        -> fresh OANDA practice pricing
        -> M006d.2 Conservative-B sizing equivalent
        -> SUPPRESSED_DRY_RUN proposal

SAFETY:
- OANDA_ENV must be practice.
- ENABLE_DEMO_EXECUTION must remain NO.
- OANDA network methods implemented here: GET only.
- No POST / PUT / PATCH / DELETE.
- No order endpoint.
- Does not modify M005 canonical state.
- Does not modify M006c state.
- Does not modify M006e.1 observer state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd

import m006e2_twelve_validator as v2


ROOT_DEFAULT = Path(
    "./data/research_runs/M006E_OANDA_AUTHORITATIVE"
)

BASE = "https://api-fxpractice.oanda.com/v3"

MAP = {
    "AUDUSD": "AUD_USD",
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
}

LEGS = {
    "AUDUSD": ("AUD", "USD"),
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
}

OANDA_PRICE_MAX_MIN = 5.0


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp = path.with_suffix(
        path.suffix + ".tmp"
    )

    tmp.write_text(
        json.dumps(
            obj,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    tmp.replace(path)


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def get_json(
    url: str,
    token: str,
) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization":
                f"Bearer {token}"
        },
        method="GET",
    )

    with urllib.request.urlopen(
        req,
        timeout=20,
    ) as r:
        return json.load(r)


def require_safe_environment():
    if os.getenv(
        "OANDA_ENV"
    ) != "practice":
        raise SystemExit(
            "FAIL_CLOSED: "
            "OANDA_ENV must be practice"
        )

    if os.getenv(
        "ENABLE_DEMO_EXECUTION",
        "NO",
    ).strip().upper() != "NO":
        raise SystemExit(
            "FAIL_CLOSED: "
            "ENABLE_DEMO_EXECUTION "
            "must remain NO"
        )

    token = os.getenv(
        "OANDA_API_TOKEN",
        "",
    )

    account = os.getenv(
        "OANDA_ACCOUNT_ID",
        "",
    )

    if not token or not account:
        raise SystemExit(
            "FAIL_CLOSED: "
            "missing OANDA credentials"
        )

    return token, account


def read_all_events(
    root: Path,
) -> list[dict]:
    events = []

    for path in sorted(
        (root / "events").glob(
            "cycle_*.csv"
        )
    ):
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue

        if df.empty:
            continue

        for row in df.to_dict(
            orient="records"
        ):
            row[
                "_source_event_file"
            ] = str(path)

            events.append(row)

    return events


def event_id(event: dict) -> str:
    return v2.event_identity(
        event
    )


def event_ts(event: dict):
    return pd.to_datetime(
        event["bar_ts_utc"],
        utc=True,
    )


def observer_all_flat(
    root: Path,
) -> bool:
    p = (
        root
        / "state"
        / "observer_state.json"
    )

    if not p.exists():
        return False

    d = json.loads(
        p.read_text()
    )

    if d.get(
        "authority"
    ) != "OANDA":
        return False

    for pair in MAP:
        pos = int(
            d[
                "pairs"
            ][pair].get(
                "position",
                0,
            )
        )

        if pos != 0:
            return False

    return True


def default_bridge_state():
    return {
        "version": "M006e.3",
        "mode":
            "ZERO_WRITE_DRY_RUN",
        "authority": "OANDA",
        "initialized_at_utc": None,
        "processed_event_ids": [],
        "proposal_count": 0,
        "virtual_positions": {
            pair: {
                "position": 0,
                "allocation_x": 0.0,
            }
            for pair in MAP
        },
        "last_run_utc": None,
        "order_payloads_constructed":
            0,
        "oanda_write_requests_performed":
            0,
        "order_endpoints_invoked":
            False,
        "canonical_m005_modified":
            False,
        "m006c_state_modified":
            False,
        "m006e1_state_modified":
            False,
    }


def initialize(
    root: Path,
    state_path: Path,
):
    if state_path.exists():
        raise SystemExit(
            "FAIL_CLOSED: "
            "M006e.3 state already exists"
        )

    if not observer_all_flat(
        root
    ):
        raise SystemExit(
            "FAIL_CLOSED: "
            "M006e.1 observer must be "
            "flat on all pairs at "
            "M006e.3 initialization"
        )

    existing = read_all_events(
        root
    )

    state = default_bridge_state()

    now = pd.Timestamp.now(
        tz="UTC"
    )

    state[
        "initialized_at_utc"
    ] = now.isoformat()

    state[
        "processed_event_ids"
    ] = sorted(
        {
            event_id(e)
            for e in existing
        }
    )

    state[
        "existing_event_ids_snapshotted"
    ] = len(
        state[
            "processed_event_ids"
        ]
    )

    atomic_json(
        state_path,
        state,
    )

    print(
        "KQTRL M006e.3 — INITIALIZATION"
    )
    print("=" * 78)
    print(
        "Mode: ZERO WRITE / DRY RUN"
    )
    print(
        "Existing event IDs snapshotted:",
        len(
            state[
                "processed_event_ids"
            ]
        ),
    )
    print(
        "Virtual positions: "
        "AUDUSD=flat, EURUSD=flat, "
        "GBPUSD=flat, USDJPY=flat"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA write requests performed: 0"
    )
    print(
        "Order endpoints invoked: FALSE"
    )


def fetch_account_and_prices(
    token: str,
    account: str,
):
    summary = get_json(
        f"{BASE}/accounts/"
        f"{account}/summary",
        token,
    )["account"]

    if summary.get(
        "currency"
    ) != "AUD":
        raise RuntimeError(
            "FAIL_CLOSED: "
            "AUD OANDA account required"
        )

    nav = float(
        summary["NAV"]
    )

    instruments = ",".join(
        MAP.values()
    )

    query = urllib.parse.urlencode(
        {
            "instruments":
                instruments
        }
    )

    payload = get_json(
        f"{BASE}/accounts/"
        f"{account}/pricing?"
        f"{query}",
        token,
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    prices = {}

    for p in payload["prices"]:
        instrument = p[
            "instrument"
        ]

        bid = float(
            p["bids"][0][
                "price"
            ]
        )

        ask = float(
            p["asks"][0][
                "price"
            ]
        )

        ts = pd.to_datetime(
            p["time"],
            utc=True,
        )

        prices[instrument] = {
            "bid": bid,
            "ask": ask,
            "mid": (
                bid + ask
            ) / 2.0,
            "time": ts,
            "age_min":
                (
                    now - ts
                ).total_seconds()
                / 60.0,
        }

    missing = [
        instrument
        for instrument
        in MAP.values()
        if instrument
        not in prices
    ]

    if missing:
        raise RuntimeError(
            "FAIL_CLOSED: "
            "missing OANDA prices: "
            + ",".join(missing)
        )

    return nav, prices


def sizing_adapter(
    nav: float,
    mids: dict[str, float],
    entries: list[
        tuple[str, str]
    ],
    existing: dict[
        str, float
    ],
):
    """
    Exact M006d.2 Conservative-B
    pro-rata calculation.

    existing values are nominal
    allocation-x magnitudes.
    """

    gross = sum(
        abs(x)
        for x in existing.values()
    )

    cleg = Counter()
    newleg = Counter()

    for pair, x in existing.items():
        if pair not in LEGS:
            continue

        a, b = LEGS[pair]

        cleg[a] += abs(x)
        cleg[b] += abs(x)

    for pair, _side in entries:
        a, b = LEGS[pair]

        newleg[a] += 1
        newleg[b] += 1

    alpha = 1.0

    if entries:
        alpha = min(
            alpha,
            max(
                0.0,
                (
                    4.0 - gross
                )
                / len(entries),
            ),
        )

        for currency, n in (
            newleg.items()
        ):
            alpha = min(
                alpha,
                max(
                    0.0,
                    (
                        3.0
                        - cleg[
                            currency
                        ]
                    )
                    / n,
                ),
            )

    alpha = max(
        0.0,
        min(
            1.0,
            alpha,
        ),
    )

    audusd = mids[
        "AUD_USD"
    ]

    aud_per_base = {
        "AUDUSD":
            1.0,
        "EURUSD":
            mids[
                "EUR_USD"
            ]
            / audusd,
        "GBPUSD":
            mids[
                "GBP_USD"
            ]
            / audusd,
        "USDJPY":
            1.0
            / audusd,
    }

    rows = []

    for pair, side in entries:
        units = (
            nav
            * alpha
            / aud_per_base[
                pair
            ]
        )

        signed = (
            units
            if side == "long"
            else -units
        )

        rows.append(
            {
                "pair": pair,
                "side": side,
                "allocation_x":
                    alpha,
                "approx_units":
                    int(
                        round(
                            signed
                        )
                    ),
            }
        )

    return alpha, rows


def load_twelve_enriched(
    twelve_dir: Path,
):
    out = {}

    for pair in MAP:
        try:
            df = v2.load_twelve(
                twelve_dir,
                pair,
            )

            out[pair] = (
                v2.add_indicators(
                    df,
                    pair,
                )
            )

        except Exception:
            out[pair] = None

    return out


def virtual_existing(
    state: dict,
):
    out = {}

    for pair, st in (
        state[
            "virtual_positions"
        ].items()
    ):
        if int(
            st.get(
                "position",
                0,
            )
        ) != 0:
            out[pair] = float(
                st.get(
                    "allocation_x",
                    0.0,
                )
            )

    return out


def price_is_fresh(
    pair: str,
    prices: dict,
):
    instrument = MAP[pair]

    age = float(
        prices[
            instrument
        ]["age_min"]
    )

    return (
        0.0
        <= age
        <= OANDA_PRICE_MAX_MIN
    ), age


def side_from_position(
    new_position: str,
):
    p = v2.position_to_int(
        new_position
    )

    if p == 1:
        return "long"

    if p == -1:
        return "short"

    raise ValueError(
        "new position is not "
        "an entry direction"
    )


def apply_virtual_exit(
    state: dict,
    pair: str,
):
    st = state[
        "virtual_positions"
    ][pair]

    had_position = (
        int(
            st.get(
                "position",
                0,
            )
        )
        != 0
    )

    st[
        "position"
    ] = 0

    st[
        "allocation_x"
    ] = 0.0

    return had_position


def apply_virtual_entry(
    state: dict,
    pair: str,
    side: str,
    allocation_x: float,
):
    state[
        "virtual_positions"
    ][pair] = {
        "position":
            (
                1
                if side
                == "long"
                else -1
            ),
        "allocation_x":
            float(
                allocation_x
            ),
    }


def consume_event_id(
    processed: set,
    report: dict,
    eid: str,
    retry_pending: set,
) -> bool:
    """
    Entry blocks are terminal and therefore consumed.

    Exit/reversal events whose risk-reducing exit leg could not
    be processed solely because OANDA pricing was stale remain
    unconsumed so the next bridge cycle can retry them.
    """
    if eid in retry_pending:
        report[
            "retry_pending_event_ids"
        ].append(eid)
        return False

    processed.add(eid)

    report[
        "processed_event_ids"
    ].append(eid)

    return True


def self_test():
    print("=" * 78)
    print(
        "KQTRL M006e.3 — "
        "OFFLINE SELF TEST"
    )
    print("=" * 78)

    mids = {
        "AUD_USD": 0.66,
        "EUR_USD": 1.10,
        "GBP_USD": 1.30,
        "USD_JPY": 150.0,
    }

    nav = 100000.0

    alpha, rows = (
        sizing_adapter(
            nav,
            mids,
            [
                (
                    "AUDUSD",
                    "long",
                ),
            ],
            {},
        )
    )

    assert alpha == 1.0

    assert (
        rows[0][
            "approx_units"
        ]
        == 100000
    )

    print(
        "PASS sizing single entry = 1.000000x"
    )

    alpha, _ = (
        sizing_adapter(
            nav,
            mids,
            [
                (
                    "AUDUSD",
                    "long",
                ),
                (
                    "EURUSD",
                    "long",
                ),
                (
                    "GBPUSD",
                    "long",
                ),
                (
                    "USDJPY",
                    "long",
                ),
            ],
            {},
        )
    )

    # USD is present in all four
    # currency-leg exposures.
    # 3x currency-leg cap therefore
    # binds before 4x gross cap.
    assert abs(
        alpha - 0.75
    ) < 1e-12

    print(
        "PASS four-pair USD-leg cap -> "
        "alpha=0.750000"
    )

    alpha, _ = (
        sizing_adapter(
            nav,
            mids,
            [
                (
                    "EURUSD",
                    "long",
                ),
            ],
            {
                "AUDUSD": 1.0,
                "GBPUSD": 1.0,
            },
        )
    )

    # Existing USD leg = 2x;
    # EURUSD can receive only 1x.
    assert abs(
        alpha - 1.0
    ) < 1e-12

    print(
        "PASS existing exposure accounting"
    )

    st = default_bridge_state()

    apply_virtual_entry(
        st,
        "EURUSD",
        "long",
        0.75,
    )

    assert (
        st[
            "virtual_positions"
        ]["EURUSD"][
            "position"
        ]
        == 1
    )

    assert abs(
        st[
            "virtual_positions"
        ]["EURUSD"][
            "allocation_x"
        ]
        - 0.75
    ) < 1e-12

    print(
        "PASS virtual entry state"
    )

    assert apply_virtual_exit(
        st,
        "EURUSD",
    )

    assert (
        st[
            "virtual_positions"
        ]["EURUSD"][
            "position"
        ]
        == 0
    )

    print(
        "PASS virtual exit state"
    )

    print(
        "Network calls: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )
    print(
        "Order endpoints implemented: NONE"
    )
    print(
        "M006E3_SELF_TEST: PASS"
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--m006e-root",
        default=str(
            ROOT_DEFAULT
        ),
    )

    ap.add_argument(
        "--twelve-dir",
        default=(
            "./data/"
            "live_5m_twelve"
        ),
    )

    ap.add_argument(
        "--initialize",
        action="store_true",
    )

    ap.add_argument(
        "--self-test",
        action="store_true",
    )

    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    token, account = (
        require_safe_environment()
    )

    root = Path(
        args.m006e_root
    )

    bridge_root = (
        root / "bridge"
    )

    state_path = (
        bridge_root
        / "state"
        / "bridge_state.json"
    )

    if args.initialize:
        initialize(
            root,
            state_path,
        )
        return 0

    if not state_path.exists():
        raise SystemExit(
            "FAIL_CLOSED: "
            "M006e.3 bridge state "
            "does not exist; "
            "initialize first"
        )

    state_before_hash = sha256(
        root
        / "state"
        / "observer_state.json"
    )

    m006c_path = Path(
        "./data/research_runs/"
        "M006_PRACTICE_EXECUTION/"
        "signal_order_bridge/"
        "state/bridge_state.json"
    )

    m006c_before_hash = (
        sha256(
            m006c_path
        )
    )

    state = json.loads(
        state_path.read_text()
    )

    processed = set(
        state.get(
            "processed_event_ids",
            [],
        )
    )

    all_events = read_all_events(
        root
    )

    new_events = [
        e
        for e in all_events
        if event_id(e)
        not in processed
    ]

    new_events.sort(
        key=lambda e: (
            event_ts(e),
            str(
                e.get(
                    "pair",
                    "",
                )
            ),
        )
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    rid = now.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    report = {
        "run_id": rid,
        "mode":
            "ZERO_WRITE_DRY_RUN",
        "authority": "OANDA",
        "validator": "Twelve Data",
        "new_authoritative_events":
            len(new_events),
        "validation_rows": [],
        "actions": [],
        "blocked_entries": [],
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
        "pricing": {},
        "order_payloads_constructed":
            0,
        "oanda_write_requests_performed":
            0,
        "order_endpoints_invoked":
            False,
        "canonical_m005_modified":
            False,
        "m006c_state_modified":
            False,
        "m006e1_state_modified":
            False,
    }

    if not new_events:
        state[
            "last_run_utc"
        ] = now.isoformat()

        atomic_json(
            state_path,
            state,
        )

        outdir = (
            bridge_root
            / "reports"
        )

        outdir.mkdir(
            parents=True,
            exist_ok=True,
        )

        out = (
            outdir
            / (
                "bridge_cycle_"
                f"{rid}.json"
            )
        )

        out.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print(
            "KQTRL M006e.3 — "
            "ZERO-WRITE DRY-RUN BRIDGE"
        )
        print("=" * 78)
        print(
            "New authoritative events: 0"
        )
        print(
            "Proposals: 0"
        )
        print(
            "OANDA network calls: 0"
        )
        print(
            "Order payloads constructed: 0"
        )
        print(
            "OANDA write requests performed: 0"
        )
        print(
            "Order endpoints invoked: FALSE"
        )
        print(
            "Report:",
            out,
        )

        return 0

    twelve = (
        load_twelve_enriched(
            Path(
                args.twelve_dir
            )
        )
    )

    nav, prices = (
        fetch_account_and_prices(
            token,
            account,
        )
    )

    mids = {
        instrument:
            info["mid"]
        for instrument, info
        in prices.items()
    }

    for pair, instrument in (
        MAP.items()
    ):
        report[
            "pricing"
        ][pair] = {
            "instrument":
                instrument,
            "mid":
                prices[
                    instrument
                ]["mid"],
            "age_min":
                prices[
                    instrument
                ]["age_min"],
            "fresh_le_5m":
                (
                    0.0
                    <= prices[
                        instrument
                    ]["age_min"]
                    <= OANDA_PRICE_MAX_MIN
                ),
        }

    # Process simultaneous strategy events
    # together by authoritative bar timestamp.
    grouped = {}

    # Events placed here are deliberately NOT consumed.
    # This is reserved for risk-reducing exit/reversal legs
    # that cannot currently proceed because OANDA pricing
    # is stale. They must be retried next bridge cycle.
    retry_pending = set()

    for e in new_events:
        key = event_ts(
            e
        ).isoformat()

        grouped.setdefault(
            key,
            [],
        ).append(e)

    for ts in sorted(
        grouped
    ):
        batch = grouped[ts]

        entry_candidates = []

        # EXIT LEGS FIRST.
        for e in batch:
            pair = str(
                e["pair"]
            )

            results = (
                v2.validate_event(
                    e,
                    twelve.get(
                        pair
                    ),
                    now,
                )
            )

            report[
                "validation_rows"
            ].extend(
                results
            )

            etype = str(
                e[
                    "event_type"
                ]
            ).strip().lower()

            fresh, age = (
                price_is_fresh(
                    pair,
                    prices,
                )
            )

            if etype in (
                "exit",
                "reversal",
            ):
                exit_row = (
                    results[0]
                )

                if not fresh:
                    eid = event_id(
                        e
                    )

                    # M006d.1 requires fresh OANDA pricing
                    # for position closure. This is a
                    # temporary operational block, not a
                    # terminal strategy decision, so retain
                    # the event for retry.
                    retry_pending.add(
                        eid
                    )

                    report[
                        "actions"
                    ].append(
                        {
                            "event_id":
                                eid,
                            "pair":
                                pair,
                            "leg":
                                (
                                    "exit"
                                    if etype
                                    == "exit"
                                    else
                                    "reversal_exit"
                                ),
                            "decision":
                                "RETRY_PENDING",
                            "reason":
                                "OANDA_PRICE_STALE_"
                                f"{age:.2f}M",
                            "status":
                                "SUPPRESSED_DRY_RUN",
                        }
                    )

                else:
                    had_virtual = (
                        apply_virtual_exit(
                            state,
                            pair,
                        )
                    )

                    report[
                        "actions"
                    ].append(
                        {
                            "event_id":
                                event_id(
                                    e
                                ),
                            "pair":
                                pair,
                            "leg":
                                (
                                    "exit"
                                    if etype
                                    == "exit"
                                    else
                                    "reversal_exit"
                                ),
                            "decision":
                                exit_row[
                                    "decision"
                                ],
                            "virtual_position_existed":
                                had_virtual,
                            "oanda_price_age_min":
                                age,
                            "status":
                                "SUPPRESSED_DRY_RUN",
                        }
                    )

        # IDENTIFY ENTRY LEGS AFTER EXITS.
        for e in batch:
            pair = str(
                e["pair"]
            )

            etype = str(
                e[
                    "event_type"
                ]
            ).strip().lower()

            if etype not in (
                "entry",
                "reversal",
            ):
                continue

            eid = event_id(
                e
            )

            # A reversal may not progress to its new entry
            # until the risk-reducing exit leg has actually
            # cleared the OANDA freshness gate.
            if (
                etype == "reversal"
                and eid in retry_pending
            ):
                report[
                    "blocked_entries"
                ].append(
                    {
                        "event_id":
                            eid,
                        "pair":
                            pair,
                        "leg":
                            "reversal_entry",
                        "decision":
                            "RETRY_PENDING",
                        "reasons": [
                            "REVERSAL_EXIT_NOT_COMPLETED"
                        ],
                        "status":
                            "SUPPRESSED_DRY_RUN",
                    }
                )

                continue

            results = (
                v2.validate_event(
                    e,
                    twelve.get(
                        pair
                    ),
                    now,
                )
            )

            entry_row = (
                results[0]
                if etype
                == "entry"
                else results[1]
            )

            fresh, age = (
                price_is_fresh(
                    pair,
                    prices,
                )
            )

            reasons = list(
                entry_row.get(
                    "reasons",
                    [],
                )
            )

            if not v2.boolish(
                e.get(
                    "in_session",
                    False,
                )
            ):
                reasons.append(
                    "AUTHORITATIVE_EVENT_"
                    "NOT_IN_SESSION"
                )

            if not fresh:
                reasons.append(
                    "OANDA_PRICE_STALE_"
                    f"{age:.2f}M"
                )

            allowed = (
                entry_row[
                    "decision"
                ]
                == "ALLOW_DRY_RUN_VALIDATION"
                and not reasons
            )

            if allowed:
                entry_candidates.append(
                    {
                        "event": e,
                        "pair": pair,
                        "side":
                            side_from_position(
                                e[
                                    "new_position"
                                ]
                            ),
                        "oanda_price_age_min":
                            age,
                        "validation":
                            entry_row,
                    }
                )

            else:
                report[
                    "blocked_entries"
                ].append(
                    {
                        "event_id":
                            event_id(
                                e
                            ),
                        "pair":
                            pair,
                        "leg":
                            (
                                "entry"
                                if etype
                                == "entry"
                                else
                                "reversal_entry"
                            ),
                        "decision":
                            "BLOCK",
                        "reasons":
                            reasons,
                        "status":
                            "SUPPRESSED_DRY_RUN",
                    }
                )

        if entry_candidates:
            existing = (
                virtual_existing(
                    state
                )
            )

            requested = [
                (
                    x["pair"],
                    x["side"],
                )
                for x
                in entry_candidates
            ]

            alpha, sized = (
                sizing_adapter(
                    nav,
                    mids,
                    requested,
                    existing,
                )
            )

            sized_by_pair = {
                x["pair"]: x
                for x in sized
            }

            for x in (
                entry_candidates
            ):
                pair = x[
                    "pair"
                ]

                s = sized_by_pair[
                    pair
                ]

                if (
                    s[
                        "allocation_x"
                    ]
                    <= 0
                ):
                    report[
                        "blocked_entries"
                    ].append(
                        {
                            "event_id":
                                event_id(
                                    x[
                                        "event"
                                    ]
                                ),
                            "pair":
                                pair,
                            "decision":
                                "BLOCK",
                            "reasons": [
                                "CONSERVATIVE_B_"
                                "ALLOCATION_ZERO"
                            ],
                            "status":
                                "SUPPRESSED_DRY_RUN",
                        }
                    )

                    continue

                apply_virtual_entry(
                    state,
                    pair,
                    x["side"],
                    s[
                        "allocation_x"
                    ],
                )

                report[
                    "actions"
                ].append(
                    {
                        "event_id":
                            event_id(
                                x[
                                    "event"
                                ]
                            ),
                        "pair":
                            pair,
                        "leg":
                            (
                                "entry"
                                if str(
                                    x[
                                        "event"
                                    ][
                                        "event_type"
                                    ]
                                ).lower()
                                == "entry"
                                else
                                "reversal_entry"
                            ),
                        "side":
                            x[
                                "side"
                            ],
                        "allocation_x":
                            s[
                                "allocation_x"
                            ],
                        "approx_units":
                            s[
                                "approx_units"
                            ],
                        "pro_rata_alpha":
                            alpha,
                        "oanda_price_age_min":
                            x[
                                "oanda_price_age_min"
                            ],
                        "decision":
                            "ALLOW_DRY_RUN_PROPOSAL",
                        "status":
                            "SUPPRESSED_DRY_RUN",
                    }
                )

                state[
                    "proposal_count"
                ] = int(
                    state.get(
                        "proposal_count",
                        0,
                    )
                ) + 1

        # Entry blocks are terminal and consumed.
        # Successful exits are consumed.
        # Exit/reversal events temporarily blocked by stale
        # OANDA pricing stay unconsumed for the next cycle.
        for e in batch:
            eid = event_id(
                e
            )

            consume_event_id(
                processed,
                report,
                eid,
                retry_pending,
            )

    state[
        "processed_event_ids"
    ] = sorted(
        processed
    )

    state[
        "last_run_utc"
    ] = now.isoformat()

    observer_after_hash = sha256(
        root
        / "state"
        / "observer_state.json"
    )

    m006c_after_hash = sha256(
        m006c_path
    )

    if (
        state_before_hash
        != observer_after_hash
    ):
        raise RuntimeError(
            "FAIL_CLOSED: "
            "M006e.1 observer state "
            "changed during bridge run"
        )

    if (
        m006c_before_hash
        != m006c_after_hash
    ):
        raise RuntimeError(
            "FAIL_CLOSED: "
            "M006c state changed "
            "during bridge run"
        )

    atomic_json(
        state_path,
        state,
    )

    outdir = (
        bridge_root
        / "reports"
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True,
    )

    out = (
        outdir
        / (
            "bridge_cycle_"
            f"{rid}.json"
        )
    )

    out.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print(
        "KQTRL M006e.3 — "
        "ZERO-WRITE DRY-RUN BRIDGE"
    )
    print("=" * 78)
    print(
        "Authority: OANDA"
    )
    print(
        "Validator: Twelve Data"
    )
    print(
        "Execution venue target: "
        "OANDA practice"
    )
    print(
        "Mode: ZERO WRITE / "
        "SUPPRESSED DRY RUN"
    )
    print(
        "New authoritative events:",
        len(new_events),
    )
    print(
        "Validation rows:",
        len(
            report[
                "validation_rows"
            ]
        ),
    )
    print(
        "Dry-run actions:",
        len(
            report[
                "actions"
            ]
        ),
    )
    print(
        "Blocked entries:",
        len(
            report[
                "blocked_entries"
            ]
        ),
    )
    print(
        "Retry-pending events:",
        len(
            report[
                "retry_pending_event_ids"
            ]
        ),
    )

    print()

    for action in report[
        "actions"
    ]:
        print(
            action[
                "pair"
            ],
            action[
                "leg"
            ],
            action[
                "decision"
            ],
            action[
                "status"
            ],
        )

    for blocked in report[
        "blocked_entries"
    ]:
        print(
            blocked[
                "pair"
            ],
            blocked.get(
                "leg",
                "entry",
            ),
            "BLOCK",
            blocked[
                "reasons"
            ],
        )

    print()
    print(
        "Report:",
        out,
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA write requests performed: 0"
    )
    print(
        "Order endpoints invoked: FALSE"
    )
    print(
        "Canonical M005 modified: FALSE"
    )
    print(
        "M006c state modified: FALSE"
    )
    print(
        "M006e.1 observer state modified: FALSE"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
