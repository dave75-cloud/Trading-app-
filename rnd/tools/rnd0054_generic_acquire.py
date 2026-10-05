#!/usr/bin/env python3
"""Gap-aware GET-only prospective acquisition for RND-0054.

This wrapper reuses the bounded OANDA Practice candle primitives but deliberately
does not use the historical evidence_summary/validate_snapshot_evidence helpers,
because those require a fully populated market-calendar schedule. Prospective
weekly evidence instead records every absent wall-clock M5 slot explicitly in a
gap ledger. No strategy evaluation, order endpoint, broker write, reserved-final
access, promotion, or capital authority exists here.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from historical_data_reconstruction import canonical_rows_sha256, validate_candle_rows
from oanda_historical_acquisition import (
    BASE_COMMIT,
    EXPECTED_AUTHORITY,
    EXPECTED_RESERVED,
    INSTRUMENTS,
    VERSION,
    aggregate_raw_bundle_bytes,
    aggregate_raw_bundle_sha256,
    build_candle_url,
    build_gap_ledger,
    fetch_page,
    merge_canonical_pages,
    parse_page,
    plan_chunks,
    raw_page_evidence,
    validate_output_target,
    validate_page_window,
)
from rnd0054_ledger import CANDIDATE_ID, CANDIDATE_FINGERPRINT, SYMBOLS


class RND0054AcquireError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0054AcquireError(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0054AcquireError(f"{role}: invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, f"{role}: M5 boundary required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def wall_clock_m5(start_utc, end_utc):
    start = _utc(start_utc, "start_utc")
    end = _utc(end_utc, "end_utc")
    _req(start < end, "start must precede end")
    out = []
    cursor = start
    while cursor < end:
        out.append(_z(cursor))
        cursor += timedelta(minutes=5)
    return out


def acquisition_declaration(start_utc, end_utc):
    _req(tuple(SYMBOLS) == tuple(INSTRUMENTS), "instrument universe drift")
    return {
        "contract_version": VERSION,
        "task_id": "RND-0028",
        "base_commit": BASE_COMMIT,
        "state": "ACQUISITION_READY",
        "source": {
            "provider": "OANDA",
            "environment": "PRACTICE",
            "base_url": "https://api-fxpractice.oanda.com",
            "method": "GET",
            "endpoint_template": "/v3/accounts/{accountID}/instruments/{instrument}/candles",
            "granularity": "M5",
            "price": "MBA",
            "smooth": False,
            "include_first": True,
            "max_candles_per_request": 5000,
        },
        "instruments": dict(INSTRUMENTS),
        "acquisition_window": {
            "start_utc": start_utc,
            "end_utc": end_utc,
            "human_approved": True,
        },
        "evidence": {
            "raw_page_sha256": True,
            "aggregate_raw_bundle_sha256": True,
            "canonical_rows_sha256": True,
            "require_bid_ask_mid_ohlc": True,
            "complete_candles_only": True,
            "explicit_gap_ledger": True,
            "immutable_snapshot": True,
            "overwrite_allowed": False,
        },
        "credential_contract": {
            "token_source": "OANDA_PRACTICE_TOKEN_ENV",
            "account_id_source": "OANDA_PRACTICE_ACCOUNT_ID_ENV",
            "credentials_committed": False,
            "credentials_written_to_evidence": False,
            "credentials_logged": False,
        },
        "reserved_test": dict(EXPECTED_RESERVED),
        "authority": dict(EXPECTED_AUTHORITY),
    }


def acquire_symbol_gap_aware(declaration, symbol, token, account_id, expected_timestamps, target, page_fetcher=fetch_page):
    raw_pages = []
    parsed_pages = []
    page_records = []
    for chunk in plan_chunks(declaration):
        request_url = build_candle_url(declaration, account_id, symbol, chunk)
        fetched = page_fetcher(request_url, token)
        raw = fetched["raw_bytes"]
        rows = parse_page(raw, INSTRUMENTS[symbol])
        validate_page_window(rows, chunk)
        raw_pages.append(raw)
        parsed_pages.append(rows)
        page_records.append(raw_page_evidence(raw, request_url, fetched.get("request_id")))

    rows = merge_canonical_pages(parsed_pages)
    validate_candle_rows(rows)
    gap_ledger = build_gap_ledger(rows, expected_timestamps)
    _req(gap_ledger.get("unexpected_timestamps") == [], f"{symbol}: unexpected candles returned")
    bundle = aggregate_raw_bundle_bytes(raw_pages)
    window = declaration["acquisition_window"]
    acquired = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw_sha = aggregate_raw_bundle_sha256(raw_pages)
    canonical_sha = canonical_rows_sha256(rows)
    manifest = {
        "contract_version": "RND-historical-snapshot-v0.1",
        "snapshot_id": (
            f"OANDA-{symbol}-M5-{window['start_utc'].replace(':', '').replace('-', '')}-"
            f"{window['end_utc'].replace(':', '').replace('-', '')}-{raw_sha[:16]}"
        ),
        "sha256": raw_sha,
        "canonical_rows_sha256": canonical_sha,
        "provider": "OANDA",
        "source_instrument": INSTRUMENTS[symbol],
        "symbol": symbol,
        "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "start_utc": window["start_utc"],
        "end_utc": window["end_utc"],
        "complete": True,
        "complete_candles_only": True,
        "timestamp_grid_seconds": 300,
        "row_count": len(rows),
        "provenance": (
            "OANDA fxTrade Practice account instrument candles; RND-0054 GET-only "
            "prospective acquisition; explicit wall-clock M5 gap ledger; account identity excluded."
        ),
        "acquired_utc": acquired,
        "immutable": True,
    }
    summary = {
        "state": "SEALED",
        "page_count": len(raw_pages),
        "row_count": len(rows),
        "aggregate_raw_bundle_sha256": raw_sha,
        "canonical_rows_sha256": canonical_sha,
        "pages": page_records,
        "gap_ledger": gap_ledger,
    }

    symbol_dir = Path(target) / symbol
    raw_dir = symbol_dir / "raw"
    raw_dir.mkdir(parents=True)
    for i, raw in enumerate(raw_pages, 1):
        (raw_dir / f"page-{i:04d}.json").write_bytes(raw)
    (symbol_dir / "raw_bundle.bin").write_bytes(bundle)
    _write_json(symbol_dir / "canonical_rows.json", rows)
    _write_json(symbol_dir / "page_evidence.json", page_records)
    _write_json(symbol_dir / "gap_ledger.json", gap_ledger)
    _write_json(symbol_dir / "evidence_summary.json", summary)
    _write_json(symbol_dir / "snapshot_manifest.json", manifest)
    return manifest


def acquire_window(start_utc, end_utc, output_dir, repo_root, *, token=None, account_id=None, page_fetcher=fetch_page):
    expected = wall_clock_m5(start_utc, end_utc)
    declaration = acquisition_declaration(start_utc, end_utc)
    token = token if token is not None else os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = account_id if account_id is not None else os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    _req(isinstance(token, str) and token, "required OANDA Practice runtime token absent")
    _req(isinstance(account_id, str) and account_id, "required OANDA Practice account id absent")

    final_target = validate_output_target(output_dir, repo_root)
    final_target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rnd0054-stage-", dir=str(final_target.parent)))
    try:
        manifests = {}
        for symbol in SYMBOLS:
            manifests[symbol] = acquire_symbol_gap_aware(
                declaration, symbol, token, account_id, expected, stage, page_fetcher=page_fetcher
            )
        receipt = {
            "task_id": "RND-0054",
            "candidate_id": CANDIDATE_ID,
            "candidate_fingerprint": CANDIDATE_FINGERPRINT,
            "acquisition_window": declaration["acquisition_window"],
            "symbols": list(SYMBOLS),
            "strategy_evaluation": False,
            "reserved_final_access": False,
            "broker_writes": False,
            "capital_authority": False,
            "automatic_promotion": False,
            "manifests": manifests,
        }
        _write_json(stage / "rnd0054_acquisition_receipt.json", receipt)
        stage.rename(final_target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return final_target
