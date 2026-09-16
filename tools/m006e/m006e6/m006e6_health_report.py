#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(".").resolve()

M006E_ROOT = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE"
)

ORCH_LOGDIR = (
    M006E_ROOT
    / "orchestration/logs"
)

E1_STATE = (
    M006E_ROOT
    / "state/observer_state.json"
)

E3_STATE = (
    M006E_ROOT
    / "bridge/state/bridge_state.json"
)

E3_REPORT_DIR = (
    M006E_ROOT
    / "bridge/reports"
)

E2_VALIDATION_DIR = (
    M006E_ROOT
    / "validation"
)

EVENT_DIR = (
    M006E_ROOT
    / "events"
)

CORE_FILES = {
    "m006e1_observer":
        ROOT
        / "tools/m006e/"
          "m006e1_oanda_authoritative_observer.py",

    "m006e2_validator":
        ROOT
        / "tools/m006e/"
          "m006e2_twelve_validator.py",

    "m006e3_bridge":
        ROOT
        / "tools/m006e/"
          "m006e3_zero_write_bridge.py",

    "m006e4_regression":
        ROOT
        / "tools/m006e/"
          "audit_m006e4_integration_regression.py",

    "m006e5_wrapper":
        ROOT
        / "tools/m006e/m006e5/"
          "run_m006e5_cycle.sh",
}

ACCEPTED_HASHES = {
    "m006e1_observer":
        "6dc02067094cb65c5c1bdc451825b9c02539bf5eef2cde19e95fbe2c492e49e4",

    "m006e2_validator":
        "4e1ad3efa00087a858b16ba6502aa3784d7de8b59971b85b7df7ac49195933f0",

    "m006e3_bridge":
        "568e30e90e95df8c7e30519947f13699fe72305e22ad9a669d8fe3b04f9b43b5",

    "m006e4_regression":
        "a45ca6f104e3cc9bf4ac0b8c273b50dc6cf09448ee823c66a1bea23972308934",

    "m006e5_wrapper":
        "a5780b27af2d550a47d9163ece6e6db81e1f8e769ff13c8190fa8565743e036e",
}


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_json(path: Path):
    if not path.exists():
        return None

    try:
        return json.loads(
            path.read_text()
        )
    except Exception:
        return None


def parse_day(day_arg: str | None):
    if day_arg:
        return pd.Timestamp(
            day_arg,
            tz="UTC",
        ).date()

    return pd.Timestamp.now(
        tz="UTC"
    ).date()


def files_for_day(
    directory: Path,
    pattern: str,
    day,
):
    out = []

    if not directory.exists():
        return out

    for p in sorted(
        directory.glob(pattern)
    ):
        m = re.search(
            r"(\d{8})T",
            p.name,
        )

        if not m:
            continue

        d = pd.Timestamp(
            m.group(1)
        ).date()

        if d == day:
            out.append(p)

    return out


def orchestration_summary(day):
    files = files_for_day(
        ORCH_LOGDIR,
        "cycle_*.log",
        day,
    )

    counts = Counter()
    failures = []
    latest = None

    for p in files:
        text = p.read_text(
            errors="replace"
        )

        latest = p

        if "M006E5_CYCLE: PASS" in text:
            counts["pass"] += 1
        elif "SKIP:" in text:
            counts["skip"] += 1
        elif "FAIL_CLOSED:" in text:
            counts["fail"] += 1

            first = next(
                (
                    line.strip()
                    for line
                    in text.splitlines()
                    if "FAIL_CLOSED:"
                    in line
                ),
                "FAIL_CLOSED",
            )

            failures.append(
                {
                    "file": str(p),
                    "reason": first,
                }
            )
        else:
            counts["other"] += 1

    return {
        "files": len(files),
        "pass": counts["pass"],
        "skip": counts["skip"],
        "fail": counts["fail"],
        "other": counts["other"],
        "latest":
            str(latest)
            if latest
            else None,
        "failures": failures,
    }


def event_summary(day):
    files = files_for_day(
        EVENT_DIR,
        "cycle_*.csv",
        day,
    )

    total = 0
    by_pair = Counter()
    by_type = Counter()

    for p in files:
        try:
            df = pd.read_csv(p)
        except pd.errors.EmptyDataError:
            continue

        if df.empty:
            continue

        total += len(df)

        if "pair" in df.columns:
            by_pair.update(
                df["pair"]
                .astype(str)
                .tolist()
            )

        if "event_type" in df.columns:
            by_type.update(
                df["event_type"]
                .astype(str)
                .str.lower()
                .tolist()
            )

    return {
        "event_files": len(files),
        "events": total,
        "by_pair":
            dict(
                sorted(
                    by_pair.items()
                )
            ),
        "by_type":
            dict(
                sorted(
                    by_type.items()
                )
            ),
    }


