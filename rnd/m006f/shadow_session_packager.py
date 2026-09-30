#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path


VERSION = "M006f-shadow-session-package-v0.1"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class PackageError(ValueError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def read_file(path, role):
    path = Path(path)

    if not path.exists():
        raise PackageError(f"{role}: file does not exist")

    if not path.is_file():
        raise PackageError(f"{role}: not a regular file")

    raw = path.read_bytes()

    return {
        "path": path,
        "raw": raw,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
    }


def read_json(component, role):
    try:
        value = json.loads(
            component["raw"].decode("utf-8")
        )
    except Exception as exc:
        raise PackageError(
            f"{role}: invalid JSON"
        ) from exc

    if not isinstance(value, dict):
        raise PackageError(
            f"{role}: expected JSON object"
        )

    return value


def read_jsonl(component, role):
    rows = []

    for line_number, raw_line in enumerate(
        component["raw"].decode("utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        try:
            value = json.loads(line)
        except Exception as exc:
            raise PackageError(
                f"{role}: invalid JSONL line {line_number}"
            ) from exc

        if not isinstance(value, dict):
            raise PackageError(
                f"{role}: line {line_number} is not an object"
            )

        rows.append(value)

    return rows


def component_manifest(component):
    return {
        "source_label": component["path"].name,
        "size_bytes": component["size_bytes"],
        "sha256": component["sha256"],
    }


def canonical_hash(payload):
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return sha256_bytes(raw)


def build_package(
    session_id,
    session_date_utc,
    accepted_session_path,
    market_evidence_path,
    replay_audit_path,
    replay_events_path,
    shadow_result_path,
):
    session_id = str(session_id).strip()

    if not session_id:
        raise PackageError("session_id is required")

    if not DATE_RE.match(str(session_date_utc)):
        raise PackageError(
            "session_date_utc must be YYYY-MM-DD"
        )

    components = {
        "accepted_session": read_file(
            accepted_session_path,
            "accepted_session",
        ),
        "market_evidence": read_file(
            market_evidence_path,
            "market_evidence",
        ),
        "replay_audit": read_file(
            replay_audit_path,
            "replay_audit",
        ),
        "replay_events": read_file(
            replay_events_path,
            "replay_events",
        ),
        "shadow_result": read_file(
            shadow_result_path,
            "shadow_result",
        ),
    }

    # Parse all required artifacts so malformed evidence fails closed.
    read_json(
        components["accepted_session"],
        "accepted_session",
    )

    market_rows = read_jsonl(
        components["market_evidence"],
        "market_evidence",
    )

    replay_audit = read_json(
        components["replay_audit"],
        "replay_audit",
    )

    replay_rows = read_jsonl(
        components["replay_events"],
        "replay_events",
    )

    shadow_result = read_json(
        components["shadow_result"],
        "shadow_result",
    )

    summary = replay_audit.get("summary")
    if not isinstance(summary, dict):
        raise PackageError(
            "replay_audit: missing summary"
        )

    if summary.get("acceptance_gate_pass") is not True:
        raise PackageError(
            "replay acceptance gate did not pass"
        )

    if summary.get("network_capability") is not False:
        raise PackageError(
            "replay audit reports network capability"
        )

    if summary.get("automatic_promotion") is not False:
        raise PackageError(
            "replay audit reports automatic promotion"
        )

    if summary.get("human_review_required") is not True:
        raise PackageError(
            "replay audit must require human review"
        )

    audit_replay_events = summary.get("replay_events")

    if audit_replay_events != len(replay_rows):
        raise PackageError(
            "replay-event count mismatch"
        )

    if shadow_result.get("event_count") != len(replay_rows):
        raise PackageError(
            "shadow-result event count mismatch"
        )

    if shadow_result.get("network_capability") is not False:
        raise PackageError(
            "shadow result reports network capability"
        )

    if shadow_result.get("submission_capability") is not False:
        raise PackageError(
            "shadow result reports submission capability"
        )

    payload = {
        "package_version": VERSION,
        "session_id": session_id,
        "session_date_utc": session_date_utc,
        "components": {
            name: component_manifest(component)
            for name, component in components.items()
        },
        "summary": {
            "market_evidence_records": len(market_rows),
            "replay_events": len(replay_rows),
            "replay_audit_records": summary.get(
                "audit_records"
            ),
            "suppressed_chains": summary.get(
                "suppressed_chains"
            ),
            "final_positions": shadow_result.get(
                "open_positions"
            ),
            "realized_pnl_aud": shadow_result.get(
                "realized_pnl_aud"
            ),
            "final_equity_aud": shadow_result.get(
                "final_equity_aud"
            ),
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_promotion": False,
            "human_review_required": True,
        },
    }

    payload["package_content_sha256"] = canonical_hash(
        payload
    )

    return payload


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--session-id", required=True)
    ap.add_argument("--session-date-utc", required=True)
    ap.add_argument("--accepted-session", required=True)
    ap.add_argument("--market-evidence", required=True)
    ap.add_argument("--replay-audit", required=True)
    ap.add_argument("--replay-events", required=True)
    ap.add_argument("--shadow-result", required=True)
    ap.add_argument("--output", required=True)

    args = ap.parse_args()

    output = Path(args.output)

    if output.exists():
        raise PackageError(
            "output already exists; refusing overwrite"
        )

    package = build_package(
        session_id=args.session_id,
        session_date_utc=args.session_date_utc,
        accepted_session_path=args.accepted_session,
        market_evidence_path=args.market_evidence,
        replay_audit_path=args.replay_audit,
        replay_events_path=args.replay_events,
        shadow_result_path=args.shadow_result,
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            package,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print("M006F_SHADOW_SESSION_PACKAGE: PASS")
    print(f"session_id={package['session_id']}")
    print(
        "package_content_sha256="
        + package["package_content_sha256"]
    )
    print("network_capability=FALSE")
    print("submission_capability=FALSE")
    print("automatic_promotion=FALSE")
    print("human_review_required=TRUE")


if __name__ == "__main__":
    main()
