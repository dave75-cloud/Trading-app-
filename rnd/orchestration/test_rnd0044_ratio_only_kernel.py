#!/usr/bin/env python3
import math
import unittest
from datetime import datetime, timedelta

import gap_aware_m005_reconstruction as frozen
import rnd0044_ratio_only_kernel as r


def rows(start="2015-01-05T10:30:00Z", n=100, spread=0.00004, up=0.00035, down=-0.00015, gap_at=None):
    dt = datetime.fromisoformat(start[:-1] + "+00:00")
    out = []
    mid = 1.0
    for i in range(n):
        if gap_at is not None and i == gap_at:
            dt += timedelta(minutes=10)
        mid *= 1.0 + (up if i % 2 == 0 else down)
        bid = mid - spread / 2
        ask = mid + spread / 2
        out.append({
            "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complete": True,
            "bid_close": bid,
            "ask_close": ask,
            "mid_close": mid,
        })
        dt += timedelta(minutes=5)
    return out


class TestRND0044RatioOnlyKernel(unittest.TestCase):
    def test_exact_predeclared_ratio_only_arms(self):
        self.assertEqual(r.AUTHORIZED_ARMS, {"Q001": 3.0, "Q002": 5.0, "Q003": 8.0})
        with self.assertRaises(r.RND0044KernelError):
            r.reconstruct_pair("AUDUSD", rows(), "Q004")

    def test_ratio_formula_uses_last_12_returns_and_current_spread(self):
        returns = [0.001, -0.001] * 6 + [99.0]
        used = returns[-12:]
        bid, ask, mid = 0.9999, 1.0001, 1.0
        got = r.signal_to_friction_ratio(returns, bid, ask, mid)
        expected_spread = (ask - bid) / mid
        expected = frozen.population_std(used) / expected_spread
        self.assertTrue(math.isclose(got["relative_spread"], expected_spread, rel_tol=0, abs_tol=1e-18))
        self.assertTrue(math.isclose(got["signal_to_friction"], expected, rel_tol=0, abs_tol=1e-12))

    def test_ratio_only_removes_legacy_absolute_floor(self):
        # sigma is deliberately below 0.0005, while a very tight spread makes
        # signal_to_friction comfortably exceed Q001/Q002/Q003.
        closes = [1.0 + i * 0.00001 for i in range(50)]
        returns = [0.0002, -0.0002] * 6
        dt = datetime.fromisoformat("2015-01-05T11:30:00+00:00")
        bid, ask, mid = 0.99999, 1.00001, 1.0
        sigma = frozen.population_std(returns[-12:])
        self.assertLess(sigma, frozen.VOL_THRESHOLD)
        old = frozen._signal("AUDUSD", closes, returns, dt)
        new, eligible, ratio = r.raw_signal("AUDUSD", closes, returns, dt, bid, ask, mid, "Q003")
        self.assertEqual(old, 0)
        self.assertNotEqual(new, 0)
        self.assertTrue(eligible)
        self.assertGreaterEqual(ratio["signal_to_friction"], 8.0)

    def test_entry_ratios_respect_arm_threshold(self):
        out = r.reconstruct_pair("AUDUSD", rows(spread=0.00002), "Q003")
        self.assertFalse(out["absolute_volatility_floor_enabled"])
        self.assertTrue(all(x >= 8.0 for x in out["actual_entry_signal_to_friction_ratios"]))
        self.assertFalse(out["authority"]["development_outcomes"])

    def test_gate_does_not_create_exit_override(self):
        # Wider friction can block prospective entries, but existing positions
        # still exit only under frozen delayed signal/min-hold mechanics.
        loose = r.reconstruct_pair("AUDUSD", rows(spread=0.00002), "Q001")
        strict = r.reconstruct_pair("AUDUSD", rows(spread=0.00020), "Q003")
        self.assertGreaterEqual(strict["rejected_entry_signal_count"], 0)
        self.assertGreaterEqual(loose["completed_trade_count"], strict["completed_trade_count"])
        self.assertFalse(strict["authority"]["strategy_selection"])

    def test_gap_resets_ratio_state(self):
        out = r.reconstruct_pair("AUDUSD", rows(n=130, gap_at=65), "Q001")
        self.assertEqual(out["gap_count"], 1)
        self.assertGreaterEqual(out["contiguous_episode_count"], 2)

    def test_zero_spread_fails_closed(self):
        with self.assertRaises(r.RND0044KernelError):
            r.signal_to_friction_ratio([0.001, -0.001] * 6, 1.0, 1.0, 1.0)

    def test_post_development_year_is_rejected(self):
        fixture = rows(start="2021-01-04T11:00:00Z", n=2)
        with self.assertRaises(r.RND0044KernelError):
            r.reconstruct_pair("AUDUSD", fixture, "Q001")


if __name__ == "__main__":
    unittest.main()
