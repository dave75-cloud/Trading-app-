#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, time, timezone
from pathlib import Path


ROOT = Path(".").resolve()

RUN_ROOT = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE"
)

LOG_DIR = (
    RUN_ROOT
    / "orchestration/logs"
)

OBSERVER_STATE = (
    RUN_ROOT
    / "state/observer_state.json"
)

BRIDGE_STATE = (
    RUN_ROOT
    / "bridge/state/bridge_state.json"
)

ACTIVE_START = time(10, 50)
ACTIVE_END = time(14, 20)

INTERVAL_SECONDS = 300

WATERMARK_WARN_MIN = 15.0
WATERMARK_ALERT_MIN = 25.0

BRIDGE_WARN_MIN = 15.0
BRIDGE_ALERT_MIN = 25.0

MIN_COVERAGE_WARN = 0.80
MIN_COVERAGE_ALERT = 0.50


def parse_dt(v):
    if not v:
        return None

    try:
        x = datetime.fromisoformat(
            str(v).replace(
                "Z",
                "+00:00",
            )
        )

        if x.tzinfo is None:
            x = x.replace(
                tzinfo=timezone.utc
            )

        return x.astimezone(
            timezone.utc
        )

    except Exception:
        return None


def cycle_timestamp(path: Path):
    m = re.search(
        r'cycle_(\d{8}T\d{6}Z)',
        path.name,
    )

    if not m:
        return None

    try:
        return datetime.strptime(
            m.group(1),
            "%Y%m%dT%H%M%SZ",
        ).replace(
            tzinfo=timezone.utc
        )

    except Exception:
        return None


def active_bounds(day):
    start = datetime.combine(
        day,
        ACTIVE_START,
        tzinfo=timezone.utc,
    )

    end = datetime.combine(
        day,
        ACTIVE_END,
        tzinfo=timezone.utc,
    )

    return start, end


def session_phase(now):
    start, end = active_bounds(
        now.date()
    )

    if now.weekday() >= 5:
        return "WEEKEND", start, end

    if now < start:
        return "PRE_WINDOW", start, end

    if now <= end:
        return "ACTIVE_WINDOW", start, end

    return "POST_WINDOW", start, end


def expected_cycles(now, start, end):
    if now < start:
        return 0

    cutoff = min(
        now,
        end,
    )

    elapsed = (
        cutoff
        - start
    ).total_seconds()

    return (
        int(
            elapsed
            // INTERVAL_SECONDS
        )
        + 1
    )


def classify_log(path: Path):
    try:
        text = path.read_text(
            errors="replace"
        )
    except Exception:
        return "OTHER"

    upper = text.upper()

    if (
        "M006E5_CYCLE: PASS"
        in upper
        or
        "M006E5_CYCLE PASS"
        in upper
    ):
        return "PASS"

    if (
        "FAIL_CLOSED"
        in upper
        or
        "M006E5_CYCLE: FAIL"
        in upper
        or
        "TRACEBACK"
        in upper
    ):
        return "FAIL"

    if (
        "SKIP"
        in upper
    ):
        return "SKIP"

    return "OTHER"


def active_logs(
    day,
    start,
    end,
):
    rows = []

    for p in sorted(
        LOG_DIR.glob(
            "cycle_*.log"
        )
    ):
        ts = cycle_timestamp(
            p
        )

        if ts is None:
            continue

        if ts.date() != day:
            continue

        if not (
            start
            <= ts
            <= end
        ):
            continue

        rows.append(
            {
                "path":
                    str(p),
                "timestamp":
                    ts,
                "status":
                    classify_log(
                        p
                    ),
            }
        )

    return rows


def load_json(path):
    try:
        return json.loads(
            path.read_text()
        )
    except Exception:
        return None


def observer_watermarks():
    d = load_json(
        OBSERVER_STATE
    )

    if not isinstance(
        d,
        dict,
    ):
        return {}

    candidates = (
        d.get("pairs")
        or d.get("state")
        or d.get("pair_state")
        or {}
    )

    out = {}

    if isinstance(
        candidates,
        dict,
    ):
        for pair, row in candidates.items():
            if not isinstance(
                row,
                dict,
            ):
                continue

            value = (
                row.get("watermark")
                or row.get("last_bar_ts")
                or row.get("last_processed_ts")
                or row.get("latest_completed")
            )

            dt = parse_dt(
                value
            )

            if dt is not None:
                out[
                    str(pair)
                ] = dt

    # Support top-level watermark maps too.
    wm = d.get(
        "watermarks"
    )

    if isinstance(
        wm,
        dict,
    ):
        for pair, value in wm.items():
            dt = parse_dt(
                value
            )

            if dt is not None:
                out[
                    str(pair)
                ] = dt

    return out


