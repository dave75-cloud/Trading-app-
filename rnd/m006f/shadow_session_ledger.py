#!/usr/bin/env python3

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from shadow_session_packager import canonical_hash
from shadow_session_review_dossier import (
    VERSION as DOSSIER_VERSION,
)
from human_disposition_record import (
    VERSION as DISPOSITION_VERSION,
    ALLOWED_DISPOSITIONS,
)


VERSION = "M006f-shadow-session-ledger-v0.1"


class LedgerError(ValueError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json_file(path, role):
    path = Path(path)

    if not path.exists() or not path.is_file():
        raise LedgerError(f"{role}: file does not exist")

    raw = path.read_bytes()

    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise LedgerError(
            f"{role}: invalid JSON"
        ) from exc

    if not isinstance(value, dict):
        raise LedgerError(
            f"{role}: expected JSON object"
        )

    return value, raw


def load_verified_dossier(path):
    dossier, raw = load_json_file(path, "dossier")

    if dossier.get("dossier_version") != DOSSIER_VERSION:
        raise LedgerError(
            "dossier: unsupported version"
        )

    safety = dossier.get("safety")

    if not isinstance(safety, dict):
        raise LedgerError(
            "dossier: safety block missing"
        )

    if safety.get("network_capability") is not False:
        raise LedgerError(
            "dossier: network capability prohibited"
        )

    if safety.get("submission_capability") is not False:
        raise LedgerError(
            "dossier: submission capability prohibited"
        )

    if safety.get("automatic_promotion") is not False:
        raise LedgerError(
            "dossier: automatic promotion prohibited"
        )

    if safety.get("human_review_required") is not True:
        raise LedgerError(
            "dossier: human review must be required"
        )

    recorded = dossier.get("dossier_content_sha256")

    if not isinstance(recorded, str):
        raise LedgerError(
            "dossier: missing dossier_content_sha256"
        )

    payload = dict(dossier)
    payload.pop("dossier_content_sha256", None)

    expected = canonical_hash(payload)

    if recorded != expected:
        raise LedgerError(
            "dossier: content hash mismatch"
        )

    review = dossier.get("review")

    if not isinstance(review, dict):
        raise LedgerError(
            "dossier: review block missing"
        )

    if review.get("human_disposition") is not None:
        raise LedgerError(
            "dossier: embedded human disposition prohibited"
        )

    if review.get("promotion_authority") != "NONE":
        raise LedgerError(
            "dossier: promotion authority must be NONE"
        )

    return dossier, raw


def load_verified_disposition(path):
    record, raw = load_json_file(
        path,
        "disposition",
    )

    if record.get("record_version") != DISPOSITION_VERSION:
        raise LedgerError(
            "disposition: unsupported version"
        )

    recorded = record.get("record_content_sha256")

    if not isinstance(recorded, str):
        raise LedgerError(
            "disposition: missing record_content_sha256"
        )

    payload = dict(record)
    payload.pop("record_content_sha256", None)

    if recorded != canonical_hash(payload):
        raise LedgerError(
            "disposition: content hash mismatch"
        )

    review = record.get("human_review")
    authority = record.get("authority")
    safety = record.get("safety")

    if not isinstance(review, dict):
        raise LedgerError(
            "disposition: human_review missing"
        )

    if review.get("disposition") not in ALLOWED_DISPOSITIONS:
        raise LedgerError(
            "disposition: invalid human disposition"
        )

    if not isinstance(authority, dict):
        raise LedgerError(
            "disposition: authority missing"
        )

    if authority.get("automatic_disposition") is not False:
        raise LedgerError(
            "disposition: automatic disposition prohibited"
        )

    if authority.get("automatic_promotion") is not False:
        raise LedgerError(
            "disposition: automatic promotion prohibited"
        )

    if authority.get("promotion_authority") != "NONE":
        raise LedgerError(
            "disposition: promotion authority must be NONE"
        )

    if not isinstance(safety, dict):
        raise LedgerError(
            "disposition: safety missing"
        )

    if safety.get("network_capability") is not False:
        raise LedgerError(
            "disposition: network capability prohibited"
        )

    if safety.get("submission_capability") is not False:
        raise LedgerError(
            "disposition: submission capability prohibited"
        )

    return record, raw


def verify_pair(dossier_path, disposition_path):
    dossier, dossier_raw = load_verified_dossier(
        dossier_path
    )
    disposition, _ = load_verified_disposition(
        disposition_path
    )

    if disposition.get("session_id") != dossier.get("session_id"):
        raise LedgerError(
            "session_id mismatch"
        )

    if (
        disposition.get("session_date_utc")
        != dossier.get("session_date_utc")
    ):
        raise LedgerError(
            "session_date_utc mismatch"
        )

    source = disposition.get("source")

    if not isinstance(source, dict):
        raise LedgerError(
            "disposition: source block missing"
        )

    if (
        source.get("dossier_content_sha256")
        != dossier.get("dossier_content_sha256")
    ):
        raise LedgerError(
            "dossier-content hash binding mismatch"
        )

    if (
        source.get("dossier_file_sha256")
        != sha256_bytes(dossier_raw)
    ):
        raise LedgerError(
            "dossier-file hash binding mismatch"
        )

    facts = dossier.get("machine_facts")
    review = dossier.get("review")

    if not isinstance(facts, dict):
        raise LedgerError(
            "dossier: machine_facts missing"
        )

    if not isinstance(review, dict):
        raise LedgerError(
            "dossier: review missing"
        )

    flags = review.get("flags")

    if not isinstance(flags, list):
        raise LedgerError(
            "dossier: flags must be a list"
        )

    return {
        "session_id": dossier["session_id"],
        "session_date_utc": dossier["session_date_utc"],
        "dossier_content_sha256":
            dossier["dossier_content_sha256"],
        "disposition_content_sha256":
            disposition["record_content_sha256"],
        "disposition":
            disposition["human_review"]["disposition"],
        "reviewer_label":
            disposition["human_review"]["reviewer_label"],
        "reviewed_at_utc":
            disposition["human_review"]["reviewed_at_utc"],
        "machine_status":
            review.get("machine_status"),
        "review_flags": list(flags),
        "market_evidence_records":
            facts.get("market_evidence_records"),
        "replay_events":
            facts.get("replay_events"),
        "suppressed_chains":
            facts.get("suppressed_chains"),
        "final_positions":
            facts.get("final_positions"),
        "realized_pnl_aud":
            facts.get("realized_pnl_aud"),
        "final_equity_aud":
            facts.get("final_equity_aud"),
    }


def build_ledger(pairs):
    if not pairs:
        raise LedgerError(
            "at least one reviewed dossier/disposition pair is required"
        )

    sessions = [
        verify_pair(dossier, disposition)
        for dossier, disposition in pairs
    ]

    session_ids = [s["session_id"] for s in sessions]

    if len(session_ids) != len(set(session_ids)):
        raise LedgerError(
            "duplicate session_id in reviewed cohort"
        )

    sessions.sort(
        key=lambda x: (
            x["session_date_utc"],
            x["session_id"],
        )
    )

    dispositions = Counter(
        s["disposition"] for s in sessions
    )

    flags = Counter(
        flag
        for session in sessions
        for flag in session["review_flags"]
    )

    open_position_sessions = sum(
        1
        for s in sessions
        if s["final_positions"]
    )

    total_realized_pnl = sum(
        float(s["realized_pnl_aud"])
        for s in sessions
    )

    payload = {
        "ledger_version": VERSION,
        "reviewed_cohort_only": True,
        "sessions": sessions,
        "summary": {
            "reviewed_sessions": len(sessions),
            "accepted_sessions":
                dispositions["ACCEPTED"],
            "accepted_with_review_sessions":
                dispositions["ACCEPTED_WITH_REVIEW"],
            "rejected_sessions":
                dispositions["REJECTED"],
            "replay_events": sum(
                int(s["replay_events"])
                for s in sessions
            ),
            "market_evidence_records": sum(
                int(s["market_evidence_records"])
                for s in sessions
            ),
            "suppressed_chains": sum(
                int(s["suppressed_chains"])
                for s in sessions
            ),
            "sessions_with_open_positions":
                open_position_sessions,
            "review_flag_counts": dict(
                sorted(flags.items())
            ),
            "total_realized_pnl_aud":
                total_realized_pnl,
            "final_equity_observations_aud": [
                s["final_equity_aud"]
                for s in sessions
            ],
        },
        "integrity": {
            "all_sessions_have_verified_human_disposition": True,
            "duplicate_session_ids": False,
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_disposition": False,
            "automatic_promotion": False,
            "promotion_authority": "NONE",
        },
    }

    payload["ledger_content_sha256"] = canonical_hash(
        payload
    )

    return payload


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--pair",
        nargs=2,
        action="append",
        metavar=("DOSSIER", "DISPOSITION"),
        required=True,
    )
    ap.add_argument(
        "--output",
        required=True,
    )

    args = ap.parse_args()

    output = Path(args.output)

    if output.exists():
        raise LedgerError(
            "output already exists; refusing overwrite"
        )

    ledger = build_ledger(args.pair)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            ledger,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print("M006F_SHADOW_SESSION_LEDGER: PASS")
    print(
        "reviewed_sessions="
        + str(ledger["summary"]["reviewed_sessions"])
    )
    print(
        "accepted_sessions="
        + str(ledger["summary"]["accepted_sessions"])
    )
    print(
        "accepted_with_review_sessions="
        + str(
            ledger["summary"][
                "accepted_with_review_sessions"
            ]
        )
    )
    print(
        "rejected_sessions="
        + str(ledger["summary"]["rejected_sessions"])
    )
    print("automatic_disposition=FALSE")
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")


if __name__ == "__main__":
    main()
