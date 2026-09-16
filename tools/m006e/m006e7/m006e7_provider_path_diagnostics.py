#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

import m006e2_twelve_validator as v2


ROOT = Path(".").resolve()

M006E_ROOT = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE"
)

EVENT_DIR = (
    M006E_ROOT
    / "events"
)

TWELVE_DIR_DEFAULT = (
    ROOT
    / "data/live_5m_twelve"
)

OUTDIR_DEFAULT = (
    M006E_ROOT
    / "provider_path_diagnostics"
)

THRESHOLD = 0.0005

PAIRS = [
    "AUDUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
]


def boolish(v):
    return v2.boolish(v)


def event_files():
    return sorted(
        EVENT_DIR.glob(
            "cycle_*.csv"
        )
    )


def load_events(day=None):
    rows = []

    for path in event_files():
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue

        if df.empty:
            continue

        for r in df.to_dict(
            orient="records"
        ):
            ts = pd.to_datetime(
                r["bar_ts_utc"],
                utc=True,
            )

            if (
                day is not None
                and ts.date()
                != day
            ):
                continue

            r[
                "_source_file"
            ] = str(path)

            rows.append(r)

    rows.sort(
        key=lambda r: (
            pd.to_datetime(
                r["bar_ts_utc"],
                utc=True,
            ),
            str(
                r.get(
                    "pair",
                    "",
                )
            ),
        )
    )

    return rows


def load_twelve_all(
    twelve_dir: Path,
):
    out = {}

    for pair in PAIRS:
        try:
            raw = v2.load_twelve(
                twelve_dir,
                pair,
            )

            enriched = (
                v2.add_indicators(
                    raw,
                    pair,
                )
            )

            out[pair] = enriched

        except Exception:
            out[pair] = None

    return out


def signal_int(v):
    if pd.isna(v):
        return None

    try:
        x = int(
            float(v)
        )
    except Exception:
        return None

    if x > 0:
        return 1

    if x < 0:
        return -1

    return 0


def find_same_bar(
    df,
    ts,
):
    if df is None:
        return None

    if df.empty:
        return None

    ts_col = None

    for candidate in [
        "ts",
        "timestamp",
        "datetime",
    ]:
        if candidate in df.columns:
            ts_col = candidate
            break

    if ts_col is None:
        return None

    d = df.copy()

    d["_ts_cmp"] = pd.to_datetime(
        d[ts_col],
        utc=True,
    )

    match = d[
        d["_ts_cmp"] == ts
    ]

    if match.empty:
        return None

    return match.iloc[-1]


def get_first(
    row,
    names,
):
    for name in names:
        if name in row.index:
            v = row[name]

            if not pd.isna(v):
                return v

    return None


