import unittest

from rnd0058_shadow_execution import (
    CANDIDATE_FINGERPRINT,
    ShadowExecutionError,
    apply_event,
    new_shadow_order,
)


def receipts():
    intent = {
        "intent_id": "i-1",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "decision": "SHADOW_ACCEPT",
        "requested_units": 10,
    }
    risk = {
        "intent_id": "i-1",
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "decision": "SHADOW_ACCEPT",
    }
    return intent, risk


class TestRND0058ShadowExecution(unittest.TestCase):
    def test_new_order_is_zero_write(self):
        order = new_shadow_order(*receipts())
        self.assertEqual(order["state"], "SHADOW_ORDER_PLANNED")
        self.assertFalse(order["broker_writes"])
        self.assertFalse(order["execution_authority"])

    def test_ack_then_full_fill(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        order = apply_event(order, {"event_id": "e2", "kind": "FILL", "units": 10})
        self.assertEqual(order["state"], "SHADOW_FILLED")
        self.assertEqual(order["filled_units"], 10)

    def test_partial_fill_then_fill(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        order = apply_event(order, {"event_id": "e2", "kind": "FILL", "units": 4})
        self.assertEqual(order["state"], "SHADOW_PARTIAL")
        order = apply_event(order, {"event_id": "e3", "kind": "FILL", "units": 6})
        self.assertEqual(order["state"], "SHADOW_FILLED")

    def test_fill_before_ack_rejected(self):
        order = new_shadow_order(*receipts())
        with self.assertRaises(ShadowExecutionError):
            apply_event(order, {"event_id": "e1", "kind": "FILL", "units": 1})

    def test_overfill_rejected(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        with self.assertRaises(ShadowExecutionError):
            apply_event(order, {"event_id": "e2", "kind": "FILL", "units": 11})

    def test_duplicate_event_rejected(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        with self.assertRaises(ShadowExecutionError):
            apply_event(order, {"event_id": "e1", "kind": "CANCEL"})

    def test_cancel_then_reconcile(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        order = apply_event(order, {"event_id": "e2", "kind": "CANCEL"})
        order = apply_event(order, {"event_id": "e3", "kind": "RECONCILE", "filled_units": 0, "position_delta_units": 0})
        self.assertEqual(order["state"], "RECONCILED")

    def test_reconciliation_mismatch_rejected(self):
        order = new_shadow_order(*receipts())
        order = apply_event(order, {"event_id": "e1", "kind": "ACK"})
        order = apply_event(order, {"event_id": "e2", "kind": "FILL", "units": 10})
        with self.assertRaises(ShadowExecutionError):
            apply_event(order, {"event_id": "e3", "kind": "RECONCILE", "filled_units": 9, "position_delta_units": 10})

    def test_receipt_binding_mismatch_rejected(self):
        intent, risk = receipts(); risk["intent_id"] = "other"
        with self.assertRaises(ShadowExecutionError):
            new_shadow_order(intent, risk)


if __name__ == "__main__":
    unittest.main()
