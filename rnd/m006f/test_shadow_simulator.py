#!/usr/bin/env python3
import unittest

from shadow_simulator import ShadowError, simulate


def event(eid, pair, action, bid, ask, **extra):
    row = {
        "event_id": eid,
        "timestamp_utc": "2026-09-21T00:00:00Z",
        "pair": pair,
        "action": action,
        "bid": bid,
        "ask": ask,
    }
    row.update(extra)
    return row


class ShadowSimulatorTests(unittest.TestCase):
    def test_long_round_trip(self):
        rows = [
            event("1", "AUDUSD", "entry", 0.6500, 0.6502,
                  side="long", units=100000, base_to_aud=1.0),
            event("2", "AUDUSD", "exit", 0.6510, 0.6512,
                  quote_to_aud=1.5),
        ]
        r = simulate(rows)
        expected = (0.6510 - 0.6502) * 100000 * 1.5
        self.assertAlmostEqual(r["realized_pnl_aud"], expected)
        self.assertEqual(r["open_positions"], {})

    def test_short_round_trip(self):
        rows = [
            event("1", "EURUSD", "entry", 1.1000, 1.1002,
                  side="short", units=1000, base_to_aud=1.7),
            event("2", "EURUSD", "exit", 1.0990, 1.0992,
                  quote_to_aud=1.5),
        ]
        r = simulate(rows)
        expected = (1.1000 - 1.0992) * 1000 * 1.5
        self.assertAlmostEqual(r["realized_pnl_aud"], expected)

    def test_slippage_is_adverse(self):
        rows = [
            event("1", "GBPUSD", "entry", 1.3000, 1.3002,
                  side="long", units=1000, base_to_aud=2.0),
            event("2", "GBPUSD", "exit", 1.3010, 1.3012,
                  quote_to_aud=1.5),
        ]
        clean = simulate(rows, slippage_bps=0.0)
        slipped = simulate(rows, slippage_bps=1.0)
        self.assertLess(slipped["realized_pnl_aud"], clean["realized_pnl_aud"])

    def test_duplicate_event_fails(self):
        rows = [
            event("x", "AUDUSD", "entry", 0.65, 0.6502,
                  side="long", units=100, base_to_aud=1.0),
            event("x", "AUDUSD", "exit", 0.651, 0.6512,
                  quote_to_aud=1.5),
        ]
        with self.assertRaises(ShadowError):
            simulate(rows)

    def test_exit_from_flat_fails(self):
        rows = [
            event("x", "USDJPY", "exit", 150.0, 150.02,
                  quote_to_aud=0.01),
        ]
        with self.assertRaises(ShadowError):
            simulate(rows)

    def test_opaque_reversal_rejected(self):
        rows = [
            event("x", "AUDUSD", "reversal", 0.65, 0.6502,
                  side="short", units=100, base_to_aud=1.0),
        ]
        with self.assertRaises(ShadowError):
            simulate(rows)

    def test_deterministic(self):
        rows = [
            event("1", "AUDUSD", "entry", 0.6500, 0.6502,
                  side="long", units=100, base_to_aud=1.0),
            event("2", "AUDUSD", "exit", 0.6510, 0.6512,
                  quote_to_aud=1.5),
        ]
        self.assertEqual(simulate(rows), simulate(rows))


if __name__ == "__main__":
    unittest.main()
