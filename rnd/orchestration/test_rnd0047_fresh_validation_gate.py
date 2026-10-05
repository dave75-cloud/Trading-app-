import unittest

import rnd0047_fresh_validation_gate as g


class RND0047GateTests(unittest.TestCase):
    def valid(self, end="2026-10-05T08:25:00Z"):
        return g.build_implementation_declaration(end)

    def test_valid_implementation_declaration(self):
        result = g.validate_declaration(self.valid())
        self.assertEqual(result["candidate_id"], "Q003")
        self.assertEqual(result["start_utc"], g.FRESH_START_UTC)
        self.assertEqual(result["state"], g.IMPLEMENTATION_STATE)

    def test_rejects_candidate_fingerprint_drift(self):
        v = self.valid()
        v["candidate_fingerprint"] = "0" * 64
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_rejects_pre_freeze_start(self):
        v = self.valid()
        v["acquisition_window"]["start_utc"] = "2026-10-05T07:20:00Z"
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_rejects_2025_historical_window(self):
        v = self.valid()
        v["acquisition_window"] = {
            "start_utc": "2025-01-01T00:00:00Z",
            "end_utc": "2025-02-01T00:00:00Z",
        }
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_rejects_symbol_change(self):
        v = self.valid()
        v["symbols"] = ["EURUSD", "GBPUSD", "USDJPY"]
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_rejects_strategy_evaluation(self):
        v = self.valid()
        v["strategy_evaluation"] = True
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_rejects_reserved_final_access(self):
        v = self.valid()
        v["reserved_final_access"] = True
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)

    def test_actual_acquisition_requires_separate_authority(self):
        v = self.valid()
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v, require_acquisition_authority=True)

    def test_m5_grid_required(self):
        v = self.valid()
        v["acquisition_window"]["end_utc"] = "2026-10-05T08:26:00Z"
        with self.assertRaises(g.RND0047GateError):
            g.validate_declaration(v)


if __name__ == "__main__":
    unittest.main()
