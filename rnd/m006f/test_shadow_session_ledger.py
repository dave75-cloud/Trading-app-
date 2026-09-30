#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from human_disposition_record import build_record
from shadow_session_ledger import LedgerError, build_ledger
from shadow_session_packager import canonical_hash
from shadow_session_review_dossier import VERSION as DOSSIER_VERSION


def make_dossier(session_id="session-001", session_date="2026-10-01"):
    d = {
        "dossier_version": DOSSIER_VERSION,
        "session_id": session_id,
        "session_date_utc": session_date,
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
            "realized_pnl_aud": 10.0,
            "final_equity_aud": 100010.0,
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

    d["dossier_content_sha256"] = canonical_hash(d)
    return d


def rehash(obj, field):
    obj = dict(obj)
    obj.pop(field, None)
    obj[field] = canonical_hash(obj)
    return obj


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def make_pair(
    root,
    session_id="session-001",
    session_date="2026-10-01",
    disposition="ACCEPTED",
):
    dossier = make_dossier(session_id, session_date)

    dossier_path = root / f"{session_id}-dossier.json"
    write_json(dossier_path, dossier)

    record = build_record(
        dossier_path,
        disposition,
        "human-reviewer",
        f"{session_date}T15:00:00Z",
    )

    disposition_path = root / f"{session_id}-disposition.json"
    write_json(disposition_path, record)

    return dossier_path, disposition_path


class ShadowSessionLedgerTests(unittest.TestCase):

    def test_valid_accepted_session(self):
        with tempfile.TemporaryDirectory() as td:
            pair = make_pair(Path(td))
            ledger = build_ledger([pair])

            self.assertEqual(
                ledger["summary"]["reviewed_sessions"], 1
            )
            self.assertEqual(
                ledger["summary"]["accepted_sessions"], 1
            )
            self.assertTrue(
                ledger["integrity"][
                    "all_sessions_have_verified_human_disposition"
                ]
            )
            self.assertFalse(
                ledger["safety"]["automatic_promotion"]
            )

    def test_all_dispositions_aggregate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            pairs = [
                make_pair(
                    root,
                    "session-001",
                    "2026-10-01",
                    "ACCEPTED",
                ),
                make_pair(
                    root,
                    "session-002",
                    "2026-10-02",
                    "ACCEPTED_WITH_REVIEW",
                ),
                make_pair(
                    root,
                    "session-003",
                    "2026-10-03",
                    "REJECTED",
                ),
            ]

            ledger = build_ledger(pairs)
            s = ledger["summary"]

            self.assertEqual(s["reviewed_sessions"], 3)
            self.assertEqual(s["accepted_sessions"], 1)
            self.assertEqual(
                s["accepted_with_review_sessions"], 1
            )
            self.assertEqual(s["rejected_sessions"], 1)
            self.assertEqual(s["replay_events"], 6)

    def test_duplicate_session_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pair = make_pair(root)

            with self.assertRaises(LedgerError):
                build_ledger([pair, pair])

    def test_empty_cohort_rejected(self):
        with self.assertRaises(LedgerError):
            build_ledger([])

    def test_modified_dossier_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dossier_path, disposition_path = make_pair(root)

            dossier = json.loads(dossier_path.read_text())
            dossier["machine_facts"]["replay_events"] = 99
            write_json(dossier_path, dossier)

            with self.assertRaises(LedgerError):
                build_ledger([
                    (dossier_path, disposition_path)
                ])

    def test_modified_disposition_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dossier_path, disposition_path = make_pair(root)

            record = json.loads(disposition_path.read_text())
            record["human_review"]["disposition"] = "REJECTED"
            write_json(disposition_path, record)

            with self.assertRaises(LedgerError):
                build_ledger([
                    (dossier_path, disposition_path)
                ])

    def test_wrong_dossier_binding_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            d1, r1 = make_pair(
                root,
                "session-001",
                "2026-10-01",
            )
            d2, _ = make_pair(
                root,
                "session-002",
                "2026-10-02",
            )

            with self.assertRaises(LedgerError):
                build_ledger([(d2, r1)])

    def test_dossier_capability_violation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dossier_path, disposition_path = make_pair(root)

            dossier = json.loads(dossier_path.read_text())
            dossier["safety"]["network_capability"] = True
            dossier = rehash(
                dossier,
                "dossier_content_sha256",
            )
            write_json(dossier_path, dossier)

            with self.assertRaises(LedgerError):
                build_ledger([
                    (dossier_path, disposition_path)
                ])

    def test_review_flags_aggregate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            dossier = make_dossier()
            dossier["review"]["machine_status"] = "REVIEW_REQUIRED"
            dossier["review"]["flags"] = [
                "SUPPRESSED_CHAINS_PRESENT"
            ]
            dossier["machine_facts"]["suppressed_chains"] = 1
            dossier = rehash(
                dossier,
                "dossier_content_sha256",
            )

            dossier_path = root / "dossier.json"
            write_json(dossier_path, dossier)

            record = build_record(
                dossier_path,
                "ACCEPTED_WITH_REVIEW",
                "human-reviewer",
                "2026-10-01T15:00:00Z",
            )

            disposition_path = root / "disposition.json"
            write_json(disposition_path, record)

            ledger = build_ledger([
                (dossier_path, disposition_path)
            ])

            self.assertEqual(
                ledger["summary"]["review_flag_counts"],
                {"SUPPRESSED_CHAINS_PRESENT": 1},
            )
            self.assertEqual(
                ledger["summary"]["suppressed_chains"], 1
            )

    def test_ledger_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            pair = make_pair(Path(td))

            a = build_ledger([pair])
            b = build_ledger([pair])

            self.assertEqual(
                a["ledger_content_sha256"],
                b["ledger_content_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
