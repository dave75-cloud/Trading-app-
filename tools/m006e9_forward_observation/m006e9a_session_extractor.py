#!/usr/bin/env python3

"""
M006e.9a v1.1 — Forward-Observation Session Extractor

READ-ONLY with respect to:
    tools/m006e/
    data/research_runs/M006E_OANDA_AUTHORITATIVE/

Writes only when --write is explicitly supplied, and then only beneath:
    data/research_runs/M006E_FORWARD_OBSERVATION/

No network access.
No broker calls.
No subprocesses.
No promotion capability.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


VERSION = "M006e.9a-v1.1"

SOURCE_ROOT = Path(
    "data/research_runs/M006E_OANDA_AUTHORITATIVE"
)

OUTPUT_ROOT = Path(
    "data/research_runs/M006E_FORWARD_OBSERVATION"
)

ACTIVE_M006E2 = Path(
    "tools/m006e/m006e2_twelve_validator.py"
)

FROZEN_M006E2_SHA256 = (
    "d9c5b46b26d1cae4f000d5c584b9afa5e3a06805cb204559dae05013c6d2906d"
)

SESSION_START_UTC = time(10, 50)
SESSION_END_UTC = time(14, 20)

CYCLE_MINUTES = 5
DOWNSTREAM_GRACE_SECONDS = 120

MIN_COVERAGE_WARN = 0.80
MIN_COVERAGE_ALERT = 0.50

EXPECTED_CYCLES = (
    (
        SESSION_END_UTC.hour * 60
        + SESSION_END_UTC.minute
        - SESSION_START_UTC.hour * 60
        - SESSION_START_UTC.minute
    )
    // CYCLE_MINUTES
) + 1

STAMP_RE = re.compile(r"(\d{8}T\d{6}Z)")


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return obj


def timestamp_from_name(path: Path) -> datetime | None:
    matches = STAMP_RE.findall(path.name)
    if not matches:
        return None

    return datetime.strptime(
        matches[-1],
        "%Y%m%dT%H%M%SZ",
    ).replace(tzinfo=timezone.utc)


def session_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(
        day,
        SESSION_START_UTC,
        tzinfo=timezone.utc,
    )

    end = datetime.combine(
        day,
        SESSION_END_UTC,
        tzinfo=timezone.utc,
    )

    return start, end


def in_primary_session(path: Path, day: date) -> bool:
    ts = timestamp_from_name(path)
    if ts is None:
        return False

    start, end = session_bounds(day)
    return start <= ts <= end


def in_downstream_session(path: Path, day: date) -> bool:
    ts = timestamp_from_name(path)
    if ts is None:
        return False

    start, end = session_bounds(day)

    return (
        start
        <= ts
        <= end + timedelta(seconds=DOWNSTREAM_GRACE_SECONDS)
    )


def session_files(
    directory: Path,
    glob_pattern: str,
    day: date,
    downstream: bool = False,
) -> list[Path]:

    if not directory.exists():
        return []

    predicate = (
        in_downstream_session
        if downstream
        else in_primary_session
    )

    return sorted(
        p
        for p in directory.glob(glob_pattern)
        if p.is_file() and predicate(p, day)
    )


def latest_json_for_day(
    directory: Path,
    day: date,
) -> tuple[Path | None, dict[str, Any] | None]:

    candidates = []

    if not directory.exists():
        return None, None

    for path in directory.glob("*.json"):
        try:
            obj = load_json(path)
        except Exception:
            continue

        # Deliberately use internal diagnostic day.
        if obj.get("day") != day.isoformat():
            continue

        stamp = timestamp_from_name(path)

        if stamp is None:
            stamp = datetime.min.replace(
                tzinfo=timezone.utc
            )

        candidates.append(
            (stamp, path, obj)
        )

    if not candidates:
        return None, None

    _, path, obj = max(
        candidates,
        key=lambda x: x[0],
    )

    return path, obj


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def classify_cycle_text(text: str) -> str:
    # Failure takes precedence.
    if (
        "FAIL_CLOSED" in text
        or "M006E5_CYCLE: FAIL" in text
        or "M006E5_CYCLE FAIL" in text
    ):
        return "FAIL"

    if (
        "M006E5_CYCLE: PASS" in text
        or "M006E5_CYCLE PASS" in text
    ):
        return "PASS"

    if (
        "M006E5_CYCLE: SKIP" in text
        or "M006E5_CYCLE SKIP" in text
    ):
        return "SKIP"

    return "UNKNOWN"


def inspect_orchestration(
    paths: list[Path],
) -> dict[str, Any]:

    counts = Counter()
    failures = []
    unknown = []

    for path in paths:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        status = classify_cycle_text(text)
        counts[status] += 1

        if status == "UNKNOWN":
            unknown.append(str(path))

        if status == "FAIL":
            evidence = []

            for line in text.splitlines():
                if any(
                    token in line
                    for token in (
                        "FAIL_CLOSED",
                        "RuntimeError",
                        "HTTP 401",
                        "invalid JSON",
                        "Traceback",
                        "M006E5_CYCLE: FAIL",
                    )
                ):
                    evidence.append(
                        line.strip()[:300]
                    )

            ts = timestamp_from_name(path)

            failures.append(
                {
                    "file": str(path),
                    "timestamp_utc": (
                        ts.isoformat()
                        if ts else None
                    ),
                    "evidence": evidence[-8:],
                }
            )

    observed = len(paths)

    coverage_ratio = (
        observed / EXPECTED_CYCLES
        if EXPECTED_CYCLES
        else None
    )

    skip_ratio = (
        counts["SKIP"] / observed
        if observed
        else None
    )

    issues = []

    if counts["FAIL"]:
        issues.append(
            {
                "severity": "ALERT",
                "reason": (
                    f"{counts['FAIL']} "
                    "active-window orchestration failure(s)"
                ),
            }
        )

    if observed and counts["PASS"] == 0:
        issues.append(
            {
                "severity": "ALERT",
                "reason": (
                    "active window has cycles "
                    "but zero PASS cycles"
                ),
            }
        )

    if counts["UNKNOWN"]:
        issues.append(
            {
                "severity": "REVIEW",
                "reason": (
                    f"{counts['UNKNOWN']} "
                    "cycle(s) lack recognised status marker"
                ),
            }
        )

    if coverage_ratio is not None:
        if coverage_ratio < MIN_COVERAGE_ALERT:
            issues.append(
                {
                    "severity": "ALERT",
                    "reason": (
                        "cycle coverage only "
                        f"{coverage_ratio:.1%}"
                    ),
                }
            )

        elif coverage_ratio < MIN_COVERAGE_WARN:
            issues.append(
                {
                    "severity": "WARN",
                    "reason": (
                        "cycle coverage only "
                        f"{coverage_ratio:.1%}"
                    ),
                }
            )

    if skip_ratio is not None:
        if skip_ratio > 0.50:
            issues.append(
                {
                    "severity": "ALERT",
                    "reason": (
                        "active-window SKIP ratio "
                        f"{skip_ratio:.1%}"
                    ),
                }
            )

        elif skip_ratio > 0.25:
            issues.append(
                {
                    "severity": "WARN",
                    "reason": (
                        "active-window SKIP ratio "
                        f"{skip_ratio:.1%}"
                    ),
                }
            )

    severities = {
        item["severity"]
        for item in issues
    }

    if "ALERT" in severities:
        verdict = "ALERT"
    elif "REVIEW" in severities:
        verdict = "REVIEW"
    elif "WARN" in severities:
        verdict = "WARN"
    else:
        verdict = "CLEAN"

    return {
        "expected_cycles": EXPECTED_CYCLES,
        "observed_cycles": observed,
        "pass_cycles": counts["PASS"],
        "skip_cycles": counts["SKIP"],
        "fail_cycles": counts["FAIL"],
        "unknown_cycles": counts["UNKNOWN"],
        "missing_cycles": max(
            EXPECTED_CYCLES - observed,
            0,
        ),
        "coverage_ratio": coverage_ratio,
        "coverage_pct": (
            round(coverage_ratio * 100, 1)
            if coverage_ratio is not None
            else None
        ),
        "skip_ratio": skip_ratio,
        "verdict": verdict,
        "issues": issues,
        "unknown_logs": unknown,
        "failures": failures,
    }


def inspect_events(paths: list[Path]) -> dict[str, Any]:
    count = 0
    by_pair = Counter()
    by_type = Counter()
    observation_only_values = Counter()

    for path in paths:
        with path.open(
            "r",
            encoding="utf-8",
            errors="replace",
            newline="",
        ) as f:
            reader = csv.DictReader(f)

            for row in reader:
                if not any(
                    (value or "").strip()
                    for value in row.values()
                ):
                    continue

                event_type = (
                    row.get("event_type") or ""
                ).strip()

                pair = (
                    row.get("pair") or ""
                ).strip()

                if not event_type:
                    continue

                count += 1

                if pair:
                    by_pair[pair] += 1

                by_type[event_type] += 1

                observation_only_values[
                    (
                        row.get(
                            "observation_only"
                        )
                        or ""
                    ).strip()
                ] += 1

    return {
        "event_files": len(paths),
        "authoritative_events": count,
        "by_pair": dict(
            sorted(by_pair.items())
        ),
        "by_event_type": dict(
            sorted(by_type.items())
        ),
        "observation_only_values": dict(
            sorted(
                observation_only_values.items()
            )
        ),
    }


def inspect_bridge(paths: list[Path]) -> dict[str, Any]:
    totals = Counter()
    modes = Counter()
    authorities = Counter()
    violations = []

    for path in paths:
        obj = load_json(path)

        mode = obj.get("mode")
        authority = obj.get("authority")

        modes[str(mode)] += 1
        authorities[str(authority)] += 1

        writes = int(
            obj.get(
                "oanda_write_requests_performed"
            )
            or 0
        )

        payloads = int(
            obj.get(
                "order_payloads_constructed"
            )
            or 0
        )

        endpoints = bool(
            obj.get("order_endpoints_invoked")
        )

        totals["write_requests"] += writes
        totals["order_payloads"] += payloads
        totals["actions"] += len(
            obj.get("actions") or []
        )
        totals["blocked_entries"] += len(
            obj.get("blocked_entries") or []
        )
        totals["processed_event_ids"] += len(
            obj.get("processed_event_ids") or []
        )
        totals["retry_pending_event_ids"] += len(
            obj.get("retry_pending_event_ids") or []
        )
        totals["new_authoritative_events"] += int(
            obj.get("new_authoritative_events")
            or 0
        )

        local = []

        if mode != "ZERO_WRITE_DRY_RUN":
            local.append(
                f"unexpected mode={mode!r}"
            )

        if authority != "OANDA":
            local.append(
                f"unexpected authority={authority!r}"
            )

        if writes:
            local.append(
                f"write_requests={writes}"
            )

        if payloads:
            local.append(
                f"order_payloads={payloads}"
            )

        if endpoints:
            local.append(
                "order_endpoints_invoked=True"
            )

        for key in (
            "canonical_m005_modified",
            "m006c_state_modified",
            "m006e1_state_modified",
        ):
            if bool(obj.get(key)):
                local.append(
                    f"{key}=True"
                )

        if local:
            violations.append(
                {
                    "file": str(path),
                    "violations": local,
                }
            )

    return {
        "reports": len(paths),
        "modes": dict(modes),
        "authorities": dict(authorities),
        "totals": dict(totals),
        "safety_violations": violations,
    }


def inspect_validation(
    paths: list[Path],
) -> dict[str, Any]:

    totals = Counter()
    modes = Counter()
    authorities = Counter()
    validators = Counter()
    violations = []

    for path in paths:
        obj = load_json(path)

        mode = obj.get("mode")
        authority = obj.get("authority")
        validator = obj.get("validator")

        modes[str(mode)] += 1
        authorities[str(authority)] += 1
        validators[str(validator)] += 1

        network_calls = int(
            obj.get("oanda_network_calls")
            or 0
        )

        writes = int(
            obj.get(
                "oanda_write_requests_performed"
            )
            or 0
        )

        payloads = int(
            obj.get(
                "order_payloads_constructed"
            )
            or 0
        )

        endpoints = bool(
            obj.get("order_endpoints_invoked")
        )

        totals["authoritative_events"] += int(
            obj.get("authoritative_events")
            or 0
        )

        totals["validation_rows"] += int(
            obj.get("validation_rows")
            or 0
        )

        totals["oanda_network_calls"] += (
            network_calls
        )

        totals["write_requests"] += writes
        totals["order_payloads"] += payloads

        local = []

        if mode != "READ_ONLY_ZERO_WRITE":
            local.append(
                f"unexpected mode={mode!r}"
            )

        if authority != "OANDA":
            local.append(
                f"unexpected authority={authority!r}"
            )

        if network_calls:
            local.append(
                f"oanda_network_calls={network_calls}"
            )

        if writes:
            local.append(
                f"write_requests={writes}"
            )

        if payloads:
            local.append(
                f"order_payloads={payloads}"
            )

        if endpoints:
            local.append(
                "order_endpoints_invoked=True"
            )

        for key in (
            "canonical_m005_modified",
            "m006c_state_modified",
        ):
            if bool(obj.get(key)):
                local.append(
                    f"{key}=True"
                )

        if local:
            violations.append(
                {
                    "file": str(path),
                    "violations": local,
                }
            )

    return {
        "reports": len(paths),
        "modes": dict(modes),
        "authorities": dict(authorities),
        "validators": dict(validators),
        "totals": dict(totals),
        "safety_violations": violations,
    }


def inspect_provider_path(
    obj: dict[str, Any] | None,
) -> dict[str, Any]:

    if obj is None:
        return {
            "available": False,
            "events": 0,
        }

    events = obj.get("events") or []

    missing = 0
    direction_disagreements = 0
    volatility_disagreements = 0
    over_10bps = 0
    divergences = []

    for event in events:
        if not isinstance(event, dict):
            continue

        if not event.get("twelve_bar_present"):
            missing += 1

        if (
            event.get("direction_agreement")
            is False
        ):
            direction_disagreements += 1

        if (
            event.get(
                "volatility_eligibility_agreement"
            )
            is False
        ):
            volatility_disagreements += 1

        value = event.get(
            "close_divergence_bps"
        )

        if isinstance(value, (int, float)):
            value = abs(float(value))
            divergences.append(value)

            if value > 10.0:
                over_10bps += 1

    return {
        "available": True,
        "events": len(events),
        "missing_twelve_bars": missing,
        "direction_disagreements":
            direction_disagreements,
        "volatility_eligibility_disagreements":
            volatility_disagreements,
        "divergence_over_10bps": over_10bps,
        "max_abs_close_divergence_bps": (
            max(divergences)
            if divergences else None
        ),
        "summary": obj.get("summary"),
        "mode": obj.get("mode"),
        "network_calls":
            obj.get("network_calls"),
        "order_capability":
            obj.get("order_capability"),
    }


def inspect_reconciliation(
    obj: dict[str, Any] | None,
) -> dict[str, Any]:

    if obj is None:
        return {
            "available": False,
            "events": 0,
        }

    timeline = obj.get("timeline") or []

    return {
        "available": True,
        "events": len(timeline),
        "summary": obj.get("summary"),
        "mode": obj.get("mode"),
        "network_calls":
            obj.get("network_calls"),
        "order_capability":
            obj.get("order_capability"),
    }


def extract(day: date) -> dict[str, Any]:

    logs = session_files(
        SOURCE_ROOT / "orchestration/logs",
        "cycle_*.log",
        day,
    )

    event_files = session_files(
        SOURCE_ROOT / "events",
        "cycle_*.csv",
        day,
    )

    bridge_files = session_files(
        SOURCE_ROOT / "bridge/reports",
        "bridge_cycle_*.json",
        day,
        downstream=True,
    )

    validation_files = session_files(
        SOURCE_ROOT / "validation",
        "m006e2_event_validation_*.json",
        day,
        downstream=True,
    )

    orchestration = inspect_orchestration(
        logs
    )

    events = inspect_events(
        event_files
    )

    bridge = inspect_bridge(
        bridge_files
    )

    validation = inspect_validation(
        validation_files
    )

    provider_file, provider_obj = (
        latest_json_for_day(
            SOURCE_ROOT
            / "provider_path_diagnostics",
            day,
        )
    )

    reconciliation_file, reconciliation_obj = (
        latest_json_for_day(
            SOURCE_ROOT / "reconciliation",
            day,
        )
    )

    current_hash = sha256(
        ACTIVE_M006E2
    )

    safety_violations = (
        len(
            bridge["safety_violations"]
        )
        + len(
            validation["safety_violations"]
        )
    )

    return {
        "version": VERSION,
        "day": day.isoformat(),
        "mode":
            "READ_ONLY_FORWARD_OBSERVATION_EXTRACTION",

        "source_root": str(
            SOURCE_ROOT
        ),

        "session_window_utc": {
            "start": "10:50:00",
            "end": "14:20:00",
            "cycle_minutes":
                CYCLE_MINUTES,
            "downstream_grace_seconds":
                DOWNSTREAM_GRACE_SECONDS,
        },

        "orchestration":
            orchestration,

        "events":
            events,

        "bridge":
            bridge,

        "validation":
            validation,

        "provider_path": {
            "source_file": (
                str(provider_file)
                if provider_file else None
            ),
            **inspect_provider_path(
                provider_obj
            ),
        },

        "reconciliation": {
            "source_file": (
                str(reconciliation_file)
                if reconciliation_file
                else None
            ),
            **inspect_reconciliation(
                reconciliation_obj
            ),
        },

        "integrity": {
            "active_m006e2_file":
                str(ACTIVE_M006E2),

            "active_m006e2_sha256":
                current_hash,

            "accepted_m006e2_sha256":
                FROZEN_M006E2_SHA256,

            "m006e2_hash_match": (
                current_hash
                == FROZEN_M006E2_SHA256
            ),
        },

        "safety": {
            "bridge_and_validation_violation_count":
                safety_violations,

            "zero_unexplained_write_indicators":
                safety_violations == 0,
        },
    }


def output_path(day: date) -> Path:

    path = (
        OUTPUT_ROOT
        / "sessions"
        / f"m006e9a_{day.isoformat()}.json"
    )

    resolved_root = OUTPUT_ROOT.resolve()
    resolved_path = path.resolve()

    if not resolved_path.is_relative_to(
        resolved_root
    ):
        raise RuntimeError(
            "Refusing output outside M006e.9 root"
        )

    if resolved_path.is_relative_to(
        SOURCE_ROOT.resolve()
    ):
        raise RuntimeError(
            "Refusing write into authoritative evidence"
        )

    return path


def compact_line(
    result: dict[str, Any],
) -> str:

    o = result["orchestration"]
    e = result["events"]
    p = result["provider_path"]
    r = result["reconciliation"]
    i = result["integrity"]
    s = result["safety"]

    return (
        f"{result['day']} "
        f"expected={o['expected_cycles']} "
        f"observed={o['observed_cycles']} "
        f"pass={o['pass_cycles']} "
        f"skip={o['skip_cycles']} "
        f"fail={o['fail_cycles']} "
        f"unknown={o['unknown_cycles']} "
        f"coverage={o['coverage_pct']:.1f}% "
        f"events={e['authoritative_events']} "
        f"provider_events={p['events']} "
        f"recon_events={r['events']} "
        f"safety_violations="
        f"{s['bridge_and_validation_violation_count']} "
        f"hash_match={i['m006e2_hash_match']} "
        f"verdict={o['verdict']}"
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--date",
        required=True,
        help="Observation date YYYY-MM-DD",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write only beneath isolated "
            "M006E_FORWARD_OBSERVATION root"
        ),
    )

    args = parser.parse_args()

    day = date.fromisoformat(
        args.date
    )

    result = extract(day)

    if args.compact:
        print(
            compact_line(result)
        )
    else:
        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

    if args.write:
        path = output_path(day)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            f"WROTE: {path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
