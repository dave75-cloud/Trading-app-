#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shadow_session_packager import (
    PackageError,
    build_package,
    canonical_hash,
)


def write_json(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True) + "\n")


def write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    )


def make_fixture(root):
    accepted = root / "accepted.json"
    market = root / "market.jsonl"
    audit = root / "audit.json"
    replay = root / "replay.jsonl"
    shadow = root / "shadow.json"

    write_json(accepted, {
        "day": "2026-10-01",
        "accepted": True,
    })

    write_jsonl(market, [
        {"event_id": "e1", "leg": "entry"},
        {"event_id": "e2", "leg": "exit"},
    ])

    write_json(audit, {
        "summary": {
            "acceptance_gate_pass": True,
            "audit_records": 2,
            "automatic_promotion": False,
            "human_review_required": True,
            "network_capability": False,
            "replay_events": 2,
            "suppressed_chains": 0,
        }
    })

    write_jsonl(replay, [
        {"event_id": "e1"},
        {"event_id": "e2"},
    ])

    write_json(shadow, {
        "event_count": 2,
        "open_positions": {},
        "realized_pnl_aud": 96.156074,
        "final_equity_aud": 100096.156074,
        "network_capability": False,
        "submission_capability": False,
    })

    return accepted, market, audit, replay, shadow


class ShadowSessionPackagerTests(unittest.TestCase):

    def test_valid_package(self):
        with tempfile.TemporaryDirectory() as td:
            paths = make_fixture(Path(td))

            package = build_package(
                "synthetic-session-001",
                "2026-10-01",
                *paths,
            )

            self.assertEqual(
                package["summary"]["replay_events"],
                2,
            )
            self.assertEqual(
                package["summary"]["final_positions"],
                {},
            )
            self.assertFalse(
                package["safety"]["network_capability"]
            )
            self.assertFalse(
                package["safety"]["submission_capability"]
            )
            self.assertFalse(
                package["safety"]["automatic_promotion"]
            )
            self.assertTrue(
                package["safety"]["human_review_required"]
            )

    def test_package_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            paths = make_fixture(Path(td))

            p1 = build_package(
                "synthetic-session-001",
                "2026-10-01",
                *paths,
            )
            p2 = build_package(
                "synthetic-session-001",
                "2026-10-01",
                *paths,
            )

            self.assertEqual(
                p1["package_content_sha256"],
                p2["package_content_sha256"],
            )

    def test_package_hash_matches_payload(self):
        with tempfile.TemporaryDirectory() as td:
            paths = make_fixture(Path(td))

            package = build_package(
                "synthetic-session-001",
                "2026-10-01",
                *paths,
            )

            recorded = package.pop(
                "package_content_sha256"
            )

            self.assertEqual(
                recorded,
                canonical_hash(package),
            )

    def test_replay_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            write_jsonl(paths[3], [
                {"event_id": "e1"},
            ])

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_shadow_event_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            write_json(paths[4], {
                "event_count": 1,
                "open_positions": {},
                "realized_pnl_aud": 0.0,
                "final_equity_aud": 100000.0,
                "network_capability": False,
                "submission_capability": False,
            })

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_replay_network_capability_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            audit = json.loads(paths[2].read_text())
            audit["summary"]["network_capability"] = True
            write_json(paths[2], audit)

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_shadow_submission_capability_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            shadow = json.loads(paths[4].read_text())
            shadow["submission_capability"] = True
            write_json(paths[4], shadow)

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_automatic_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            audit = json.loads(paths[2].read_text())
            audit["summary"]["automatic_promotion"] = True
            write_json(paths[2], audit)

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_human_review_false_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = list(make_fixture(root))

            audit = json.loads(paths[2].read_text())
            audit["summary"]["human_review_required"] = False
            write_json(paths[2], audit)

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "2026-10-01",
                    *paths,
                )

    def test_invalid_session_date_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            paths = make_fixture(Path(td))

            with self.assertRaises(PackageError):
                build_package(
                    "synthetic-session-001",
                    "01-10-2026",
                    *paths,
                )


if __name__ == "__main__":
    unittest.main()
