#!/usr/bin/env python3
"""Fail-closed OANDA practice historical acquisition primitives for RND-0028.

This module exposes one broker-facing capability only: authenticated HTTP GET
of M5 historical candles from the exact fxTrade Practice account/instrument
candles endpoint. It has no order, trade, position, account-configuration,
strategy-selection, promotion or capital authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

from historical_data_reconstruction import (
    HistoricalDataError,
    canonical_rows_sha256,
    validate_candle_rows,
)

VERSION = "RND-oanda-historical-acquisition-v0.1"
PRACTICE_BASE = "https://api-fxpractice.oanda.com"
M5_SECONDS = 300
MAX_CANDLES = 5000
INSTRUMENTS = {
    "AUDUSD": "AUD_USD",
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
}
ACCOUNT_RE = re.compile(r"^[A-Za-z0-9_-]{3,128}$")
INSTRUMENT_RE = re.compile(r"^[A-Z]{3}_[A-Z]{3}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_AUTHORITY = {
    "strategy_selection": False,
    "broker_writes": False,
    "automatic_merge": False,
    "automatic_promotion": False,
    "capital_authority": False,
    "human_review_required": True,
}
EXPECTED_RESERVED = {
    "state": "SEALED_BOUNDARY_UNBOUND",
    "strategy_metrics_allowed": False,
    "signal_generation_allowed": False,
    "trade_simulation_allowed": False,
    "parameter_selection_allowed": False,
    "human_open_gate_required": True,
}


class AcquisitionError(HistoricalDataError):
    pass


def _utc(value, role):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AcquisitionError(f"{role}: UTC timestamp ending Z required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AcquisitionError(f"{role}: invalid timestamp") from exc
    if int(dt.timestamp()) % M5_SECONDS:
        raise AcquisitionError(f"{role}: must be on M5 grid")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_declaration(value):
    required = {
        "contract_version", "task_id", "base_commit", "state", "source",
        "instruments", "acquisition_window", "evidence", "credential_contract",
        "reserved_test", "authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise AcquisitionError("declaration: exact fields required")
    if value["contract_version"] != VERSION or value["task_id"] != "RND-0028":
        raise AcquisitionError("declaration: identity mismatch")
    if value["instruments"] != INSTRUMENTS:
        raise AcquisitionError("declaration: instrument mapping drift")

    source = value["source"]
    expected_source = {
        "provider": "OANDA",
        "environment": "PRACTICE",
        "base_url": PRACTICE_BASE,
        "method": "GET",
        "endpoint_template": "/v3/accounts/{accountID}/instruments/{instrument}/candles",
        "granularity": "M5",
        "price": "MBA",
        "smooth": False,
        "include_first": True,
        "max_candles_per_request": MAX_CANDLES,
    }
    if source != expected_source:
        raise AcquisitionError("declaration: source authority drift")

    evidence = value["evidence"]
    expected_evidence = {
        "raw_page_sha256": True,
        "aggregate_raw_bundle_sha256": True,
        "canonical_rows_sha256": True,
        "require_bid_ask_mid_ohlc": True,
        "complete_candles_only": True,
        "explicit_gap_ledger": True,
        "immutable_snapshot": True,
        "overwrite_allowed": False,
    }
    if evidence != expected_evidence:
        raise AcquisitionError("declaration: evidence contract drift")

    credentials = value["credential_contract"]
    expected_credentials = {
        "token_source": "OANDA_PRACTICE_TOKEN_ENV",
        "account_id_source": "OANDA_PRACTICE_ACCOUNT_ID_ENV",
        "credentials_committed": False,
        "credentials_written_to_evidence": False,
        "credentials_logged": False,
    }
    if credentials != expected_credentials:
        raise AcquisitionError("declaration: credential contract drift")
    if value["reserved_test"] != EXPECTED_RESERVED:
        raise AcquisitionError("declaration: reserved-test drift")
    if value["authority"] != EXPECTED_AUTHORITY:
        raise AcquisitionError("declaration: authority escalation")

    window = value["acquisition_window"]
    if not isinstance(window, dict) or set(window) != {"start_utc", "end_utc", "human_approved"}:
        raise AcquisitionError("declaration: acquisition window fields")
    state = value["state"]
    if state == "UNBOUND_WINDOW":
        if window != {"start_utc": None, "end_utc": None, "human_approved": False}:
            raise AcquisitionError("declaration: unbound window must remain null")
    elif state == "ACQUISITION_READY":
        if window["human_approved"] is not True:
            raise AcquisitionError("declaration: human-approved window required")
        start = _utc(window["start_utc"], "window.start_utc")
        end = _utc(window["end_utc"], "window.end_utc")
        if start >= end:
            raise AcquisitionError("declaration: invalid acquisition window")
    else:
        raise AcquisitionError("declaration: unsupported state")
    return True


def plan_chunks(declaration):
    validate_declaration(declaration)
    if declaration["state"] != "ACQUISITION_READY":
        raise AcquisitionError("acquisition: window is not human-approved")
    window = declaration["acquisition_window"]
    start = _utc(window["start_utc"], "window.start_utc")
    end = _utc(window["end_utc"], "window.end_utc")
    step = timedelta(seconds=M5_SECONDS * MAX_CANDLES)
    chunks = []
    cursor = start
    while cursor < end:
        chunk_end = min(cursor + step, end)
        slots = int((chunk_end - cursor).total_seconds() // M5_SECONDS)
        if slots < 1 or slots > MAX_CANDLES:
            raise AcquisitionError("acquisition: invalid chunk size")
        chunks.append({"start_utc": _z(cursor), "end_utc": _z(chunk_end), "slots": slots})
        cursor = chunk_end
    return chunks


def build_candle_url(declaration, account_id, symbol, chunk):
    validate_declaration(declaration)
    if declaration["state"] != "ACQUISITION_READY":
        raise AcquisitionError("request: acquisition window not ready")
    if not isinstance(account_id, str) or not ACCOUNT_RE.fullmatch(account_id):
        raise AcquisitionError("request: invalid account identifier")
    if symbol not in INSTRUMENTS:
        raise AcquisitionError("request: unsupported symbol")
    if not isinstance(chunk, dict) or set(chunk) != {"start_utc", "end_utc", "slots"}:
        raise AcquisitionError("request: invalid chunk")
    start = _utc(chunk["start_utc"], "chunk.start_utc")
    end = _utc(chunk["end_utc"], "chunk.end_utc")
    slots = int((end - start).total_seconds() // M5_SECONDS)
    if chunk["slots"] != slots or slots < 1 or slots > MAX_CANDLES:
        raise AcquisitionError("request: chunk exceeds bounded M5 slots")
    w = declaration["acquisition_window"]
    if start < _utc(w["start_utc"], "window.start_utc") or end > _utc(w["end_utc"], "window.end_utc"):
        raise AcquisitionError("request: chunk outside approved window")
    instrument = INSTRUMENTS[symbol]
    path = f"/v3/accounts/{quote(account_id, safe='')}/instruments/{instrument}/candles"
    query = urlencode({
        "price": "MBA",
        "granularity": "M5",
        "from": chunk["start_utc"],
        "to": chunk["end_utc"],
        "smooth": "false",
        "includeFirst": "true",
    })
    url = PRACTICE_BASE + path + "?" + query
    validate_candle_url(url)
    return url


def validate_candle_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "api-fxpractice.oanda.com":
        raise AcquisitionError("request: practice host required")
    match = re.fullmatch(
        r"/v3/accounts/([A-Za-z0-9_-]{3,128})/instruments/([A-Z]{3}_[A-Z]{3})/candles",
        parsed.path,
    )
    if not match:
        raise AcquisitionError("request: exact candle endpoint required")
    if match.group(2) not in set(INSTRUMENTS.values()):
        raise AcquisitionError("request: unsupported instrument")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if set(query) != {"price", "granularity", "from", "to", "smooth", "includeFirst"}:
        raise AcquisitionError("request: exact query fields required")
    singleton = {k: v[0] for k, v in query.items() if len(v) == 1}
    if len(singleton) != len(query):
        raise AcquisitionError("request: duplicate query parameter")
    if singleton["price"] != "MBA" or singleton["granularity"] != "M5":
        raise AcquisitionError("request: MBA/M5 required")
    if singleton["smooth"] != "false" or singleton["includeFirst"] != "true":
        raise AcquisitionError("request: candle semantics drift")
    start = _utc(singleton["from"], "request.from")
    end = _utc(singleton["to"], "request.to")
    slots = int((end - start).total_seconds() // M5_SECONDS)
    if start >= end or slots < 1 or slots > MAX_CANDLES:
        raise AcquisitionError("request: invalid bounded range")
    return True


def fetch_page(url, token, opener=urlopen, timeout=30):
    validate_candle_url(url)
    if not isinstance(token, str) or not token.strip():
        raise AcquisitionError("credential: runtime token required")
    request = Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept-Datetime-Format": "RFC3339",
            "Accept": "application/json",
        },
        method="GET",
    )
    response = opener(request, timeout=timeout)
    status = getattr(response, "status", 200)
    if status != 200:
        raise AcquisitionError(f"transport: HTTP {status}")
    raw = response.read()
    if not isinstance(raw, bytes) or not raw:
        raise AcquisitionError("transport: non-empty bytes required")
    request_id = None
    headers = getattr(response, "headers", None)
    if headers is not None:
        request_id = headers.get("RequestID")
    return {"raw_bytes": raw, "request_id": request_id}


def _price_text(value, role):
    if not isinstance(value, str) or not value:
        raise AcquisitionError(f"{role}: provider price string required")
    try:
        price = Decimal(value)
    except InvalidOperation as exc:
        raise AcquisitionError(f"{role}: invalid decimal") from exc
    if not price.is_finite() or price <= 0:
        raise AcquisitionError(f"{role}: positive finite price required")
    return value


def parse_page(raw_bytes, expected_instrument):
    if not isinstance(raw_bytes, bytes) or not raw_bytes:
        raise AcquisitionError("response: raw bytes required")
    if expected_instrument not in set(INSTRUMENTS.values()):
        raise AcquisitionError("response: unsupported expected instrument")
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcquisitionError("response: invalid JSON") from exc
    if not isinstance(payload, dict):
        raise AcquisitionError("response: object required")
    if payload.get("instrument") != expected_instrument or payload.get("granularity") != "M5":
        raise AcquisitionError("response: instrument/granularity mismatch")
    candles = payload.get("candles")
    if not isinstance(candles, list) or not candles:
        raise AcquisitionError("response: non-empty candles required")

    rows = []
    for i, candle in enumerate(candles):
        if not isinstance(candle, dict) or candle.get("complete") is not True:
            raise AcquisitionError(f"response.candles[{i}]: complete candle required")
        ts = candle.get("time")
        _utc(ts, f"response.candles[{i}].time")
        row = {"timestamp_utc": ts, "complete": True}
        for component in ("bid", "ask", "mid"):
            part = candle.get(component)
            if not isinstance(part, dict) or set(part) != {"o", "h", "l", "c"}:
                raise AcquisitionError(f"response.candles[{i}].{component}: OHLC required")
            for short, long_name in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close")):
                row[f"{component}_{long_name}"] = _price_text(
                    part[short], f"response.candles[{i}].{component}.{short}"
                )
        rows.append(row)
    validate_candle_rows(rows)
    return rows


def raw_page_evidence(raw_bytes, request_url, request_id=None):
    validate_candle_url(request_url)
    if not isinstance(raw_bytes, bytes) or not raw_bytes:
        raise AcquisitionError("page evidence: bytes required")
    parsed = urlparse(request_url)
    match = re.fullmatch(
        r"/v3/accounts/([A-Za-z0-9_-]{3,128})/instruments/([A-Z]{3}_[A-Z]{3})/candles",
        parsed.path,
    )
    query = parse_qs(parsed.query)
    return {
        "instrument": match.group(2),
        "from_utc": query["from"][0],
        "to_utc": query["to"][0],
        "request_id": request_id,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "byte_count": len(raw_bytes),
    }


def aggregate_raw_bundle_sha256(raw_pages):
    if not isinstance(raw_pages, list) or not raw_pages:
        raise AcquisitionError("bundle: non-empty page list required")
    h = hashlib.sha256()
    for page in raw_pages:
        if not isinstance(page, bytes):
            raise AcquisitionError("bundle: bytes pages required")
        h.update(len(page).to_bytes(8, "big"))
        h.update(page)
    return h.hexdigest()


def merge_canonical_pages(pages):
    if not isinstance(pages, list) or not pages:
        raise AcquisitionError("merge: non-empty page list required")
    rows = []
    for page in pages:
        if not isinstance(page, list) or not page:
            raise AcquisitionError("merge: non-empty parsed pages required")
        rows.extend(page)
    timestamps = [r["timestamp_utc"] for r in rows]
    if len(set(timestamps)) != len(timestamps):
        raise AcquisitionError("merge: page overlap/duplicate timestamp")
    validate_candle_rows(rows)
    return rows


def build_gap_ledger(rows, expected_timestamps):
    validate_candle_rows(rows)
    if not isinstance(expected_timestamps, list):
        raise AcquisitionError("gap ledger: expected timestamps list required")
    expected = list(expected_timestamps)
    actual = [r["timestamp_utc"] for r in rows]
    missing = [x for x in expected if x not in set(actual)]
    unexpected = [x for x in actual if x not in set(expected)]
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing_timestamps": missing,
        "unexpected_timestamps": unexpected,
        "complete": not missing and not unexpected,
    }


def evidence_summary(raw_pages, parsed_rows, page_evidence, gap_ledger):
    if not isinstance(page_evidence, list) or len(page_evidence) != len(raw_pages):
        raise AcquisitionError("evidence: page evidence cardinality mismatch")
    for raw, evidence in zip(raw_pages, page_evidence):
        digest = hashlib.sha256(raw).hexdigest()
        if evidence.get("raw_sha256") != digest:
            raise AcquisitionError("evidence: raw page hash mismatch")
    if not isinstance(gap_ledger, dict) or gap_ledger.get("complete") is not True:
        raise AcquisitionError("evidence: unresolved gap ledger")
    return {
        "state": "SEALED",
        "page_count": len(raw_pages),
        "row_count": len(parsed_rows),
        "aggregate_raw_bundle_sha256": aggregate_raw_bundle_sha256(raw_pages),
        "canonical_rows_sha256": canonical_rows_sha256(parsed_rows),
        "pages": page_evidence,
        "gap_ledger": gap_ledger,
    }


def validate_output_target(output_dir, repo_root):
    target = Path(output_dir).expanduser().resolve()
    repo = Path(repo_root).expanduser().resolve()
    if target == repo or repo in target.parents:
        raise AcquisitionError("storage: output must be outside governed repository")
    if target.exists():
        raise AcquisitionError("storage: sealed target already exists; overwrite prohibited")
    return target
