#!/usr/bin/env python3

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shadow_session_packager import VERSION as PACKAGE_VERSION, canonical_hash
from shadow_session_review_dossier import (
    DossierError,
    build_dossier,
    render_markdown,
)


def make_package():
    payload = {
        "package_version": PACKAGE_VERSION,
        "session_id": "synthetic-shadow-session-001",
        "session_date_utc": "2026-10-01",
        "components": {},
        "summary": {
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
    }

    payload["package_content_sha256"] = canonical_hash(payload)
    return payload


def write_package(root, package):
    path = root / "package.json"
    path.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n"
    )
    return path


def rehash(package):
    package = dict(package)
    package.pop("package_content_sha256", None)
    package["package_content_sha256"] = canonical_hash(package)
    return package


class ShadowSessionReviewDossierTests(unittest.TestCase):

    def test_clean_session_has_no_flags(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_package(Path(td), make_package())
            dossier = build_dossier(p)

            self.assertEqual(
                dossier["review"]["machine_status"],
                "CLEAN",
            )
            self.assertEqual(
                dossier["review"]["flags"],
                [],
            )
            self.assertIsNone(
                dossier["review"]["human_disposition"]
            )
            self.assertIsNone(
                dossier["review"]["human_notes"]
            )
            self.assertEqual(
                dossier["review"]["promotion_authority"],
                "NONE",
            )

    def test_suppressed_chain_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["suppressed_chains"] = 1
            package = rehash(package)

            p = write_package(Path(td), package)
            dossier = build_dossier(p)

            self.assertIn(
                "SUPPRESSED_CHAINS_PRESENT",
                dossier["review"]["flags"],
            )
            self.assertEqual(
                dossier["review"]["machine_status"],
                "REVIEW_REQUIRED",
            )

    def test_open_position_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["final_positions"] = {
                "USDJPY": {
                    "side": "long",
                    "units": 1000,
                }
            }
            package = rehash(package)

            p = write_package(Path(td), package)
            dossier = build_dossier(p)

            self.assertIn(
                "OPEN_POSITIONS_AT_SESSION_END",
                dossier["review"]["flags"],
            )

    def test_zero_replay_events_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["replay_events"] = 0
            package["summary"]["market_evidence_records"] = 0
            package = rehash(package)

            p = write_package(Path(td), package)
            dossier = build_dossier(p)

            self.assertIn(
                "ZERO_REPLAY_EVENTS",
                dossier["review"]["flags"],
            )

    def test_market_evidence_shortfall_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["market_evidence_records"] = 1
            package = rehash(package)

            p = write_package(Path(td), package)
            dossier = build_dossier(p)

            self.assertIn(
                "MARKET_EVIDENCE_SHORTFALL",
                dossier["review"]["flags"],
            )

    def test_package_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["replay_events"] = 99

            p = write_package(Path(td), package)

            with self.assertRaises(DossierError):
                build_dossier(p)

    def test_capability_violation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["safety"]["submission_capability"] = True
            package = rehash(package)

            p = write_package(Path(td), package)

            with self.assertRaises(DossierError):
                build_dossier(p)

    def test_nonfinite_pnl_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            package = make_package()
            package["summary"]["realized_pnl_aud"] = math.inf
            package = rehash(package)

            p = write_package(Path(td), package)

            with self.assertRaises(DossierError):
                build_dossier(p)

    def test_dossier_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_package(Path(td), make_package())

            d1 = build_dossier(p)
            d2 = build_dossier(p)

            self.assertEqual(
                d1["dossier_content_sha256"],
                d2["dossier_content_sha256"],
            )

    def test_markdown_preserves_unset_human_disposition(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_package(Path(td), make_package())

            dossier = build_dossier(p)
            rendered = render_markdown(dossier)

            self.assertIn(
                "Human disposition\n\nUNSET",
                rendered,
            )
            self.assertIn(
                "Promotion authority: NONE",
                rendered,
            )


if __name__ == "__main__":
    unittest.main()
