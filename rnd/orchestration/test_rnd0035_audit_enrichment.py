#!/usr/bin/env python3

import unittest

from rnd0035_audit_enrichment import RND0035AuditError, enrich_for_historical_audit


def fixture_result(with_events=False):
    trade = {
        "symbol": "AUDUSD",
        "side": "long",
        "side_value": 1,
        "entry_timestamp": "2019-01-02T11:00:00Z",
        "exit_timestamp": "2019-01-02T11:20:00Z",
        "entry_execution_price": 1.1001,
        "exit_execution_price": 1.1004,
        "entry_mid_price": 1.1,
        "exit_mid_price": 1.1005,
        "gross_return": 0.0004545454545,
        "net_return": 0.0002727024816,
        "execution_cost_drag": 0.0001818429729,
        "holding_bars": 4,
        "gap_exposure_count": 0,
        "gap_elapsed_seconds": 0,
        "gap_exposed": False,
        "exit_year": 2019,
        "episode": 1,
        "status": "COMPLETE",
    }
    events = []
    if with_events:
        events = [
            {"event_type": "ENTRY", "symbol": "AUDUSD", "timestamp": trade["entry_timestamp"]},
            {"event_type": "EXIT", "symbol": "AUDUSD", "timestamp": trade["exit_timestamp"]},
        ]
    return {
        "trial_id": "A001",
        "symbol": "AUDUSD",
        "completed_trade_count": 1,
        "censored_trade_count": 0,
        "completed_trade_net_equity_index": 1.0002727024816,
        "completed_trade_net_max_drawdown": 0.0,
        "completed_trade_gross_equity_index": 1.0004545454545,
        "completed_trade_gross_max_drawdown": 0.0,
        "total_execution_cost_drag": trade["execution_cost_drag"],
        "trades": [trade],
        "censored_trades": [],
        "gaps": [],
        "events": events,
        "marks": [],
        "authority": {"broker_writes": False, "capital_authority": False},
    }


class TestRND0035AuditEnrichment(unittest.TestCase):
    def test_adds_missing_audit_events_without_changing_economics(self):
        source = fixture_result()
        out = enrich_for_historical_audit(source)
        self.assertEqual(out["completed_trade_net_equity_index"], source["completed_trade_net_equity_index"])
        self.assertEqual(out["trades"][0]["net_return"], source["trades"][0]["net_return"])
        self.assertEqual(out["event_reconciliation"]["entry_events"], 1)
        self.assertEqual(out["event_reconciliation"]["exit_events"], 1)
        self.assertEqual(out["trades"][0]["elapsed_seconds"], 1200)
        self.assertEqual(out["by_exit_year"]["2019"]["trades"], 1)
        self.assertEqual(out["net_hit_rate"], 1.0)
        self.assertFalse(out["historical_audit_enrichment"]["economic_fields_modified"])
        self.assertEqual(source["events"], [])
        self.assertNotIn("elapsed_seconds", source["trades"][0])

    def test_preserves_existing_complete_entry_exit_ledger(self):
        source = fixture_result(with_events=True)
        out = enrich_for_historical_audit(source)
        self.assertEqual(len(out["events"]), 2)
        self.assertNotIn("audit_reconstructed", out["events"][0])
        self.assertEqual(out["event_reconciliation"]["entry_events"], 1)
        self.assertEqual(out["event_reconciliation"]["exit_events"], 1)

    def test_rejects_partial_event_ledger(self):
        source = fixture_result()
        source["events"] = [{"event_type": "ENTRY"}]
        with self.assertRaisesRegex(RND0035AuditError, "partial ENTRY/EXIT"):
            enrich_for_historical_audit(source)

    def test_rejects_trade_count_mismatch(self):
        source = fixture_result()
        source["completed_trade_count"] = 2
        with self.assertRaisesRegex(RND0035AuditError, "completed trade count"):
            enrich_for_historical_audit(source)


if __name__ == "__main__":
    unittest.main()
