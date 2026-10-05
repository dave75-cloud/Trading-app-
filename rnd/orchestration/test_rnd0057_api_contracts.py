import unittest

from rnd0057_api_contracts import (
    APIContractError,
    CANDIDATE_FINGERPRINT,
    authority_map,
    candidate_identity,
    control_envelope,
    human_authority_receipt,
)


def candidate():
    return {
        "candidate_id": "Q003",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"],
    }


def receipt(**overrides):
    out = {
        "receipt_id": "human-1",
        "action": "AUTHORIZE_SHADOW",
        "from_state": "VALIDATION_SUPPORTED",
        "to_state": "SHADOW_ELIGIBLE",
        "human_authorized": True,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
    }
    out.update(overrides)
    return out


def envelope(**overrides):
    out = {
        "candidate": candidate(),
        "state": "VALIDATION_SUPPORTED",
        "authority": {},
        "human_receipt": None,
        "broker_writes": False,
        "capital_authority": False,
        "live_environment": False,
    }
    out.update(overrides)
    return out


class TestRND0057APIContracts(unittest.TestCase):
    def test_candidate_identity_passes(self):
        self.assertEqual(candidate_identity(candidate())["candidate_id"], "Q003")

    def test_candidate_extra_field_fails(self):
        bad = candidate(); bad["x"] = 1
        with self.assertRaises(APIContractError):
            candidate_identity(bad)

    def test_unknown_authority_field_fails(self):
        with self.assertRaises(APIContractError):
            authority_map({"magic": True})

    def test_missing_authority_defaults_false(self):
        self.assertTrue(all(v is False for v in authority_map({}).values()))

    def test_human_receipt_requires_true(self):
        with self.assertRaises(APIContractError):
            human_authority_receipt(receipt(human_authorized=False))

    def test_human_receipt_candidate_binding(self):
        with self.assertRaises(APIContractError):
            human_authority_receipt(receipt(candidate_fingerprint="0" * 64))

    def test_pre_execution_broker_authority_rejected(self):
        with self.assertRaises(APIContractError):
            control_envelope(envelope(authority={"broker_writes_authorized": True}))

    def test_payload_cannot_assert_broker_write(self):
        with self.assertRaises(APIContractError):
            control_envelope(envelope(broker_writes=True))

    def test_valid_envelope_stays_zero_write(self):
        out = control_envelope(envelope(human_receipt=receipt()))
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["live_environment"])


if __name__ == "__main__":
    unittest.main()
