import unittest
from datetime import datetime, timedelta, timezone

from rnd0060c_cross_sectional_usd_relative_value import (
    RND0060CError,
    SYMBOLS,
    evaluate_portfolio,
)


def z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row(dt, mid, spread=0.0002):
    half = spread / 2
    return {
        "timestamp_utc": z(dt),
        "complete": True,
        "bid_close": mid - half,
        "ask_close": mid + half,
        "mid_close": mid,
    }


def base_rows(day=datetime(2019, 1, 2, tzinfo=timezone.utc), moves=None, omit=None, post_gap_symbol=None):
    moves = moves or {}
    omit = omit or set()
    out = {s: [] for s in SYMBOLS}
    starts = {"AUDUSD": 1.0, "EURUSD": 1.2, "GBPUSD": 1.4, "USDJPY": 110.0}
    for s in SYMBOLS:
        start_mid = starts[s]
        end_mid = start_mid * (1.0 + moves.get(s, 0.0))
        for n in range(11):  # 11:00 through 11:50
            dt = datetime(day.year, day.month, day.day, 11, 0, tzinfo=timezone.utc) + timedelta(minutes=5*n)
            if (s, z(dt)) in omit:
                continue
            if n <= 6:
                frac = n / 6.0
                mid = start_mid + (end_mid - start_mid) * frac
            else:
                # After 11:30 drift back toward the 11:00 level to reward convergence.
                frac = min((n - 6) / 4.0, 1.0)
                mid = end_mid + (start_mid - end_mid) * frac
            out[s].append(row(dt, mid, spread=0.0002 if s != "USDJPY" else 0.02))

        if post_gap_symbol == s:
            # Remove 11:40 only; 11:45 and 11:50 remain genuine observations.
            out[s] = [r for r in out[s] if r["timestamp_utc"] != z(datetime(day.year, day.month, day.day, 11, 40, tzinfo=timezone.utc))]
    return out


class TestRND0060CCrossSectional(unittest.TestCase):
    def test_audusd_positive_raw_outlier_is_short_for_convergence(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}))
        t = out["per_symbol"]["AUDUSD"]["trades"][0]
        self.assertEqual(t["side"], "short")
        self.assertGreater(t["net_return"], 0)

    def test_audusd_negative_raw_outlier_is_long_for_convergence(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": -0.003}))
        self.assertEqual(out["per_symbol"]["AUDUSD"]["trades"][0]["side"], "long")

    def test_usdjpy_positive_raw_outlier_is_short_for_usd_weakening(self):
        out = evaluate_portfolio(base_rows(moves={"USDJPY": 0.003}))
        self.assertEqual(out["per_symbol"]["USDJPY"]["trades"][0]["side"], "short")

    def test_unique_small_outlier_trades_without_threshold(self):
        out = evaluate_portfolio(base_rows(moves={"EURUSD": 0.00001}))
        self.assertEqual(sum(x["trade_count"] for x in out["per_symbol"].values()), 1)
        self.assertEqual(out["selected_pair_counts"]["EURUSD"], 1)

    def test_exact_maximum_residual_tie_means_no_trade(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.002, "EURUSD": -0.002}))
        self.assertEqual(sum(x["trade_count"] for x in out["per_symbol"].values()), 0)
        self.assertTrue(any(e["event_type"] == "NO_TRADE_EXACT_TIE" for e in out["events"]))

    def test_missing_cross_section_window_skips_day(self):
        dt = datetime(2019, 1, 2, 11, 15, tzinfo=timezone.utc)
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}, omit={("GBPUSD", z(dt))}))
        self.assertEqual(sum(x["trade_count"] for x in out["per_symbol"].values()), 0)
        self.assertTrue(any(e["event_type"] == "DAY_SKIPPED_INCOMPLETE_CROSS_SECTION" for e in out["events"]))

    def test_missing_selected_pair_entry_bar_cancels(self):
        dt = datetime(2019, 1, 2, 11, 35, tzinfo=timezone.utc)
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}, omit={("AUDUSD", z(dt))}))
        self.assertEqual(sum(x["trade_count"] for x in out["per_symbol"].values()), 0)
        self.assertTrue(any(e["event_type"] == "PENDING_SIGNAL_CANCELLED" for e in out["events"]))

    def test_entry_bar_does_not_count_as_first_holding_bar(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}))
        t = out["per_symbol"]["AUDUSD"]["trades"][0]
        self.assertEqual(t["entry_timestamp"], "2019-01-02T11:35:00Z")
        self.assertEqual(t["exit_timestamp"], "2019-01-02T11:50:00Z")
        self.assertEqual(t["holding_bars"], 3)

    def test_gap_during_open_position_survives_and_missing_bar_does_not_count(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}, post_gap_symbol="AUDUSD"))
        t = out["per_symbol"]["AUDUSD"]["trades"][0]
        self.assertEqual(t["gap_exposure_count"], 1)
        self.assertEqual(t["holding_bars"], 3)

    def test_cost_drag_positive(self):
        out = evaluate_portfolio(base_rows(moves={"GBPUSD": 0.003}))
        t = out["per_symbol"]["GBPUSD"]["trades"][0]
        self.assertGreater(t["execution_cost_drag"], 0)
        self.assertGreater(t["gross_return"], t["net_return"])

    def test_selected_pair_counts_reconcile_trade_count(self):
        out = evaluate_portfolio(base_rows(moves={"USDJPY": -0.003}))
        self.assertEqual(sum(out["selected_pair_counts"].values()), 1)
        self.assertEqual(sum(x["trade_count"] for x in out["per_symbol"].values()), 1)

    def test_non_stacking_skips_later_day_if_prior_position_still_open(self):
        first = base_rows(day=datetime(2019, 1, 4, tzinfo=timezone.utc), moves={"AUDUSD": 0.003})
        second = base_rows(day=datetime(2019, 1, 7, tzinfo=timezone.utc), moves={"EURUSD": 0.003})
        # Remove every AUDUSD observation after Friday entry until Monday 11:35,
        # so the Friday economic position is still open at Monday 11:30.
        first["AUDUSD"] = [r for r in first["AUDUSD"] if r["timestamp_utc"] <= "2019-01-04T11:35:00Z"]
        second["AUDUSD"] = [r for r in second["AUDUSD"] if r["timestamp_utc"] >= "2019-01-07T11:35:00Z"]
        rows = {s: first[s] + second[s] for s in SYMBOLS}
        out = evaluate_portfolio(rows)
        self.assertTrue(any(e["event_type"] == "DAY_SKIPPED_OPEN_POSITION" for e in out["events"]))

    def test_development_year_firewall(self):
        rows = base_rows(moves={"AUDUSD": 0.003})
        rows["AUDUSD"][0] = dict(rows["AUDUSD"][0], timestamp_utc="2021-01-02T11:00:00Z")
        with self.assertRaises(RND0060CError):
            evaluate_portfolio(rows)

    def test_authority_remains_closed(self):
        out = evaluate_portfolio(base_rows(moves={"AUDUSD": 0.003}))
        self.assertTrue(out["development_only"])
        self.assertFalse(out["reserved_final_access"])
        self.assertFalse(out["broker_writes"])
        self.assertFalse(out["capital_authority"])
        self.assertFalse(out["automatic_promotion"])


if __name__ == "__main__":
    unittest.main()