def validation_summary(day):
    files = files_for_day(
        E2_VALIDATION_DIR,
        "*.json",
        day,
    )

    rows = 0
    decisions = Counter()
    reasons = Counter()

    for p in files:
        d = load_json(p)

        if not d:
            continue

        vals = (
            d.get(
                "validation_rows",
                d.get(
                    "rows",
                    [],
                ),
            )
        )

        if not isinstance(
            vals,
            list,
        ):
            continue

        for r in vals:
            if not isinstance(
                r,
                dict,
            ):
                continue

            rows += 1

            decision = str(
                r.get(
                    "decision",
                    "UNKNOWN",
                )
            )

            decisions[
                decision
            ] += 1

            rr = r.get(
                "reasons",
                [],
            )

            if isinstance(
                rr,
                str,
            ):
                rr = [rr]

            if isinstance(
                rr,
                list,
            ):
                reasons.update(
                    str(x)
                    for x in rr
                )

    return {
        "files": len(files),
        "rows": rows,
        "decisions":
            dict(
                sorted(
                    decisions.items()
                )
            ),
        "reasons":
            dict(
                sorted(
                    reasons.items(),
                    key=lambda x:
                        (
                            -x[1],
                            x[0],
                        )
                )
            ),
    }


def bridge_report_summary(day):
    files = files_for_day(
        E3_REPORT_DIR,
        "bridge_cycle_*.json",
        day,
    )

    new_events = 0
    actions = 0
    blocked_entries = 0
    retry_pending = 0
    action_legs = Counter()
    block_reasons = Counter()

    latest = None

    for p in files:
        d = load_json(p)

        if not d:
            continue

        latest = p

        new_events += int(
            d.get(
                "new_authoritative_events",
                0,
            )
        )

        aa = d.get(
            "actions",
            [],
        )

        bb = d.get(
            "blocked_entries",
            [],
        )

        rr = d.get(
            "retry_pending_event_ids",
            [],
        )

        if isinstance(
            aa,
            list,
        ):
            actions += len(aa)

            for x in aa:
                if isinstance(
                    x,
                    dict,
                ):
                    action_legs[
                        str(
                            x.get(
                                "leg",
                                "UNKNOWN",
                            )
                        )
                    ] += 1

        if isinstance(
            bb,
            list,
        ):
            blocked_entries += len(bb)

            for x in bb:
                if not isinstance(
                    x,
                    dict,
                ):
                    continue

                reasons = x.get(
                    "reasons",
                    [],
                )

                if isinstance(
                    reasons,
                    str,
                ):
                    reasons = [
                        reasons
                    ]

                if isinstance(
                    reasons,
                    list,
                ):
                    block_reasons.update(
                        str(r)
                        for r in reasons
                    )

        if isinstance(
            rr,
            list,
        ):
            retry_pending += len(rr)

    return {
        "files": len(files),
        "new_authoritative_events":
            new_events,
        "actions": actions,
        "blocked_entries":
            blocked_entries,
        "retry_pending":
            retry_pending,
        "action_legs":
            dict(
                sorted(
                    action_legs.items()
                )
            ),
        "block_reasons":
            dict(
                sorted(
                    block_reasons.items(),
                    key=lambda x:
                        (
                            -x[1],
                            x[0],
                        )
                )
            ),
        "latest_report":
            str(latest)
            if latest
            else None,
    }


def observer_state_summary():
    d = load_json(
        E1_STATE
    )

    if not d:
        return {
            "present": False
        }

    pairs = {}

    for pair, st in (
        d.get(
            "pairs",
            {}
        ).items()
    ):
        pairs[pair] = {
            "position":
                st.get(
                    "position"
                ),
            "bars_held":
                st.get(
                    "bars_held"
                ),
            "last_signal":
                st.get(
                    "last_signal"
                ),
        }

    return {
        "present": True,
        "authority":
            d.get(
                "authority"
            ),
        "mode":
            d.get(
                "mode"
            ),
        "initialized_at_utc":
            d.get(
                "initialized_at_utc"
            ),
        "watermarks":
            d.get(
                "watermarks",
                {},
            ),
        "pairs": pairs,
        "gap_quarantines":
            d.get(
                "gap_quarantines",
                {},
            ),
    }


