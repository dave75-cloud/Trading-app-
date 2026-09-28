#!/usr/bin/env python3

import copy
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from historical_data_reconstruction import canonical_rows_sha256
from oanda_historical_acquisition import (
    AcquisitionError,
    aggregate_raw_bundle_sha256,
    build_candle_url,
    build_gap_ledger,
    evidence_summary,
    fetch_page,
    merge_canonical_pages,
    parse_page,
    plan_chunks,
    raw_page_evidence,
    validate_candle_url,
    validate_declaration,
    validate_output_target,
    validate_page_window,
)


ROOT = Path(__file__).resolve().parents[1]


def declaration():
    return json.loads(
        (ROOT / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json").read_text()
    )


def ready():
    value = declaration()
    value["state"] = "ACQUISITION_READY"
    value["acquisition_window"] = {
        "start_utc": "2020-01-01T00:00:00Z",
        "end_utc": "2020-01-20T00:00:00Z",
        "human_approved": True,
    }
    return value


def candle(ts="2020-01-01T00:00:00.000000000Z", complete=True):
    return {
        "complete": complete,
        "volume": 100,
        "time": ts,
        "bid": {"o": "1.10000", "h": "1.10100", "l": "1.09900", "c": "1.10050"},
        "ask": {"o": "1.10020", "h": "1.10120", "l": "1.09920", "c": "1.10070"},
        "mid": {"o": "1.10010", "h": "1.10110", "l": "1.09910", "c": "1.10060"},
    }


def raw_page(candles=None, instrument="AUD_USD", granularity="M5"):
    if candles is None:
        candles = [candle()]
    return json.dumps(
        {"instrument": instrument, "granularity": granularity, "candles": candles},
        separators=(",", ":"),
    ).encode()


def one_chunk(value=None):
    value = value or ready()
    return plan_chunks(value)[0]


def url(value=None, account="practice-account", symbol="AUDUSD", chunk=None):
    value = value or ready()
    return build_candle_url(value, account, symbol, chunk or one_chunk(value))


class FakeResponse:
    def __init__(self, raw, status=200, request_id="RID-1"):
        self._raw = raw
        self.status = status
        self.headers = {"RequestID": request_id}

    def read(self):
        return self._raw


class CaptureOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout=None):
        self.request = request
        self.timeout = timeout
        return self.response


class LeakyOpener:
    def __call__(self, request, timeout=None):
        raise RuntimeError(request.full_url)