def bridge_last_run():
    d = load_json(
        BRIDGE_STATE
    )

    if not isinstance(
        d,
        dict,
    ):
        return None

    for key in [
        "last_run",
        "last_run_utc",
        "updated_at",
    ]:
        dt = parse_dt(
            d.get(
                key
            )
        )

        if dt is not None:
            return dt

    return None


def age_minutes(
    now,
    ts,
):
    if ts is None:
        return None

    return (
        now
        - ts
    ).total_seconds() / 60.0


def evaluate(
    now,
    phase,
    start,
    end,
    logs,
    watermarks,
    bridge_run,
):
    issues = []

    counts = {
        "PASS": 0,
        "SKIP": 0,
        "FAIL": 0,
        "OTHER": 0,
    }

    for row in logs:
        counts[
            row["status"]
        ] += 1

    expected = expected_cycles(
        now,
        start,
        end,
    )

    observed = len(
        logs
    )

    coverage = (
        observed / expected
        if expected > 0
        else None
    )

    pass_ratio = (
        counts["PASS"]
        / observed
        if observed
        else None
    )

    skip_ratio = (
        counts["SKIP"]
        / observed
        if observed
        else None
    )

    # Before the active window, absence of active cycles is expected.
    if phase in {
        "PRE_WINDOW",
        "WEEKEND",
    }:
        return {
            "verdict":
                "NOT_DUE",
            "issues":
                [],
            "counts":
                counts,
            "expected_cycles":
                expected,
            "observed_cycles":
                observed,
            "coverage_ratio":
                coverage,
            "pass_ratio":
                pass_ratio,
            "skip_ratio":
                skip_ratio,
        }

    if counts[
        "FAIL"
    ] > 0:
        issues.append(
            (
                "ALERT",
                f"{counts['FAIL']} active-window "
                "orchestration failure(s)",
            )
        )

    # Give launchd 20 minutes from window start before declaring
    # a zero-cycle condition.
    elapsed_min = (
        now
        - start
    ).total_seconds() / 60.0

    if (
        elapsed_min >= 20
        and observed == 0
    ):
        issues.append(
            (
                "ALERT",
                "active window has no orchestration cycles",
            )
        )

    if (
        elapsed_min >= 20
        and counts["PASS"] == 0
        and observed > 0
    ):
        issues.append(
            (
                "ALERT",
                "active window has cycles but zero PASS cycles",
            )
        )

    if coverage is not None:
        if (
            elapsed_min >= 20
            and coverage
            < MIN_COVERAGE_ALERT
        ):
            issues.append(
                (
                    "ALERT",
                    f"cycle coverage only {coverage:.1%}",
                )
            )

        elif (
            elapsed_min >= 20
            and coverage
            < MIN_COVERAGE_WARN
        ):
            issues.append(
                (
                    "WARN",
                    f"cycle coverage only {coverage:.1%}",
                )
            )

    if (
        skip_ratio is not None
        and observed >= 4
    ):
        if skip_ratio > 0.50:
            issues.append(
                (
                    "ALERT",
                    f"active-window SKIP ratio {skip_ratio:.1%}",
                )
            )

        elif skip_ratio > 0.25:
            issues.append(
                (
                    "WARN",
                    f"active-window SKIP ratio {skip_ratio:.1%}",
                )
            )

    reference_now = min(
        now,
        end,
    )

    if watermarks:
        for pair, ts in sorted(
            watermarks.items()
        ):
            age = age_minutes(
                reference_now,
                ts,
            )

            if age is None:
                continue

            if age > WATERMARK_ALERT_MIN:
                issues.append(
                    (
                        "ALERT",
                        f"{pair} observer watermark "
                        f"stale by {age:.1f}m",
                    )
                )

            elif age > WATERMARK_WARN_MIN:
                issues.append(
                    (
                        "WARN",
                        f"{pair} observer watermark "
                        f"age {age:.1f}m",
                    )
                )

    elif elapsed_min >= 20:
        issues.append(
            (
                "WARN",
                "observer watermark information unavailable",
            )
        )

    if bridge_run is not None:
        bridge_age = age_minutes(
            reference_now,
            bridge_run,
        )

        if bridge_age > BRIDGE_ALERT_MIN:
            issues.append(
                (
                    "ALERT",
                    f"bridge last-run stale by "
                    f"{bridge_age:.1f}m",
                )
            )

        elif bridge_age > BRIDGE_WARN_MIN:
            issues.append(
                (
                    "WARN",
                    f"bridge last-run age "
                    f"{bridge_age:.1f}m",
                )
            )

    elif elapsed_min >= 20:
        issues.append(
            (
                "WARN",
                "bridge last-run unavailable",
            )
        )

    severities = {
        x[0]
        for x in issues
    }

    if "ALERT" in severities:
        verdict = "ALERT"
    elif "WARN" in severities:
        verdict = "WARN"
    else:
        verdict = "CLEAN"

    return {
        "verdict":
            verdict,
        "issues":
            issues,
        "counts":
            counts,
        "expected_cycles":
            expected,
        "observed_cycles":
            observed,
        "coverage_ratio":
            coverage,
        "pass_ratio":
            pass_ratio,
        "skip_ratio":
            skip_ratio,
    }


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--now",
        help=(
            "Override UTC now for testing, "
            "ISO-8601 format."
        ),
    )

    ap.add_argument(
        "--json-out",
    )

    args = ap.parse_args()

    now = (
        parse_dt(
            args.now
        )
        if args.now
        else datetime.now(
            timezone.utc
        )
    )

    if now is None:
        raise SystemExit(
            "Invalid --now timestamp"
        )

    phase, start, end = session_phase(
        now
    )

    logs = active_logs(
        now.date(),
        start,
        end,
    )

    watermarks = (
        observer_watermarks()
    )

    bridge_run = (
        bridge_last_run()
    )

    result = evaluate(
        now,
        phase,
        start,
        end,
        logs,
        watermarks,
        bridge_run,
    )

    print("=" * 78)
    print(
        "KQTRL M006e.6a — "
        "ACTIVE-SESSION COVERAGE HEALTH"
    )
    print("=" * 78)

    print(
        "UTC now:",
        now.isoformat(),
    )

    print(
        "Phase:",
        phase,
    )

    print(
        "Active window:",
        start.isoformat(),
        "to",
        end.isoformat(),
    )

    print()
    print(
        "Expected cycles:",
        result[
            "expected_cycles"
        ],
    )

    print(
        "Observed active-window cycles:",
        result[
            "observed_cycles"
        ],
    )

    print(
        "PASS:",
        result[
            "counts"
        ]["PASS"],
    )

    print(
        "SKIP:",
        result[
            "counts"
        ]["SKIP"],
    )

    print(
        "FAIL:",
        result[
            "counts"
        ]["FAIL"],
    )

    print(
        "OTHER:",
        result[
            "counts"
        ]["OTHER"],
    )

    if (
        result[
            "coverage_ratio"
        ]
        is not None
    ):
        print(
            "Coverage:",
            f"{result['coverage_ratio']:.1%}",
        )

    print()
    print(
        "Observer watermarks:"
    )

    if watermarks:
        for pair, ts in sorted(
            watermarks.items()
        ):
            print(
                f"  {pair}:",
                ts.isoformat(),
            )
    else:
        print(
            "  unavailable"
        )

    print(
        "Bridge last run:",
        (
            bridge_run.isoformat()
            if bridge_run
            else "unavailable"
        ),
    )

    print()
    print(
        "=== COVERAGE ISSUES ==="
    )

    if result[
        "issues"
    ]:
        for severity, text in result[
            "issues"
        ]:
            print(
                severity + ":",
                text,
            )
    else:
        print(
            "None"
        )

    print()
    print(
        "COVERAGE VERDICT:",
        result[
            "verdict"
        ],
    )

    print()
    print(
        "Network calls by M006e.6a: 0"
    )

    print(
        "External writes:",
        (
            "local JSON only"
            if args.json_out
            else "0"
        ),
    )

    print(
        "Trading/order capability: NONE"
    )

    report = {
        "version":
            "M006e.6a",
        "mode":
            "READ_ONLY_ACTIVE_SESSION_COVERAGE",
        "utc_now":
            now.isoformat(),
        "phase":
            phase,
        "active_window_start":
            start.isoformat(),
        "active_window_end":
            end.isoformat(),
        "result":
            result,
        "watermarks":
            {
                k:
                    v.isoformat()
                for k, v
                in watermarks.items()
            },
        "bridge_last_run":
            (
                bridge_run.isoformat()
                if bridge_run
                else None
            ),
        "network_calls":
            0,
        "order_capability":
            False,
    }

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

        print(
            "JSON:",
            p,
        )


if __name__ == "__main__":
    main()