def bridge_state_summary():
    d = load_json(
        E3_STATE
    )

    if not d:
        return {
            "present": False
        }

    return {
        "present": True,
        "version":
            d.get(
                "version"
            ),
        "mode":
            d.get(
                "mode"
            ),
        "initialized_at_utc":
            d.get(
                "initialized_at_utc"
            ),
        "last_run_utc":
            d.get(
                "last_run_utc"
            ),
        "processed_event_ids":
            len(
                d.get(
                    "processed_event_ids",
                    [],
                )
            ),
        "proposal_count":
            d.get(
                "proposal_count",
                0,
            ),
        "virtual_positions":
            d.get(
                "virtual_positions",
                {},
            ),
        "order_payloads_constructed":
            d.get(
                "order_payloads_constructed",
                0,
            ),
        "oanda_write_requests_performed":
            d.get(
                "oanda_write_requests_performed",
                0,
            ),
        "order_endpoints_invoked":
            d.get(
                "order_endpoints_invoked",
                False,
            ),
    }


def hash_summary():
    out = {}

    for name, path in (
        CORE_FILES.items()
    ):
        actual = sha256(
            path
        )

        expected = (
            ACCEPTED_HASHES[
                name
            ]
        )

        out[name] = {
            "path": str(path),
            "actual": actual,
            "expected": expected,
            "match":
                actual == expected,
        }

    return out


def health_flags(
    orch,
    obs,
    bridge,
    hashes,
):
    flags = []

    if orch["fail"] > 0:
        flags.append(
            "ORCHESTRATION_FAILURE_PRESENT"
        )

    if not obs.get(
        "present"
    ):
        flags.append(
            "M006E1_STATE_MISSING"
        )

    if not bridge.get(
        "present"
    ):
        flags.append(
            "M006E3_STATE_MISSING"
        )

    if bridge.get(
        "order_payloads_constructed",
        0,
    ) != 0:
        flags.append(
            "ORDER_PAYLOAD_COUNT_NONZERO"
        )

    if bridge.get(
        "oanda_write_requests_performed",
        0,
    ) != 0:
        flags.append(
            "OANDA_WRITE_COUNT_NONZERO"
        )

    if bridge.get(
        "order_endpoints_invoked",
        False,
    ):
        flags.append(
            "ORDER_ENDPOINT_FLAG_TRUE"
        )

    bad_hashes = [
        name
        for name, row
        in hashes.items()
        if not row[
            "match"
        ]
    ]

    if bad_hashes:
        flags.append(
            "CORE_HASH_MISMATCH:"
            + ",".join(
                bad_hashes
            )
        )

    return flags


