import unittest

from rnd0060s_prospective_operations_integrity import (
    RND0060SIntegrityError,
    STREAM_ID,
    operational_status,
    reconcile_ledger,
    validate_tranche,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64


def tranche(
    tranche_id="T001",
    start="2026-10-09T02:33:50Z",
    end="2026-10-10T02:33:50Z",
    captured="2026-10-10T03:00:00Z",
    source=A,
    artifact=B,
    eligible=1,
    defer=0,
    status="CAPTURED",
    stream_id=STREAM_ID,
):
    return {
        "tranche_id": tranche_id,
        "stream_id": stream_id,
        "window_start_utc": start,
        "window_end_utc": end,
        "captured_at_utc": captured,
        "source_sha256": source,
        "artifact_sha256": artifact,
        "eligible_non_defer_count": eligible,
        "defer_count": defer,
        "status": status,
    }


class TestRND0060SProspectiveOperationsIntegrity(unittest.TestCase):
    def test_01_valid_tranche(self):
        r = validate_tranche(tranche())
        self.assertEqual(r["tranche_id"], "T001")
        self.assertFalse(r["recovered"])

    def test_02_pre_start_interval_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            validate_tranche(tranche(start="2026-10-09T02:33:49Z"))

    def test_03_wrong_stream_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            validate_tranche(tranche(stream_id="Q003"))

    def test_04_capture_before_window_end_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            validate_tranche(tranche(captured="2026-10-10T02:00:00Z"))

    def test_05_bad_sha_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            validate_tranche(tranche(source="xyz"))

    def test_06_negative_count_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            validate_tranche(tranche(eligible=-1))

    def test_07_duplicate_tranche_id_rejected(self):
        rows = [tranche(), tranche(artifact=C, start="2026-10-10T02:33:50Z", end="2026-10-11T02:33:50Z", captured="2026-10-11T03:00:00Z")]
        with self.assertRaises(RND0060SIntegrityError):
            reconcile_ledger(rows)

    def test_08_duplicate_artifact_rejected(self):
        rows = [tranche(), tranche(tranche_id="T002", source=C, start="2026-10-10T02:33:50Z", end="2026-10-11T02:33:50Z", captured="2026-10-11T03:00:00Z")]
        with self.assertRaises(RND0060SIntegrityError):
            reconcile_ledger(rows)

    def test_09_overlap_rejected(self):
        rows = [
            tranche(),
            tranche(tranche_id="T002", source=C, artifact=D, start="2026-10-10T00:00:00Z", end="2026-10-11T00:00:00Z", captured="2026-10-11T01:00:00Z"),
        ]
        with self.assertRaises(RND0060SIntegrityError):
            reconcile_ledger(rows)

    def test_10_gap_recorded_not_hidden(self):
        rows = [
            tranche(),
            tranche(tranche_id="T002", source=C, artifact=D, start="2026-10-11T02:33:50Z", end="2026-10-12T02:33:50Z", captured="2026-10-12T03:00:00Z"),
        ]
        r = reconcile_ledger(rows)
        self.assertEqual(r["gap_count"], 1)
        self.assertEqual(r["gaps"][0]["status"], "GAP_DETECTED")

    def test_11_recovery_tag_preserved(self):
        r = reconcile_ledger([tranche(status="RECOVERED")])
        self.assertEqual(r["recovered_tranche_count"], 1)

    def test_12_counts_recomputed(self):
        rows = [
            tranche(eligible=3, defer=2),
            tranche(tranche_id="T002", source=C, artifact=D, start="2026-10-10T02:33:50Z", end="2026-10-11T02:33:50Z", captured="2026-10-11T03:00:00Z", eligible=4, defer=1),
        ]
        r = reconcile_ledger(rows)
        self.assertEqual(r["eligible_non_defer_count"], 7)
        self.assertEqual(r["defer_count"], 3)

    def test_13_readout_locked_before_time_and_count(self):
        r = operational_status([tranche()], "2026-10-20T02:33:50Z")
        self.assertEqual(r["readout_state"], "READOUT_LOCKED")
        self.assertFalse(r["economic_outcomes_exposed"])

    def test_14_count_met_but_time_not_met_stays_locked(self):
        r = operational_status([tranche(eligible=100)], "2026-12-01T02:33:50Z")
        self.assertTrue(r["count_requirement_met"])
        self.assertFalse(r["time_requirement_met"])
        self.assertEqual(r["readout_state"], "READOUT_LOCKED")

    def test_15_time_met_but_count_not_met_stays_locked(self):
        r = operational_status([tranche(eligible=99)], "2027-04-07T02:33:50Z")
        self.assertTrue(r["time_requirement_met"])
        self.assertFalse(r["count_requirement_met"])
        self.assertEqual(r["readout_state"], "READOUT_LOCKED")

    def test_16_both_requirements_met_pending_human_gate(self):
        r = operational_status([tranche(eligible=100)], "2027-04-07T02:33:50Z")
        self.assertTrue(r["time_requirement_met"])
        self.assertTrue(r["count_requirement_met"])
        self.assertEqual(r["readout_state"], "READOUT_ELIGIBLE_PENDING_HUMAN_GATE")

    def test_17_no_authority_expansion(self):
        r = operational_status([tranche()], "2026-10-20T02:33:50Z")
        for key in (
            "q003_prospective_outcomes_open",
            "validation_open",
            "final_test_open",
            "reserved_final_access",
            "broker_writes",
            "capital_authority",
            "automatic_promotion",
        ):
            self.assertFalse(r[key])

    def test_18_empty_ledger_rejected(self):
        with self.assertRaises(RND0060SIntegrityError):
            reconcile_ledger([])


if __name__ == "__main__":
    unittest.main()
