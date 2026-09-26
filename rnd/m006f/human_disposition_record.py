#!/usr/bin/env python3

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from shadow_session_packager import canonical_hash
from shadow_session_review_dossier import (
    VERSION as DOSSIER_VERSION,
)


VERSION = "M006f-human-disposition-v0.1"

ALLOWED_DISPOSITIONS = {
    "ACCEPTED",
    "ACCEPTED_WITH_REVIEW",
    "REJECTED",
}


class DispositionError(ValueError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def require_utc_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise DispositionError(
            "reviewed_at_utc is required"
        )

    text = value.strip().replace("Z", "+00:00")

    try:
        ts = datetime.fromisoformat(text)
    except ValueError as exc:
        raise DispositionError(
            "reviewed_at_utc must be ISO-8601"
        ) from exc

    if ts.tzinfo is None:
        raise DispositionError(
            "reviewed_at_utc must include UTC timezone"
        )

    if ts.utcoffset().total_seconds() != 0:
        raise DispositionError(
            "reviewed_at_utc must be UTC"
        )

    return value.strip()


def load_verified_dossier(path):
    path = Path(path)

    if not path.exists() or not path.is_file():
        raise DispositionError(
            "dossier file does not exist"
        )

    raw = path.read_bytes()

    try:
        dossier = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise DispositionError(
            "dossier is invalid JSON"
        ) from exc

    if not isinstance(dossier, dict):
        raise DispositionError(
            "dossier must be a JSON object"
        )

    if dossier.get("dossier_version") != DOSSIER_VERSION:
        raise DispositionError(
            "unsupported dossier version"
        )

    recorded = dossier.get(
        "dossier_content_sha256"
    )

    if not isinstance(recorded, str):
        raise DispositionError(
            "missing dossier_content_sha256"
        )

    payload = dict(dossier)
    payload.pop("dossier_content_sha256", None)

    expected = canonical_hash(payload)

    if recorded != expected:
        raise DispositionError(
            "dossier-content SHA-256 mismatch"
        )

    review = dossier.get("review")

    if not isinstance(review, dict):
        raise DispositionError(
            "dossier review block missing"
        )

    if review.get("human_disposition") is not None:
        raise DispositionError(
            "source dossier human disposition must be unset"
        )

    if review.get("promotion_authority") != "NONE":
        raise DispositionError(
            "source dossier promotion authority must be NONE"
        )

    return dossier, raw


def build_record(
    dossier_path,
    disposition,
    reviewer_label,
    reviewed_at_utc,
    human_notes=None,
):
    dossier, raw = load_verified_dossier(
        dossier_path
    )

    disposition = str(disposition).strip().upper()

    if disposition not in ALLOWED_DISPOSITIONS:
        raise DispositionError(
            "unsupported human disposition"
        )

    reviewer_label = str(reviewer_label).strip()

    if not reviewer_label:
        raise DispositionError(
            "reviewer_label is required"
        )

    reviewed_at_utc = require_utc_timestamp(
        reviewed_at_utc
    )

    if human_notes is not None:
        human_notes = str(human_notes).strip()
        if not human_notes:
            human_notes = None

    record = {
        "record_version": VERSION,
        "session_id": dossier.get("session_id"),
        "session_date_utc": dossier.get(
            "session_date_utc"
        ),
        "source": {
            "dossier_content_sha256": dossier.get(
                "dossier_content_sha256"
            ),
            "dossier_file_sha256": sha256_bytes(raw),
        },
        "human_review": {
            "disposition": disposition,
            "reviewer_label": reviewer_label,
            "reviewed_at_utc": reviewed_at_utc,
            "notes": human_notes,
        },
        "authority": {
            "automatic_disposition": False,
            "automatic_promotion": False,
            "promotion_authority": "NONE",
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
        },
    }

    record["record_content_sha256"] = canonical_hash(
        record
    )

    return record


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--dossier",
        required=True,
    )
    ap.add_argument(
        "--disposition",
        required=True,
        choices=sorted(ALLOWED_DISPOSITIONS),
    )
    ap.add_argument(
        "--reviewer-label",
        required=True,
    )
    ap.add_argument(
        "--reviewed-at-utc",
        required=True,
    )
    ap.add_argument(
        "--notes",
        default=None,
    )
    ap.add_argument(
        "--output",
        required=True,
    )

    args = ap.parse_args()

    output = Path(args.output)

    if output.exists():
        raise DispositionError(
            "output already exists; refusing overwrite"
        )

    record = build_record(
        dossier_path=args.dossier,
        disposition=args.disposition,
        reviewer_label=args.reviewer_label,
        reviewed_at_utc=args.reviewed_at_utc,
        human_notes=args.notes,
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            record,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print("M006F_HUMAN_DISPOSITION_RECORD: PASS")
    print(
        "disposition="
        + record["human_review"]["disposition"]
    )
    print("automatic_disposition=FALSE")
    print("automatic_promotion=FALSE")
    print("promotion_authority=NONE")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")


if __name__ == "__main__":
    main()
