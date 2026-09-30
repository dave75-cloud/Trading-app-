#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import oanda_historical_quarantine as q  # noqa: E402


def acquisition_declaration():
    return json.loads(
        (ROOT / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json").read_text()
    )


def calendar_declaration():
    return json.loads(
        (ROOT / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json").read_text()
    )


def shard():
    return {
        "year": 2024,
        "start_utc": "2024-01-01T00:00:00Z",
        "end_utc": "2025-01-01T00:00:00Z",
    }


def raw_page(ts="2024-01-02T22:05:00.000000000Z"):
    candle = {
        "complete": True,
        "volume": 100,
        "time": ts,
        "bid": {"o": "1.10000", "h": "1.10100", "l": "1.09900", "c": "1.10050"},
        "ask": {"o": "1.10020", "h": "1.10120", "l": "1.09920", "c": "1.10070"},
        "mid": {"o": "1.10010", "h": "1.10110", "l": "1.09910", "c": "1.10060"},
    }
    return json.dumps(
        {"instrument": "AUD_USD", "granularity": "M5", "candles": [candle]},
        separators=(",", ":"),
    ).encode()


def acquire_into(target, expected=None):
    expected = expected or ["2024-01-02T22:05:00Z"]
    chunk = {
        "start_utc": "2024-01-02T22:05:00Z",
        "end_utc": "2024-01-02T22:10:00Z",
        "slots": 1,
    }
    with (
        patch.object(q, "standard_session_schedule", return_value=expected),
        patch.object(q, "plan_chunks", return_value=[chunk]),
        patch.object(
            q,
            "fetch_page",
            return_value={"raw_bytes": raw_page(), "request_id": "RID-TEST"},
        ),
    ):
        return q.acquire_shard(
            acquisition_declaration(),
            calendar_declaration(),
            "AUDUSD",
            shard(),
            "runtime-secret-token",
            "practice-account",
            Path(target),
            0.5,
        )


class OandaHistoricalQuarantineTests(unittest.TestCase):
    def test_source_binding_rejects_acquisition_window_drift(self):
        acquisition = acquisition_declaration()
        acquisition["acquisition_window"]["start_utc"] = "2016-01-01T00:00:00Z"
        with self.assertRaisesRegex(SystemExit, "not bound"):
            q._validate_source_binding(acquisition, calendar_declaration())

    def test_shard_declaration_does_not_mutate_source_window(self):
        source = acquisition_declaration()
        original = dict(source["acquisition_window"])
        value = q._shard_declaration(source, shard())
        self.assertEqual(original, source["acquisition_window"])
        self.assertEqual("2024-01-01T00:00:00Z", value["acquisition_window"]["start_utc"])
        self.assertEqual("2025-01-01T00:00:00Z", value["acquisition_window"]["end_utc"])

    def test_exact_standard_match_is_quarantined_not_sealed(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = acquire_into(tmp)
            self.assertEqual("QUARANTINED_STANDARD_MATCH", manifest["status"])
            self.assertFalse(manifest["seal_allowed"])
            self.assertEqual("RND-0030_QUARANTINE_ONLY", manifest["seal_block_reason"])
            self.assertFalse(manifest["credentials_recorded"])
            self.assertFalse(manifest["account_identity_recorded"])
            self.assertNotIn("runtime-secret-token", repr(manifest))
            self.assertNotIn("practice-account", repr(manifest))

    def test_missing_standard_timestamp_remains_unresolved(self):
        expected = [
            "2024-01-02T22:05:00Z",
            "2024-01-02T22:10:00Z",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            manifest = acquire_into(tmp, expected)
            self.assertEqual("QUARANTINED_UNRESOLVED_DISCREPANCIES", manifest["status"])
            self.assertEqual(1, manifest["missing_count"])
            self.assertFalse(manifest["seal_allowed"])
            self.assertEqual(
                "UNRESOLVED_CALENDAR_DISCREPANCIES",
                manifest["seal_block_reason"],
            )


    def test_valid_empty_provider_page_is_explicit_quarantine_evidence(self):
        raw = json.dumps(
            {"instrument": "AUD_USD", "granularity": "M5", "candles": []},
            separators=(",", ":"),
        ).encode()
        self.assertEqual([], q._parse_quarantine_page(raw, "AUD_USD"))

    def test_empty_provider_page_still_requires_exact_envelope(self):
        wrong = json.dumps(
            {"instrument": "EUR_USD", "granularity": "M5", "candles": []},
            separators=(",", ":"),
        ).encode()
        with self.assertRaisesRegex(ValueError, "mismatch"):
            q._parse_quarantine_page(wrong, "AUD_USD")

    def test_acquisition_preserves_empty_page_and_counts_it(self):
        first = {
            "start_utc": "2024-01-02T22:05:00Z",
            "end_utc": "2024-01-02T22:10:00Z",
            "slots": 1,
        }
        second = {
            "start_utc": "2024-01-02T22:10:00Z",
            "end_utc": "2024-01-02T22:15:00Z",
            "slots": 1,
        }
        empty = json.dumps(
            {"instrument": "AUD_USD", "granularity": "M5", "candles": []},
            separators=(",", ":"),
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(q, "standard_session_schedule", return_value=["2024-01-02T22:05:00Z"]),
                patch.object(q, "plan_chunks", return_value=[first, second]),
                patch.object(
                    q,
                    "fetch_page",
                    side_effect=[
                        {"raw_bytes": raw_page(), "request_id": "RID-1"},
                        {"raw_bytes": empty, "request_id": "RID-2"},
                    ],
                ),
                patch.object(q.time, "sleep", return_value=None),
            ):
                manifest = q.acquire_shard(
                    acquisition_declaration(),
                    calendar_declaration(),
                    "AUDUSD",
                    shard(),
                    "runtime-secret-token",
                    "practice-account",
                    Path(tmp),
                    0.5,
                )
            self.assertEqual(2, manifest["raw_page_count"])
            self.assertEqual(1, manifest["empty_raw_page_count"])
            self.assertEqual(1, manifest["row_count"])
            page_evidence = json.loads((Path(tmp) / "page_evidence.json").read_text())
            self.assertEqual([1, 0], [x["candle_count"] for x in page_evidence])
            self.assertTrue(q.verify_existing_shard(
                Path(tmp), "AUDUSD", shard(),
                acquisition_declaration(), calendar_declaration()
            ))

    def test_verified_existing_shard_can_be_resumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_into(tmp)
            self.assertTrue(q.verify_existing_shard(
                Path(tmp), "AUDUSD", shard(),
                acquisition_declaration(), calendar_declaration()
            ))

    def test_declaration_drift_breaks_resume_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_into(tmp)
            calendar = calendar_declaration()
            calendar["status"] = "DRIFTED"
            self.assertFalse(
                q.verify_existing_shard(
                    Path(tmp), "AUDUSD", shard(),
                    acquisition_declaration(), calendar
                )
            )

    def test_raw_page_tamper_breaks_resume_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_into(tmp)
            raw = Path(tmp) / "raw" / "page-0001.json"
            raw.write_bytes(raw.read_bytes() + b" ")
            self.assertFalse(q.verify_existing_shard(
                Path(tmp), "AUDUSD", shard(),
                acquisition_declaration(), calendar_declaration()
            ))

    def test_canonical_row_tamper_breaks_resume_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_into(tmp)
            path = Path(tmp) / "canonical_rows.json"
            rows = json.loads(path.read_text())
            rows[0]["mid_close"] = "1.10061"
            path.write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")
            self.assertFalse(q.verify_existing_shard(
                Path(tmp), "AUDUSD", shard(),
                acquisition_declaration(), calendar_declaration()
            ))

    def test_discrepancy_ledger_tamper_breaks_resume_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_into(tmp)
            path = Path(tmp) / "discrepancy_ledger.json"
            value = json.loads(path.read_text())
            value["resolved"] = False
            path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
            self.assertFalse(q.verify_existing_shard(
                Path(tmp), "AUDUSD", shard(),
                acquisition_declaration(), calendar_declaration()
            ))

    def test_selection_rejects_year_outside_predeclared_horizon(self):
        with self.assertRaisesRegex(SystemExit, "year outside"):
            q._validate_selection(["AUDUSD"], [2025])

    def test_selection_rejects_unknown_symbol(self):
        with self.assertRaisesRegex(SystemExit, "unsupported symbol"):
            q._validate_selection(["NZDUSD"], [2024])


if __name__ == "__main__":
    unittest.main()
