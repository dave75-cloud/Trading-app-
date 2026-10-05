import unittest

from rnd0054_ledger import audit_and_advance, RND0054LedgerError, CANDIDATE_FINGERPRINT, SYMBOLS


def hashes(seed):
    out = {}
    for i, symbol in enumerate(SYMBOLS):
        a = f"{seed + i:064x}"[-64:]
        b = f"{seed + 100 + i:064x}"[-64:]
        out[symbol] = {"raw_sha256": a, "canonical_sha256": b}
    return out


def record(start, end, seed=1, **overrides):
    base = {
        "candidate_id": "Q003",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "start_utc": start,
        "end_utc": end,
        "integrity_pass": True,
        "hashes": hashes(seed),
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
    base.update(overrides)
    return base


class TestRND0054Ledger(unittest.TestCase):
    def test_single_first_tranche_accumulating(self):
        out = audit_and_advance([
            record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z")
        ])
        self.assertEqual(out["state"], "ACCUMULATING")
        self.assertEqual(out["tranche_count"], 1)

    def test_exact_contiguous_second_tranche(self):
        out = audit_and_advance([
            record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", 1),
            record("2026-10-05T07:35:00Z", "2026-10-12T07:35:00Z", 1000),
        ])
        self.assertEqual(out["cumulative_end_utc"], "2026-10-12T07:35:00Z")

    def test_gap_between_tranches_fails(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", 1),
                record("2026-10-05T07:40:00Z", "2026-10-12T07:40:00Z", 1000),
            ])

    def test_overlap_fails(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", 1),
                record("2026-10-05T07:30:00Z", "2026-10-12T07:30:00Z", 1000),
            ])

    def test_first_start_drift_fails(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:30:00Z", "2026-10-05T07:40:00Z", 1)
            ])

    def test_duplicate_hash_tuple_fails(self):
        shared = hashes(1)
        r1 = record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", 1, hashes=shared)
        r2 = record("2026-10-05T07:35:00Z", "2026-10-12T07:35:00Z", 2, hashes=shared)
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([r1, r2])

    def test_authority_escalation_fails(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", broker_writes=True)
            ])

    def test_integrity_required(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:25:00Z", "2026-10-05T07:35:00Z", integrity_pass=False)
            ])

    def test_boundary_overrun_fails(self):
        with self.assertRaises(RND0054LedgerError):
            audit_and_advance([
                record("2026-10-05T07:25:00Z", "2027-04-03T07:30:00Z")
            ])

    def test_exact_boundary_becomes_readout_eligible(self):
        out = audit_and_advance([
            record("2026-10-05T07:25:00Z", "2027-04-03T07:25:00Z")
        ])
        self.assertEqual(out["state"], "READOUT_ELIGIBLE_PENDING_HUMAN_GATE")
        self.assertFalse(out["strategy_evaluation"])


if __name__ == "__main__":
    unittest.main()
