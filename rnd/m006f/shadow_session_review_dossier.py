#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
from pathlib import Path

from shadow_session_packager import (
    VERSION as PACKAGE_VERSION,
    canonical_hash,
)


VERSION = "M006f-shadow-session-review-dossier-v0.1"


class DossierError(ValueError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def finite_number(value, name):
    if isinstance(value, bool):
        raise DossierError(f"{name} must be numeric")

    try:
        x = float(value)
    except (TypeError, ValueError):
        raise DossierError(f"{name} must be numeric")

    if not math.isfinite(x):
        raise DossierError(f"{name} must be finite")

    return x


def nonnegative_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise DossierError(
            f"{name} must be a non-negative integer"
        )

    if value < 0:
        raise DossierError(
            f"{name} must be a non-negative integer"
        )

    return value


def load_verified_package(path):
    path = Path(path)

    if not path.exists() or not path.is_file():
        raise DossierError(
            "source package manifest does not exist"
        )

    raw = path.read_bytes()

    try:
        package = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise DossierError(
            "source package manifest is invalid JSON"
        ) from exc

    if not isinstance(package, dict):
        raise DossierError(
            "source package manifest must be an object"
        )

    if package.get("package_version") != PACKAGE_VERSION:
        raise DossierError(
            "unsupported package version"
        )

    recorded_hash = package.get(
        "package_content_sha256"
    )

    if not isinstance(recorded_hash, str):
        raise DossierError(
            "missing package_content_sha256"
        )

    payload = dict(package)
    payload.pop("package_content_sha256", None)

    expected_hash = canonical_hash(payload)

    if recorded_hash != expected_hash:
        raise DossierError(
            "package-content SHA-256 mismatch"
        )

    return package, raw


def build_dossier(package_path):
    package, package_raw = load_verified_package(
        package_path
    )

    summary = package.get("summary")
    safety = package.get("safety")

    if not isinstance(summary, dict):
        raise DossierError("package summary is missing")

    if not isinstance(safety, dict):
        raise DossierError("package safety is missing")

    if safety.get("network_capability") is not False:
        raise DossierError(
            "source package reports network capability"
        )

    if safety.get("submission_capability") is not False:
        raise DossierError(
            "source package reports submission capability"
        )

    if safety.get("automatic_promotion") is not False:
        raise DossierError(
            "source package reports automatic promotion"
        )

    if safety.get("human_review_required") is not True:
        raise DossierError(
            "source package must require human review"
        )

    market_records = nonnegative_int(
        summary.get("market_evidence_records"),
        "market_evidence_records",
    )

    replay_events = nonnegative_int(
        summary.get("replay_events"),
        "replay_events",
    )

    replay_audit_records = nonnegative_int(
        summary.get("replay_audit_records"),
        "replay_audit_records",
    )

    suppressed_chains = nonnegative_int(
        summary.get("suppressed_chains"),
        "suppressed_chains",
    )

    final_positions = summary.get("final_positions")

    if not isinstance(final_positions, dict):
        raise DossierError(
            "final_positions must be an object"
        )

    realized_pnl = finite_number(
        summary.get("realized_pnl_aud"),
        "realized_pnl_aud",
    )

    final_equity = finite_number(
        summary.get("final_equity_aud"),
        "final_equity_aud",
    )

    flags = []

    if replay_events == 0:
        flags.append("ZERO_REPLAY_EVENTS")

    if suppressed_chains > 0:
        flags.append("SUPPRESSED_CHAINS_PRESENT")

    if final_positions:
        flags.append("OPEN_POSITIONS_AT_SESSION_END")

    if market_records < replay_events:
        flags.append("MARKET_EVIDENCE_SHORTFALL")

    machine_status = (
        "CLEAN"
        if not flags
        else "REVIEW_REQUIRED"
    )

    dossier = {
        "dossier_version": VERSION,
        "session_id": package.get("session_id"),
        "session_date_utc": package.get(
            "session_date_utc"
        ),
        "source": {
            "package_version": package.get(
                "package_version"
            ),
            "package_content_sha256": package.get(
                "package_content_sha256"
            ),
            "package_manifest_sha256": sha256_bytes(
                package_raw
            ),
        },
        "machine_facts": {
            "market_evidence_records": market_records,
            "replay_events": replay_events,
            "replay_audit_records": replay_audit_records,
            "suppressed_chains": suppressed_chains,
            "final_positions": final_positions,
            "realized_pnl_aud": realized_pnl,
            "final_equity_aud": final_equity,
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_promotion": False,
            "human_review_required": True,
        },
        "review": {
            "machine_status": machine_status,
            "flags": flags,
            "human_disposition": None,
            "human_notes": None,
            "promotion_authority": "NONE",
        },
    }

    dossier["dossier_content_sha256"] = canonical_hash(
        dossier
    )

    return dossier


def render_markdown(dossier):
    facts = dossier["machine_facts"]
    safety = dossier["safety"]
    review = dossier["review"]

    flags = review["flags"]

    if flags:
        flag_text = "\n".join(
            f"- {flag}" for flag in flags
        )
    else:
        flag_text = "- NONE"

    positions = json.dumps(
        facts["final_positions"],
        sort_keys=True,
    )

    return f"""# M006f Shadow-Session Review Dossier

## Session

- Session ID: {dossier["session_id"]}
- UTC session date: {dossier["session_date_utc"]}
- Machine status: {review["machine_status"]}

## Integrity

- Package content SHA-256: {dossier["source"]["package_content_sha256"]}
- Package manifest SHA-256: {dossier["source"]["package_manifest_sha256"]}
- Dossier content SHA-256: {dossier["dossier_content_sha256"]}

## Machine facts

- Market-evidence records: {facts["market_evidence_records"]}
- Replay events: {facts["replay_events"]}
- Replay-audit records: {facts["replay_audit_records"]}
- Suppressed chains: {facts["suppressed_chains"]}
- Final positions: {positions}
- Realized shadow P&L (AUD): {facts["realized_pnl_aud"]}
- Final shadow equity (AUD): {facts["final_equity_aud"]}

## Review flags

{flag_text}

## Safety

- Network capability: {str(safety["network_capability"]).lower()}
- Submission capability: {str(safety["submission_capability"]).lower()}
- Automatic promotion: {str(safety["automatic_promotion"]).lower()}
- Human review required: {str(safety["human_review_required"]).lower()}
- Promotion authority: {review["promotion_authority"]}

## Human disposition

UNSET

Human notes: UNSET
"""


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--package",
        required=True,
    )
    ap.add_argument(
        "--json-output",
        required=True,
    )
    ap.add_argument(
        "--markdown-output",
        required=True,
    )

    args = ap.parse_args()

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)

    if json_output.exists():
        raise DossierError(
            "JSON output already exists; refusing overwrite"
        )

    if markdown_output.exists():
        raise DossierError(
            "Markdown output already exists; refusing overwrite"
        )

    dossier = build_dossier(args.package)

    json_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    markdown_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_output.write_text(
        json.dumps(
            dossier,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    markdown_output.write_text(
        render_markdown(dossier)
    )

    print("M006F_SHADOW_SESSION_REVIEW_DOSSIER: PASS")
    print(
        "machine_status="
        + dossier["review"]["machine_status"]
    )
    print(
        "review_flags="
        + str(len(dossier["review"]["flags"]))
    )
    print("human_disposition=UNSET")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")


if __name__ == "__main__":
    main()