class OandaHistoricalAcquisitionTests(unittest.TestCase):
    def test_repository_declaration_is_valid_and_unbound(self):
        value = declaration()
        self.assertTrue(validate_declaration(value))
        self.assertEqual("UNBOUND_WINDOW", value["state"])
        self.assertEqual(
            {"start_utc": None, "end_utc": None, "human_approved": False},
            value["acquisition_window"],
        )

    def test_unbound_window_cannot_plan_requests(self):
        with self.assertRaisesRegex(AcquisitionError, "not human-approved"):
            plan_chunks(declaration())

    def test_ready_window_requires_human_approval(self):
        value = ready()
        value["acquisition_window"]["human_approved"] = False
        with self.assertRaisesRegex(AcquisitionError, "human-approved"):
            validate_declaration(value)

    def test_live_host_or_source_drift_is_rejected(self):
        value = declaration()
        value["source"]["base_url"] = "https://api-fx" + "trade.oanda.com"
        with self.assertRaisesRegex(AcquisitionError, "source authority"):
            validate_declaration(value)

    def test_non_get_source_drift_is_rejected(self):
        value = declaration()
        value["source"]["method"] = "POST"
        with self.assertRaisesRegex(AcquisitionError, "source authority"):
            validate_declaration(value)

    def test_chunk_planner_caps_each_request_at_5000_slots(self):
        chunks = plan_chunks(ready())
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(1 <= x["slots"] <= 5000 for x in chunks))
        self.assertEqual("2020-01-01T00:00:00Z", chunks[0]["start_utc"])
        self.assertEqual("2020-01-20T00:00:00Z", chunks[-1]["end_utc"])

    def test_exact_candle_url_is_practice_get_surface(self):
        request_url = url()
        self.assertTrue(validate_candle_url(request_url))
        parsed = urlparse(request_url)
        self.assertEqual("api-fxpractice.oanda.com", parsed.netloc)
        self.assertTrue(parsed.path.endswith("/instruments/AUD_USD/candles"))
        query = parse_qs(parsed.query)
        self.assertEqual(["MBA"], query["price"])
        self.assertEqual(["M5"], query["granularity"])
        self.assertNotIn("count", query)

    def test_live_url_is_rejected(self):
        request_url = url().replace("api-fxpractice", "api-fxtrade")
        with self.assertRaisesRegex(AcquisitionError, "practice host"):
            validate_candle_url(request_url)

    def test_order_endpoint_injection_is_rejected(self):
        request_url = url().replace("/instruments/AUD_USD/candles", "/orders")
        with self.assertRaisesRegex(AcquisitionError, "exact candle endpoint"):
            validate_candle_url(request_url)

    def test_extra_query_authority_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "exact query fields"):
            validate_candle_url(url() + "&count=5000")

    def test_chunk_over_5000_slots_is_rejected(self):
        value = ready()
        chunk = {
            "start_utc": "2020-01-01T00:00:00Z",
            "end_utc": "2020-01-18T08:45:00Z",
            "slots": 5001,
        }
        with self.assertRaisesRegex(AcquisitionError, "bounded"):
            build_candle_url(value, "practice-account", "AUDUSD", chunk)

    def test_fetch_is_get_and_token_is_not_returned(self):
        token = "super-secret-token"
        opener = CaptureOpener(FakeResponse(raw_page()))
        result = fetch_page(url(), token, opener=opener)
        self.assertEqual("GET", opener.request.get_method())
        self.assertIn(token, opener.request.get_header("Authorization"))
        self.assertNotIn(token, repr(result))
        self.assertEqual(raw_page(), result["raw_bytes"])

    def test_transport_failure_fails_closed_without_echoing_token(self):
        opener = CaptureOpener(FakeResponse(b"denied", status=401))
        with self.assertRaisesRegex(AcquisitionError, "HTTP 401") as ctx:
            fetch_page(url(), "never-echo-this", opener=opener)
        self.assertNotIn("never-echo-this", str(ctx.exception))

    def test_transport_exception_does_not_echo_account_url(self):
        with self.assertRaisesRegex(AcquisitionError, "request failed") as ctx:
            fetch_page(url(account="secret-account"), "secret-token", opener=LeakyOpener())
        self.assertNotIn("secret-account", str(ctx.exception))
        self.assertNotIn("secret-token", str(ctx.exception))

    def test_valid_page_preserves_bid_ask_mid_provider_strings(self):
        rows = parse_page(raw_page(), "AUD_USD")
        self.assertEqual(1, len(rows))
        self.assertEqual("1.10050", rows[0]["bid_close"])
        self.assertEqual("1.10070", rows[0]["ask_close"])
        self.assertEqual("1.10060", rows[0]["mid_close"])

    def test_missing_mid_is_rejected(self):
        item = candle()
        del item["mid"]
        with self.assertRaisesRegex(AcquisitionError, "mid"):
            parse_page(raw_page([item]), "AUD_USD")

    def test_incomplete_candle_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "complete candle"):
            parse_page(raw_page([candle(complete=False)]), "AUD_USD")

    def test_wrong_instrument_or_granularity_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "mismatch"):
            parse_page(raw_page(instrument="EUR_USD"), "AUD_USD")
        with self.assertRaisesRegex(AcquisitionError, "mismatch"):
            parse_page(raw_page(granularity="H1"), "AUD_USD")

    def test_malformed_json_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "invalid JSON"):
            parse_page(b"{", "AUD_USD")

    def test_off_grid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "M5 grid"):
            parse_page(raw_page([candle("2020-01-01T00:01:00.000000000Z")]), "AUD_USD")

    def test_non_string_provider_price_is_rejected(self):
        item = candle()
        item["mid"]["c"] = 1.1006
        with self.assertRaisesRegex(AcquisitionError, "provider price string"):
            parse_page(raw_page([item]), "AUD_USD")

    def test_page_evidence_excludes_account_and_token(self):
        request_url = url(account="secret-account")
        raw = raw_page()
        evidence = raw_page_evidence(raw, request_url, "RID-7")
        self.assertNotIn("secret-account", repr(evidence))
        self.assertNotIn("Authorization", repr(evidence))
        self.assertEqual("AUD_USD", evidence["instrument"])

    def test_raw_bundle_digest_binds_page_order(self):
        a, b = b"a", b"bb"
        self.assertNotEqual(
            aggregate_raw_bundle_sha256([a, b]),
            aggregate_raw_bundle_sha256([b, a]),
        )

    def test_candle_outside_requested_chunk_is_rejected(self):
        rows = parse_page(raw_page([candle("2020-01-01T00:00:00.000000000Z")]), "AUD_USD")
        chunk = {"start_utc": "2020-01-01T00:05:00Z", "end_utc": "2020-01-01T00:10:00Z", "slots": 1}
        with self.assertRaisesRegex(AcquisitionError, "outside requested"):
            validate_page_window(rows, chunk)

    def test_response_cannot_exceed_requested_slot_count(self):
        rows = parse_page(
            raw_page([
                candle("2020-01-01T00:00:00.000000000Z"),
                candle("2020-01-01T00:05:00.000000000Z"),
            ]),
            "AUD_USD",
        )
        chunk = {"start_utc": "2020-01-01T00:00:00Z", "end_utc": "2020-01-01T00:05:00Z", "slots": 1}
        with self.assertRaisesRegex(AcquisitionError, "exceeds requested"):
            validate_page_window(rows, chunk)

    def test_page_overlap_is_rejected(self):
        page = parse_page(raw_page(), "AUD_USD")
        with self.assertRaisesRegex(AcquisitionError, "overlap"):
            merge_canonical_pages([page, copy.deepcopy(page)])

    def test_gap_ledger_rejects_duplicate_expected_schedule(self):
        rows = parse_page(raw_page(), "AUD_USD")
        with self.assertRaisesRegex(AcquisitionError, "unique and ordered"):
            build_gap_ledger(
                rows,
                ["2020-01-01T00:00:00Z", "2020-01-01T00:00:00.000000000Z"],
            )

    def test_gap_ledger_normalizes_equivalent_timestamp_precision(self):
        rows = parse_page(raw_page(), "AUD_USD")
        ledger = build_gap_ledger(rows, ["2020-01-01T00:00:00Z"])
        self.assertTrue(ledger["complete"])

    def test_gap_ledger_blocks_seal_when_unresolved(self):
        rows = parse_page(raw_page(), "AUD_USD")
        ledger = build_gap_ledger(
            rows,
            ["2020-01-01T00:00:00.000000000Z", "2020-01-01T00:05:00.000000000Z"],
        )
        self.assertFalse(ledger["complete"])
        ev = [raw_page_evidence(raw_page(), url())]
        with self.assertRaisesRegex(AcquisitionError, "gap ledger"):
            evidence_summary([raw_page()], rows, ev, ledger)

    def test_evidence_summary_detects_raw_mutation(self):
        raw = raw_page()
        rows = parse_page(raw, "AUD_USD")
        expected = [rows[0]["timestamp_utc"]]
        ledger = build_gap_ledger(rows, expected)
        ev = [raw_page_evidence(raw, url())]
        with self.assertRaisesRegex(AcquisitionError, "hash mismatch"):
            evidence_summary([raw + b" "], rows, ev, ledger)

    def test_midpoint_mutation_changes_canonical_digest(self):
        rows = parse_page(raw_page(), "AUD_USD")
        changed = copy.deepcopy(rows)
        changed[0]["mid_close"] = "1.10061"
        self.assertNotEqual(canonical_rows_sha256(rows), canonical_rows_sha256(changed))

    def test_output_inside_repository_is_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "outside governed"):
            validate_output_target(ROOT / "evidence", ROOT.parent)

    def test_existing_output_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "sealed"
            existing.mkdir()
            with self.assertRaisesRegex(AcquisitionError, "overwrite"):
                validate_output_target(existing, ROOT.parent)

    def test_new_external_output_target_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "new-sealed"
            resolved = validate_output_target(target, ROOT.parent)
            self.assertEqual(target.resolve(), resolved)


if __name__ == "__main__":
    unittest.main()
