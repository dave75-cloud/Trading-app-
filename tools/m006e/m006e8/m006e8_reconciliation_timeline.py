#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


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

VALIDATION_DIR = (
    M006E_ROOT
    / "validation"
)

BRIDGE_REPORT_DIR = (
    M006E_ROOT
    / "bridge/reports"
)

PROVIDER_PATH_DIR = (
    M006E_ROOT
    / "provider_path_diagnostics"
)

OUTDIR_DEFAULT = (
    M006E_ROOT
    / "reconciliation"
)


def event_identity(row: dict) -> str:
    parts = [
        str(
            row.get(
                "cycle_id",
                "",
            )
        ),
        str(
            row.get(
                "provider",
                "",
            )
        ),
        str(
            row.get(
                "pair",
                "",
            )
        ),
        str(
            row.get(
                "bar_ts_utc",
                "",
            )
        ),
        str(
            row.get(
                "event_type",
                "",
            )
        ),
        str(
            row.get(
                "old_position",
                "",
            )
        ),
        str(
            row.get(
                "new_position",
                "",
            )
        ),
    ]

    return "|".join(parts)


def normalize_ts(v):
    if v is None:
        return None

    try:
        return pd.to_datetime(
            v,
            utc=True,
        ).isoformat()
    except Exception:
        return str(v)