def print_report(
    day,
    report,
):
    print(
        "=" * 78
    )
    print(
        "KQTRL M006e.6 — "
        "OPERATIONAL HEALTH REPORT"
    )
    print(
        "=" * 78
    )
    print(
        "UTC day:",
        day.isoformat(),
    )

    print()
    print(
        "=== M006e.5 ORCHESTRATION ==="
    )

    o = report[
        "orchestration"
    ]

    print(
        "Cycle logs:",
        o["files"],
    )
    print(
        "PASS:",
        o["pass"],
    )
    print(
        "SKIP:",
        o["skip"],
    )
    print(
        "FAIL:",
        o["fail"],
    )
    print(
        "OTHER:",
        o["other"],
    )

    if o["latest"]:
        print(
            "Latest:",
            o["latest"],
        )

    print()
    print(
        "=== M006e.1 AUTHORITATIVE EVENTS ==="
    )

    e = report[
        "events"
    ]

    print(
        "Event files:",
        e["event_files"],
    )
    print(
        "Events:",
        e["events"],
    )
    print(
        "By pair:",
        e["by_pair"],
    )
    print(
        "By type:",
        e["by_type"],
    )

    print()
    print(
        "=== M006e.2 VALIDATION ==="
    )

    v = report[
        "validation"
    ]

    print(
        "Validation files:",
        v["files"],
    )
    print(
        "Rows:",
        v["rows"],
    )
    print(
        "Decisions:",
        v["decisions"],
    )
    print(
        "Reasons:",
        v["reasons"],
    )

    print()
    print(
        "=== M006e.3 BRIDGE REPORTS ==="
    )

    br = report[
        "bridge_reports"
    ]

    print(
        "Reports:",
        br["files"],
    )
    print(
        "New authoritative events:",
        br[
            "new_authoritative_events"
        ],
    )
    print(
        "Actions:",
        br["actions"],
    )
    print(
        "Blocked entries:",
        br[
            "blocked_entries"
        ],
    )
    print(
        "Retry-pending:",
        br[
            "retry_pending"
        ],
    )
    print(
        "Action legs:",
        br[
            "action_legs"
        ],
    )
    print(
        "Block reasons:",
        br[
            "block_reasons"
        ],
    )

    print()
    print(
        "=== CURRENT OBSERVER STATE ==="
    )

    obs = report[
        "observer_state"
    ]

    print(
        "Present:",
        obs.get(
            "present"
        ),
    )

    if obs.get(
        "present"
    ):
        print(
            "Authority:",
            obs.get(
                "authority"
            ),
        )
        print(
            "Mode:",
            obs.get(
                "mode"
            ),
        )
        print(
            "Initialized:",
            obs.get(
                "initialized_at_utc"
            ),
        )

        print(
            "Watermarks:"
        )

        for pair, ts in sorted(
            obs.get(
                "watermarks",
                {}
            ).items()
        ):
            print(
                f"  {pair}: {ts}"
            )

        print(
            "Positions:"
        )

        for pair, st in sorted(
            obs.get(
                "pairs",
                {}
            ).items()
        ):
            print(
                f"  {pair}: "
                f"position={st.get('position')} "
                f"bars_held={st.get('bars_held')} "
                f"last_signal={st.get('last_signal')}"
            )

    print()
    print(
        "=== CURRENT BRIDGE STATE ==="
    )

    bs = report[
        "bridge_state"
    ]

    print(
        "Present:",
        bs.get(
            "present"
        ),
    )

    if bs.get(
        "present"
    ):
        print(
            "Mode:",
            bs.get(
                "mode"
            ),
        )
        print(
            "Initialized:",
            bs.get(
                "initialized_at_utc"
            ),
        )
        print(
            "Last run:",
            bs.get(
                "last_run_utc"
            ),
        )
        print(
            "Processed IDs:",
            bs.get(
                "processed_event_ids"
            ),
        )
        print(
            "Proposal count:",
            bs.get(
                "proposal_count"
            ),
        )

        print(
            "Virtual positions:"
        )

        for pair, st in sorted(
            bs.get(
                "virtual_positions",
                {}
            ).items()
        ):
            pos = int(
                st.get(
                    "position",
                    0,
                )
            )

            name = {
                -1: "short",
                 0: "flat",
                 1: "long",
            }.get(
                pos,
                str(pos),
            )

            print(
                f"  {pair}: {name} "
                f"allocation_x="
                f"{st.get('allocation_x')}"
            )

        print(
            "Order payloads constructed:",
            bs.get(
                "order_payloads_constructed"
            ),
        )
        print(
            "OANDA writes:",
            bs.get(
                "oanda_write_requests_performed"
            ),
        )
        print(
            "Order endpoints invoked:",
            bs.get(
                "order_endpoints_invoked"
            ),
        )

    print()
    print(
        "=== FROZEN CORE HASHES ==="
    )

    for name, row in (
        report[
            "hashes"
        ].items()
    ):
        print(
            f"{name}: "
            f"{'PASS' if row['match'] else 'FAIL'}"
        )
        print(
            f"  {row['actual']}"
        )

    print()
    print(
        "=== HEALTH VERDICT ==="
    )

    flags = report[
        "health_flags"
    ]

    if flags:
        print(
            "STATUS: REVIEW_REQUIRED"
        )

        for f in flags:
            print(
                "  -",
                f,
            )
    else:
        print(
            "STATUS: CLEAN"
        )

    print()
    print(
        "Network calls by M006e.6: 0"
    )
    print(
        "External writes by M006e.6: 0"
    )
    print(
        "Trading/order capability: NONE"
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--day",
        help=(
            "UTC day YYYY-MM-DD; "
            "default=current UTC day"
        ),
    )

    ap.add_argument(
        "--json-out",
        help=(
            "Optional local JSON report path"
        ),
    )

    args = ap.parse_args()

    day = parse_day(
        args.day
    )

    orch = orchestration_summary(
        day
    )

    events = event_summary(
        day
    )

    validation = (
        validation_summary(
            day
        )
    )

    bridge_reports = (
        bridge_report_summary(
            day
        )
    )

    obs = (
        observer_state_summary()
    )

    bridge = (
        bridge_state_summary()
    )

    hashes = hash_summary()

    flags = health_flags(
        orch,
        obs,
        bridge,
        hashes,
    )

    report = {
        "version": "M006e.6",
        "mode":
            "READ_ONLY_OPERATIONAL_REPORT",
        "utc_day":
            day.isoformat(),
        "orchestration":
            orch,
        "events":
            events,
        "validation":
            validation,
        "bridge_reports":
            bridge_reports,
        "observer_state":
            obs,
        "bridge_state":
            bridge,
        "hashes":
            hashes,
        "health_flags":
            flags,
        "network_calls":
            0,
        "external_writes":
            0,
        "order_capability":
            False,
    }

    print_report(
        day,
        report,
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
            "JSON report:",
            p,
        )


if __name__ == "__main__":
    main()
