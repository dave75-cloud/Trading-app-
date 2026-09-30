#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from human_disposition_record import (
    DispositionError,
    build_record,
)
from shadow_session_packager import canonical_hash
from shadow_session_review_dossier import VERSION as DOSSIER_VERSION


def make_dossier():
    payload = {
        "dossier_version": DOSSIER_VERSION,
        "session_id": "synthetic-shadow-session-001",
        "session_date_utc": "2026-10-01",
        "source": {
            "package_version": "synthetic",
            "package_content_sha256": "a" * 64,
            "package_manifest_sha256": "b" * 64,
        },
        "machine_facts": {
            "market_evidence_records": 2,
            "replay_events": 2,
            "replay_audit_records": 2,
            "suppressed_chains": 0,
            "final_positions": {},
            "realized_pnl_aud": 96.156074,
            "final_equity_aud": 100096.156074,
        },
        "safety": {
            "network_capability": False,
            "submission_capability": False,
            "automatic_promotion": False,
            "human_review_required": True,
        },
        "review": {
            "machine_status": "CLEAN",
            "flags": [],
            "human_disposition": None,
            "human_notes": None,
            "promotion_authority": "NONE",
        },
    }

    payload["dossier_content_sha256"] = canonical_hash(payload)
    return payload


def write_dossier(root, dossier):
    path = root / "dossier.json"
    path.write_text(
        json.dumps(dossier, indent=2, sort_keys=True) + "\n"
    )
    return path


def rehash(dossier):
    dossier = dict(dossier)
    dossier.pop("dossier_content_sha256", None)
    dossier["dossier_content_sha256"] = canonical_hash(dossier)
    return dossier


class HumanDispositionRecordTests(unittest.TestCase):

    def test_explicit_acceptance_record(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            record = build_record(
                path,
                "ACCEPTED",
                "human-reviewer",
                "2026-10-01T15:00:00Z",
            )

            self.assertEqual(
                record["human_review"]["disposition"],
                "ACCEPTED",
            )
            self.assertFalse(
                record["authority"]["automatic_disposition"]
            )
            self.assertFalse(
                record["authority"]["automatic_promotion"]
            )
            self.assertEqual(
                record["authority"]["promotion_authority"],
                "NONE",
            )

    def test_accepted_with_review_supported(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            record = build_record(
                path,
                "ACCEPTED_WITH_REVIEW",
                "human-reviewer",
                "2026-10-01T15:00:00+00:00",
                "Synthetic review note",
            )

            self.assertEqual(
                record["human_review"]["disposition"],
                "ACCEPTED_WITH_REVIEW",
            )

    def test_rejected_supported(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            record = build_record(
                path,
                "REJECTED",
                "human-reviewer",
                "2026-10-01T15:00:00Z",
            )

            self.assertEqual(
                record["human_review"]["disposition"],
                "REJECTED",
            )

    def test_unsupported_disposition_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            with self.assertRaises(DispositionError):
                build_record(
                    path,
                    "AUTO_ACCEPT",
                    "human-reviewer",
                    "2026-10-01T15:00:00Z",
                )

    def test_modified_dossier_fails_hash_check(self):
        with tempfile.TemporaryDirectory() as td:
            dossier = make_dossier()
            path = write_dossier(Path(td), dossier)

            altered = json.loads(path.read_text())
            altered["review"]["machine_status"] = "REVIEW_REQUIRED"
            path.write_text(
                json.dumps(altered, indent=2, sort_keys=True) + "\n"
            )

            with self.assertRaises(DispositionError):
                build_record(
                    path,
                    "ACCEPTED",
                    "human-reviewer",
                    "2026-10-01T15:00:00Z",
                )

    def test_reviewer_label_required(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            with self.assertRaises(DispositionError):
                build_record(
                    path,
                    "ACCEPTED",
                    "",
                    "2026-10-01T15:00:00Z",
                )

    def test_non_utc_review_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            with self.assertRaises(DispositionError):
                build_record(
                    path,
                    "ACCEPTED",
                    "human-reviewer",
                    "2026-10-02T01:00:00+10:00",
                )

    def test_source_dossier_cannot_already_have_disposition(self):
        with tempfile.TemporaryDirectory() as td:
            dossier = make_dossier()
            dossier["review"]["human_disposition"] = "ACCEPTED"
            dossier = rehash(dossier)

            path = write_dossier(Path(td), dossier)

            with self.assertRaises(DispositionError):
                build_record(
                    path,
                    "ACCEPTED",
                    "human-reviewer",
                    "2026-10-01T15:00:00Z",
                )

    def test_record_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_dossier(Path(td), make_dossier())

            r1 = build_record(
                path,
                "ACCEPTED",
                "human-reviewer",
                "2026-10-01T15:00:00Z",
            )

            r2 = build_record(
                path,
                "ACCEPTED",
                "human-reviewer",
                "2026-10-01T15:00:00Z",
            )

            self.assertEqual(
                r1["record_content_sha256"],
                r2["record_content_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