def load_events(day=None):
    out = []

    for p in sorted(
        EVENT_DIR.glob(
            "cycle_*.csv"
        )
    ):
        try:
            df = pd.read_csv(p)
        except pd.errors.EmptyDataError:
            continue

        if df.empty:
            continue

        for row in df.to_dict(
            orient="records"
        ):
            ts = pd.to_datetime(
                row[
                    "bar_ts_utc"
                ],
                utc=True,
            )

            if (
                day is not None
                and ts.date()
                != day
            ):
                continue

            row[
                "_event_file"
            ] = str(p)

            row[
                "_event_id"
            ] = event_identity(
                row
            )

            out.append(
                row
            )

    out.sort(
        key=lambda r: (
            pd.to_datetime(
                r[
                    "bar_ts_utc"
                ],
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

    return out


def load_validation_rows(day=None):
    out = []

    for p in sorted(
        VALIDATION_DIR.glob(
            "*.json"
        )
    ):
        try:
            d = json.loads(
                p.read_text()
            )
        except Exception:
            continue

        rows = d.get(
            "validation_rows",
            d.get(
                "rows",
                [],
            ),
        )

        if not isinstance(
            rows,
            list,
        ):
            continue

        for r in rows:
            if not isinstance(
                r,
                dict,
            ):
                continue

            ts = (
                r.get(
                    "bar_ts_utc"
                )
                or r.get(
                    "event_bar_ts_utc"
                )
                or r.get(
                    "ts"
                )
            )

            if ts is not None:
                try:
                    dte = pd.to_datetime(
                        ts,
                        utc=True,
                    )

                    if (
                        day is not None
                        and dte.date()
                        != day
                    ):
                        continue
                except Exception:
                    pass

            r = dict(r)

            r[
                "_validation_file"
            ] = str(p)

            out.append(
                r
            )

    return out


def load_bridge_rows(day=None):
    actions = []
    blocked = []
    retries = set()

    for p in sorted(
        BRIDGE_REPORT_DIR.glob(
            "bridge_cycle_*.json"
        )
    ):
        try:
            d = json.loads(
                p.read_text()
            )
        except Exception:
            continue

        for r in d.get(
            "actions",
            [],
        ):
            if not isinstance(
                r,
                dict,
            ):
                continue

            x = dict(r)

            x[
                "_bridge_file"
            ] = str(p)

            actions.append(
                x
            )

        for r in d.get(
            "blocked_entries",
            [],
        ):
            if not isinstance(
                r,
                dict,
            ):
                continue

            x = dict(r)

            x[
                "_bridge_file"
            ] = str(p)

            blocked.append(
                x
            )

        for eid in d.get(
            "retry_pending_event_ids",
            [],
        ):
            retries.add(
                str(eid)
            )

    return (
        actions,
        blocked,
        retries,
    )


def load_provider_path(day=None):
    out = []

    files = sorted(
        PROVIDER_PATH_DIR.glob(
            "*.json"
        )
    )

    # Prefer latest generated provider-path file.
    if files:
        files = [
            files[-1]
        ]

    for p in files:
        try:
            d = json.loads(
                p.read_text()
            )
        except Exception:
            continue

        for r in d.get(
            "events",
            [],
        ):
            if not isinstance(
                r,
                dict,
            ):
                continue

            ts = r.get(
                "bar_ts_utc"
            )

            if ts is not None:
                try:
                    dte = pd.to_datetime(
                        ts,
                        utc=True,
                    )

                    if (
                        day is not None
                        and dte.date()
                        != day
                    ):
                        continue
                except Exception:
                    pass

            x = dict(r)

            x[
                "_provider_path_file"
            ] = str(p)

            out.append(
                x
            )

    return out


def validation_matches(
    event,
    validations,
):
    pair = str(
        event.get(
            "pair",
            "",
        )
    )

    ts = normalize_ts(
        event.get(
            "bar_ts_utc"
        )
    )

    matches = []

    for r in validations:
        rp = str(
            r.get(
                "pair",
                "",
            )
        )

        rts = normalize_ts(
            r.get(
                "bar_ts_utc"
            )
            or r.get(
                "event_bar_ts_utc"
            )
            or r.get(
                "ts"
            )
        )

        if (
            rp == pair
            and rts == ts
        ):
            matches.append(
                r
            )

    return matches


def provider_match(
    event,
    rows,
):
    pair = str(
        event.get(
            "pair",
            "",
        )
    )

    ts = normalize_ts(
        event.get(
            "bar_ts_utc"
        )
    )

    for r in rows:
        if (
            str(
                r.get(
                    "pair",
                    "",
                )
            )
            == pair
            and normalize_ts(
                r.get(
                    "bar_ts_utc"
                )
            )
            == ts
        ):
            return r

    return None


def bridge_matches(
    event,
    rows,
):
    eid = event[
        "_event_id"
    ]

    return [
        r
        for r in rows
        if str(
            r.get(
                "event_id",
                "",
            )
        )
        == eid
    ]


def build_timeline(
    events,
    validations,
    actions,
    blocked,
    retries,
    provider_rows,
):
    timeline = []

    for e in events:
        eid = e[
            "_event_id"
        ]

        vv = validation_matches(
            e,
            validations,
        )

        aa = bridge_matches(
            e,
            actions,
        )

        bb = bridge_matches(
            e,
            blocked,
        )

        pp = provider_match(
            e,
            provider_rows,
        )

        validation_decisions = [
            str(
                r.get(
                    "decision",
                    "UNKNOWN",
                )
            )
            for r in vv
        ]

        validation_reasons = []

        for r in vv:
            rr = r.get(
                "reasons",
                [],
            )

            if isinstance(
                rr,
                str,
            ):
                rr = [
                    rr
                ]

            if isinstance(
                rr,
                list,
            ):
                validation_reasons.extend(
                    str(x)
                    for x in rr
                )

        bridge_actions = [
            {
                "leg":
                    r.get(
                        "leg"
                    ),
                "decision":
                    r.get(
                        "decision"
                    ),
                "status":
                    r.get(
                        "status"
                    ),
                "reason":
                    r.get(
                        "reason"
                    ),
                "allocation_x":
                    r.get(
                        "allocation_x"
                    ),
                "approx_units":
                    r.get(
                        "approx_units"
                    ),
            }
            for r in aa
        ]

        blocked_rows = [
            {
                "leg":
                    r.get(
                        "leg"
                    ),
                "decision":
                    r.get(
                        "decision"
                    ),
                "reasons":
                    r.get(
                        "reasons"
                    ),
                "status":
                    r.get(
                        "status"
                    ),
            }
            for r in bb
        ]

        row = {
            "event_id":
                eid,
            "bar_ts_utc":
                normalize_ts(
                    e.get(
                        "bar_ts_utc"
                    )
                ),
            "pair":
                e.get(
                    "pair"
                ),
            "event_type":
                e.get(
                    "event_type"
                ),
            "old_position":
                e.get(
                    "old_position"
                ),
            "new_position":
                e.get(
                    "new_position"
                ),
            "oanda_close":
                e.get(
                    "close"
                ),
            "oanda_volatility":
                e.get(
                    "volatility"
                ),
            "oanda_volatility_ok":
                e.get(
                    "volatility_ok"
                ),
            "oanda_delayed_signal":
                e.get(
                    "desired_delayed_signal"
                ),
            "validation_rows":
                len(vv),
            "validation_decisions":
                validation_decisions,
            "validation_reasons":
                validation_reasons,
            "provider_path_status":
                (
                    pp.get(
                        "diagnostic_status"
                    )
                    if pp
                    else None
                ),
            "close_divergence_bps":
                (
                    pp.get(
                        "close_divergence_bps"
                    )
                    if pp
                    else None
                ),
            "twelve_volatility":
                (
                    pp.get(
                        "twelve_volatility"
                    )
                    if pp
                    else None
                ),
            "twelve_volatility_ok":
                (
                    pp.get(
                        "twelve_volatility_ok"
                    )
                    if pp
                    else None
                ),
            "twelve_delayed_signal":
                (
                    pp.get(
                        "twelve_delayed_signal"
                    )
                    if pp
                    else None
                ),
            "bridge_actions":
                bridge_actions,
            "blocked_entries":
                blocked_rows,
            "retry_pending":
                eid in retries,
        }

        timeline.append(
            row
        )

    return timeline


def summary(timeline):
    return {
        "events":
            len(timeline),
        "with_validation":
            sum(
                1
                for r in timeline
                if r[
                    "validation_rows"
                ]
                > 0
            ),
        "with_provider_path":
            sum(
                1
                for r in timeline
                if r[
                    "provider_path_status"
                ]
                is not None
            ),
        "with_bridge_action":
            sum(
                1
                for r in timeline
                if r[
                    "bridge_actions"
                ]
            ),
        "blocked_entries":
            sum(
                len(
                    r[
                        "blocked_entries"
                    ]
                )
                for r in timeline
            ),
        "retry_pending":
            sum(
                1
                for r in timeline
                if r[
                    "retry_pending"
                ]
            ),
    }


def print_report(
    timeline,
    s,
):
    print(
        "=" * 78
    )
    print(
        "KQTRL M006e.8 — "
        "POST-SESSION RECONCILIATION TIMELINE"
    )
    print(
        "=" * 78
    )

    print(
        "Authoritative events:",
        s["events"],
    )

    print(
        "Events with Twelve validation:",
        s[
            "with_validation"
        ],
    )

    print(
        "Events with provider-path diagnostics:",
        s[
            "with_provider_path"
        ],
    )

    print(
        "Events with bridge action:",
        s[
            "with_bridge_action"
        ],
    )

    print(
        "Blocked entry legs:",
        s[
            "blocked_entries"
        ],
    )

    print(
        "Retry-pending events:",
        s[
            "retry_pending"
        ],
    )

    if timeline:
        print()
        print(
            "=== EVENT TIMELINE ==="
        )

    for r in timeline:
        print()
        print(
            r[
                "bar_ts_utc"
            ],
            r[
                "pair"
            ],
            r[
                "event_type"
            ],
            f"{r['old_position']}->{r['new_position']}",
        )

        print(
            "  OANDA:",
            "close=",
            r[
                "oanda_close"
            ],
            "vol=",
            r[
                "oanda_volatility"
            ],
            "vol_ok=",
            r[
                "oanda_volatility_ok"
            ],
            "signal=",
            r[
                "oanda_delayed_signal"
            ],
        )

        print(
            "  Twelve validation:",
            r[
                "validation_decisions"
            ],
        )

        if r[
            "validation_reasons"
        ]:
            print(
                "  Validation reasons:",
                r[
                    "validation_reasons"
                ],
            )

        print(
            "  Provider path:",
            r[
                "provider_path_status"
            ],
            "div_bps=",
            r[
                "close_divergence_bps"
            ],
        )

        if r[
            "bridge_actions"
        ]:
            print(
                "  Bridge actions:",
                r[
                    "bridge_actions"
                ],
            )

        if r[
            "blocked_entries"
        ]:
            print(
                "  Blocked entries:",
                r[
                    "blocked_entries"
                ],
            )

        print(
            "  Retry pending:",
            r[
                "retry_pending"
            ],
        )

    print()
    print(
        "Network calls by M006e.8: 0"
    )
    print(
        "Trading/order writes by M006e.8: 0"
    )
    print(
        "Order capability: NONE"
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--day",
        help=(
            "Optional UTC day YYYY-MM-DD. "
            "Default: all recorded events."
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
        day
    )

    validations = (
        load_validation_rows(
            day
        )
    )

    (
        actions,
        blocked,
        retries,
    ) = load_bridge_rows(
        day
    )

    provider_rows = (
        load_provider_path(
            day
        )
    )

    timeline = build_timeline(
        events,
        validations,
        actions,
        blocked,
        retries,
        provider_rows,
    )

    s = summary(
        timeline
    )

    report = {
        "version":
            "M006e.8",
        "mode":
            "READ_ONLY_POST_SESSION_RECONCILIATION",
        "day":
            (
                day.isoformat()
                if day
                else None
            ),
        "summary":
            s,
        "timeline":
            timeline,
        "network_calls":
            0,
        "order_capability":
            False,
    }

    print_report(
        timeline,
        s,
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

        flat = []

        for r in timeline:
            x = dict(r)

            x[
                "validation_decisions"
            ] = json.dumps(
                x[
                    "validation_decisions"
                ]
            )

            x[
                "validation_reasons"
            ] = json.dumps(
                x[
                    "validation_reasons"
                ]
            )

            x[
                "bridge_actions"
            ] = json.dumps(
                x[
                    "bridge_actions"
                ]
            )

            x[
                "blocked_entries"
            ] = json.dumps(
                x[
                    "blocked_entries"
                ]
            )

            flat.append(
                x
            )

        pd.DataFrame(
            flat
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