def diagnose_event(
    event,
    twelve_df,
):
    pair = str(
        event["pair"]
    )

    ts = pd.to_datetime(
        event["bar_ts_utc"],
        utc=True,
    )

    o_close = float(
        event["close"]
    )

    o_vol = float(
        event["volatility"]
    )

    o_vol_ok = boolish(
        event.get(
            "volatility_ok",
            False,
        )
    )

    o_signal = signal_int(
        event.get(
            "desired_delayed_signal"
        )
    )

    base = {
        "pair": pair,
        "bar_ts_utc":
            ts.isoformat(),
        "event_type":
            str(
                event.get(
                    "event_type",
                    ""
                )
            ),
        "old_position":
            str(
                event.get(
                    "old_position",
                    ""
                )
            ),
        "new_position":
            str(
                event.get(
                    "new_position",
                    ""
                )
            ),
        "oanda_close":
            o_close,
        "oanda_volatility":
            o_vol,
        "oanda_volatility_ok":
            o_vol_ok,
        "oanda_vol_distance_from_threshold":
            o_vol - THRESHOLD,
        "oanda_delayed_signal":
            o_signal,
        "twelve_bar_present":
            False,
        "source_event_file":
            event.get(
                "_source_file"
            ),
    }

    trow = find_same_bar(
        twelve_df,
        ts,
    )

    if trow is None:
        base.update(
            {
                "diagnostic_status":
                    "TWELVE_BAR_MISSING",
                "close_divergence_bps":
                    None,
                "twelve_close":
                    None,
                "twelve_volatility":
                    None,
                "twelve_volatility_ok":
                    None,
                "twelve_vol_distance_from_threshold":
                    None,
                "twelve_delayed_signal":
                    None,
                "direction_agreement":
                    None,
                "volatility_eligibility_agreement":
                    None,
            }
        )

        return base

    t_close_raw = get_first(
        trow,
        [
            "c",
            "close",
        ],
    )

    t_vol_raw = get_first(
        trow,
        [
            "vol",
            "volatility",
        ],
    )

    t_vol_ok_raw = get_first(
        trow,
        [
            "vol_ok",
            "volatility_ok",
        ],
    )

    t_signal_raw = get_first(
        trow,
        [
            "delayed_signal",
            "desired_delayed_signal",
        ],
    )

    t_close = (
        float(
            t_close_raw
        )
        if t_close_raw
        is not None
        else None
    )

    t_vol = (
        float(
            t_vol_raw
        )
        if t_vol_raw
        is not None
        else None
    )

    t_vol_ok = (
        boolish(
            t_vol_ok_raw
        )
        if t_vol_ok_raw
        is not None
        else None
    )

    t_signal = signal_int(
        t_signal_raw
    )

    divergence_bps = None

    if (
        t_close is not None
        and o_close != 0
    ):
        divergence_bps = (
            (
                t_close
                / o_close
            )
            - 1.0
        ) * 10000.0

    direction_agreement = (
        None
        if (
            o_signal is None
            or t_signal is None
        )
        else (
            o_signal
            == t_signal
        )
    )

    vol_agreement = (
        None
        if t_vol_ok
        is None
        else (
            o_vol_ok
            == t_vol_ok
        )
    )

    status_bits = []

    if (
        direction_agreement
        is False
    ):
        status_bits.append(
            "DIRECTION_DISAGREEMENT"
        )

    if (
        vol_agreement
        is False
    ):
        status_bits.append(
            "VOL_ELIGIBILITY_DISAGREEMENT"
        )

    if (
        divergence_bps
        is not None
        and abs(
            divergence_bps
        ) > 10.0
    ):
        status_bits.append(
            "PRICE_DIVERGENCE_GT_10BPS"
        )

    elif (
        divergence_bps
        is not None
        and abs(
            divergence_bps
        ) >= 5.0
    ):
        status_bits.append(
            "PRICE_DIVERGENCE_5_TO_10BPS"
        )

    if not status_bits:
        status_bits.append(
            "AGREEMENT"
        )

    base.update(
        {
            "diagnostic_status":
                "|".join(
                    status_bits
                ),
            "twelve_bar_present":
                True,
            "twelve_close":
                t_close,
            "close_divergence_bps":
                divergence_bps,
            "twelve_volatility":
                t_vol,
            "twelve_volatility_ok":
                t_vol_ok,
            "twelve_vol_distance_from_threshold":
                (
                    t_vol
                    - THRESHOLD
                    if t_vol
                    is not None
                    else None
                ),
            "twelve_delayed_signal":
                t_signal,
            "direction_agreement":
                direction_agreement,
            "volatility_eligibility_agreement":
                vol_agreement,
        }
    )

    return base


def summarize(rows):
    by_pair = {}

    for pair in PAIRS:
        rr = [
            r
            for r in rows
            if r["pair"]
            == pair
        ]

        statuses = Counter()

        for r in rr:
            for bit in str(
                r[
                    "diagnostic_status"
                ]
            ).split("|"):
                statuses[
                    bit
                ] += 1

        divergences = [
            abs(
                float(
                    r[
                        "close_divergence_bps"
                    ]
                )
            )
            for r in rr
            if r[
                "close_divergence_bps"
            ]
            is not None
        ]

        by_pair[pair] = {
            "events":
                len(rr),
            "missing_twelve":
                sum(
                    1
                    for r in rr
                    if not r[
                        "twelve_bar_present"
                    ]
                ),
            "direction_disagreements":
                sum(
                    1
                    for r in rr
                    if r[
                        "direction_agreement"
                    ]
                    is False
                ),
            "volatility_eligibility_disagreements":
                sum(
                    1
                    for r in rr
                    if r[
                        "volatility_eligibility_agreement"
                    ]
                    is False
                ),
            "max_abs_close_divergence_bps":
                (
                    max(
                        divergences
                    )
                    if divergences
                    else None
                ),
            "status_counts":
                dict(
                    sorted(
                        statuses.items()
                    )
                ),
        }

    aggregate = {
        "events":
            len(rows),
        "missing_twelve":
            sum(
                1
                for r in rows
                if not r[
                    "twelve_bar_present"
                ]
            ),
        "direction_disagreements":
            sum(
                1
                for r in rows
                if r[
                    "direction_agreement"
                ]
                is False
            ),
        "volatility_eligibility_disagreements":
            sum(
                1
                for r in rows
                if r[
                    "volatility_eligibility_agreement"
                ]
                is False
            ),
        "price_divergence_gt_10bps":
            sum(
                1
                for r in rows
                if (
                    r[
                        "close_divergence_bps"
                    ]
                    is not None
                    and abs(
                        r[
                            "close_divergence_bps"
                        ]
                    )
                    > 10.0
                )
            ),
        "price_divergence_5_to_10bps":
            sum(
                1
                for r in rows
                if (
                    r[
                        "close_divergence_bps"
                    ]
                    is not None
                    and 5.0
                    <= abs(
                        r[
                            "close_divergence_bps"
                        ]
                    )
                    <= 10.0
                )
            ),
    }

    return {
        "aggregate":
            aggregate,
        "by_pair":
            by_pair,
    }


