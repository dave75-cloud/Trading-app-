import unittest

from rnd0059_governance_guard import GovernanceError, validate_integration_manifest

TRACKS = {
    "RND-0055": {"status": "VERIFIED", "verification_commit": "e3b7032611b10815bbd943a93295736d63ea23b2", "broker_writes": False, "capital_authority": False},
    "RND-0056": {"status": "VERIFIED", "verification_commit": "9e583b229dda3b483647b94fba7270a0e3341591", "broker_writes": False, "capital_authority": False},
    "RND-0057": {"status": "VERIFIED", "verification_commit": "8d30fdd6fcb7ac890126f4ed0ae685b6da30f793", "broker_writes": False, "capital_authority": False},
    "RND-0058": {"status": "VERIFIED", "verification_commit": "ba5003f31fb35864a87236de42f16c3ac37844f3", "broker_writes": False, "capital_authority": False},
}


def manifest(**overrides):
    out = {
        "tracks": {k: dict(v) for k, v in TRACKS.items()},
        "automatic_merge": False,
        "automatic_promotion": False,
        "broker_writes": False,
        "capital_authority": False,
        "reserved_final_access": False,
    }
    out.update(overrides)
    return out


class TestRND0059GovernanceGuard(unittest.TestCase):
    def test_verified_manifest_passes(self):
        out = validate_integration_manifest(manifest())
        self.assertEqual(out["status"], "INTEGRATION_READY_FOR_HUMAN_REVIEW")

    def test_missing_track_fails(self):
        m = manifest(); del m["tracks"]["RND-0058"]
        with self.assertRaises(GovernanceError): validate_integration_manifest(m)

    def test_unverified_track_fails(self):
        m = manifest(); m["tracks"]["RND-0056"]["status"] = "UNVERIFIED"
        with self.assertRaises(GovernanceError): validate_integration_manifest(m)

    def test_bad_commit_fails(self):
        m = manifest(); m["tracks"]["RND-0057"]["verification_commit"] = "bad"
        with self.assertRaises(GovernanceError): validate_integration_manifest(m)

    def test_track_broker_escalation_fails(self):
        m = manifest(); m["tracks"]["RND-0055"]["broker_writes"] = True
        with self.assertRaises(GovernanceError): validate_integration_manifest(m)

    def test_global_auto_merge_fails(self):
        with self.assertRaises(GovernanceError): validate_integration_manifest(manifest(automatic_merge=True))

    def test_reserved_final_access_fails(self):
        with self.assertRaises(GovernanceError): validate_integration_manifest(manifest(reserved_final_access=True))


if __name__ == "__main__":
    unittest.main()
