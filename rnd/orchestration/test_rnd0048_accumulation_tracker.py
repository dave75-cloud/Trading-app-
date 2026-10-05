import unittest

import rnd0048_accumulation_tracker as t


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64


def tranche(start, end, suffix="1"):
    seeds = {
        "AUDUSD": (HASH_A[:-1] + suffix, HASH_B[:-1] + suffix),
        "EURUSD": (HASH_C[:-1] + suffix, HASH_D[:-1] + suffix),
        "GBPUSD": (HASH_E[:-1] + suffix, HASH_F[:-1] + suffix),
        "USDJPY": (HASH_B[:-1] + suffix, HASH_C[:-1] + suffix),
    }
    return {
        "candidate_id": t.CANDIDATE_ID,
        "candidate_fingerprint": t.CANDIDATE_FINGERPRINT,
        "symbols": list(t.SYMBOLS),
        "start_utc": start,
        "end_utc": end,
        "integrity_pass": True,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "hashes": {
            s: {"raw_sha256": seeds[s][0], "canonical_sha256": seeds[s][1]}
            for s in t.SYMBOLS
        },
    }


class RND0048Tests(unittest.TestCase):
    def test_initial_state_accumulating(self):
        result = t.audit_cumulative([
            tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        ])
        self.assertEqual(result["state"], "ACCUMULATING")
        self.assertFalse(result["minimum_horizon_met"])

    def test_horizon_reaches_readout_eligible(self):
        result = t.audit_cumulative([
            tranche("2026-10-05T07:25:00Z", "2027-04-03T07:25:00Z")
        ])
        self.assertEqual(result["state"], "READOUT_ELIGIBLE_PENDING_HUMAN_GATE")
        self.assertTrue(result["minimum_horizon_met"])

    def test_candidate_fingerprint_drift_rejected(self):
        r = tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        r["candidate_fingerprint"] = "0" * 64
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r])

    def test_symbol_universe_drift_rejected(self):
        r = tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        r["symbols"] = ["EURUSD", "GBPUSD", "USDJPY"]
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r])

    def test_strategy_evaluation_rejected(self):
        r = tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        r["strategy_evaluation"] = True
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r])

    def test_pre_freeze_evidence_rejected(self):
        r = tranche("2026-10-05T07:20:00Z", "2026-10-05T07:30:00Z")
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r])

    def test_overlap_rejected(self):
        r1 = tranche("2026-10-05T07:25:00Z", "2026-10-05T08:00:00Z", "1")
        r2 = tranche("2026-10-05T07:55:00Z", "2026-10-05T08:30:00Z", "2")
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r1, r2])

    def test_duplicate_hash_tuple_rejected(self):
        r1 = tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", "1")
        r2 = tranche("2026-10-05T07:35:00Z", "2026-10-05T07:45:00Z", "2")
        r2["hashes"]["AUDUSD"] = dict(r1["hashes"]["AUDUSD"])
        with self.assertRaises(t.RND0048Error):
            t.audit_cumulative([r1, r2])

    def test_authority_remains_closed(self):
        result = t.audit_cumulative([
            tranche("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        ])
        self.assertFalse(result["strategy_evaluation"])
        self.assertFalse(result["validation_classification"])
        self.assertFalse(result["reserved_final_access"])
        self.assertFalse(result["broker_writes"])
        self.assertFalse(result["capital_authority"])


if __name__ == "__main__":
    unittest.main()