def print_report(
    rows,
    summary,
):
    print(
        "=" * 78
    )
    print(
        "KQTRL M006e.7 — "
        "PROVIDER-PATH DIAGNOSTICS"
    )
    print(
        "=" * 78
    )

    a = summary[
        "aggregate"
    ]

    print(
        "Authoritative OANDA events:",
        a["events"],
    )
    print(
        "Missing Twelve bars:",
        a["missing_twelve"],
    )
    print(
        "Direction disagreements:",
        a[
            "direction_disagreements"
        ],
    )
    print(
        "Volatility-eligibility disagreements:",
        a[
            "volatility_eligibility_disagreements"
        ],
    )
    print(
        "Price divergence 5-10 bps:",
        a[
            "price_divergence_5_to_10bps"
        ],
    )
    print(
        "Price divergence >10 bps:",
        a[
            "price_divergence_gt_10bps"
        ],
    )

    print()
    print(
        "=== BY PAIR ==="
    )

    for pair in PAIRS:
        s = summary[
            "by_pair"
        ][pair]

        print(
            pair,
            f"events={s['events']}",
            f"missing={s['missing_twelve']}",
            "direction_disagree="
            f"{s['direction_disagreements']}",
            "vol_disagree="
            f"{s['volatility_eligibility_disagreements']}",
            "max_abs_div_bps="
            f"{s['max_abs_close_divergence_bps']}",
        )

    if rows:
        print()
        print(
            "=== EVENT DETAIL ==="
        )

        for r in rows:
            print()
            print(
                r["bar_ts_utc"],
                r["pair"],
                r["event_type"],
                r["diagnostic_status"],
            )

            print(
                "  OANDA close:",
                r["oanda_close"],
                "Twelve close:",
                r["twelve_close"],
                "div_bps:",
                r[
                    "close_divergence_bps"
                ],
            )

            print(
                "  OANDA vol:",
                r[
                    "oanda_volatility"
                ],
                "distance:",
                r[
                    "oanda_vol_distance_from_threshold"
                ],
                "eligible:",
                r[
                    "oanda_volatility_ok"
                ],
            )

            print(
                "  Twelve vol:",
                r[
                    "twelve_volatility"
                ],
                "distance:",
                r[
                    "twelve_vol_distance_from_threshold"
                ],
                "eligible:",
                r[
                    "twelve_volatility_ok"
                ],
            )

            print(
                "  delayed signal "
                "OANDA/Twelve:",
                r[
                    "oanda_delayed_signal"
                ],
                "/",
                r[
                    "twelve_delayed_signal"
                ],
            )

    print()
    print(
        "Network calls by M006e.7: 0"
    )
    print(
        "External writes except requested "
        "local report files: 0"
    )
    print(
        "Order/trading capability: NONE"
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--day",
        help=(
            "Optional UTC day YYYY-MM-DD. "
            "Default: all recorded M006e.1 events."
        ),
    )

    ap.add_argument(
        "--twelve-dir",
        default=str(
            TWELVE_DIR_DEFAULT
        ),
    )

    ap.add_argument(
        "--json-out",
    )

    ap.add_argument(
        "--csv-out",
    )

    args = ap.parse_args()

    day = None

    if args.day:
        day = pd.Timestamp(
            args.day
        ).date()

    events = load_events(
        day=day
    )

    twelve = load_twelve_all(
        Path(
            args.twelve_dir
        )
    )

    rows = []

    for e in events:
        pair = str(
            e["pair"]
        )

        rows.append(
            diagnose_event(
                e,
                twelve.get(
                    pair
                ),
            )
        )

    summary = summarize(
        rows
    )

    report = {
        "version":
            "M006e.7",
        "mode":
            "READ_ONLY_PROVIDER_PATH_DIAGNOSTIC",
        "frozen_volatility_threshold":
            THRESHOLD,
        "day":
            (
                day.isoformat()
                if day
                else None
            ),
        "summary":
            summary,
        "events":
            rows,
        "network_calls":
            0,
        "order_capability":
            False,
    }

    print_report(
        rows,
        summary,
    )

    if args.json_out:
        p = Path(
            args.json_out
        )

        p.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        p.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print()
        print(
            "JSON:",
            p,
        )

    if args.csv_out:
        p = Path(
            args.csv_out
        )

        p.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pd.DataFrame(
            rows
        ).to_csv(
            p,
            index=False,
        )

        print(
            "CSV:",
            p,
        )


if __name__ == "__main__":
    main()
