#!/usr/bin/env python3
"""Generic structural verifier for prospective RND-0054 tranches.

No strategy evaluation, signal generation, trade simulation, validation outcome
classification, broker writes, reserved-final access, or capital authority.
Provider/market gaps are permitted only when they are explicit in the sealed gap
ledger and exactly reconcile to the declared wall-clock M5 window.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from historical_data_reconstruction import canonical_rows_sha256, validate_candle_rows
from rnd0054_ledger import (
    CANDIDATE_ID,
    CANDIDATE_FINGERPRINT,
    SYMBOLS,
    EARLIEST_READOUT_UTC,
)


class RND0054VerifyError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0054VerifyError(message)


def _utc(value, role):
    _req(isinstance(value, str) and value.endswith("Z"), f"{role}: UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise RND0054VerifyError(f"{role}: invalid timestamp") from exc
    _req(int(dt.timestamp()) % 300 == 0, f"{role}: M5 boundary required")
    return dt


def _z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path):
    return json.loads(Path(path).read_text())


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _receipt_path(root):
    generic = root / "rnd0054_acquisition_receipt.json"
    legacy = root / "rnd0047_acquisition_receipt.json"
    if generic.is_file():
        return generic
    _req(legacy.is_file(), "acquisition receipt missing")
    return legacy


def _expected_instants(start_utc, end_utc):
    start = _utc(start_utc, "start_utc")
    end = _utc(end_utc, "end_utc")
    _req(start < end, "start must precede end")
    _req(end <= _utc(EARLIEST_READOUT_UTC, "readout boundary"), "window beyond readout boundary")
    out = []
    cursor = start
    while cursor < end:
        out.append(cursor)
        cursor += timedelta(minutes=5)
    return out


def _normalized_list(values, role):
    _req(isinstance(values, list), f"{role}: list required")
    return [_utc(value, role) for value in values]


def verify_tranche(root, expected_start_utc, expected_end_utc):
    root = Path(root).expanduser().resolve()
    _req(root.is_dir(), "tranche directory missing")
    expected = _expected_instants(expected_start_utc, expected_end_utc)
    expected_set = set(expected)
    start = expected[0]
    end = _utc(expected_end_utc, "end_utc")

    receipt = _load(_receipt_path(root))
    _req(receipt.get("candidate_id") == CANDIDATE_ID, "candidate id mismatch")
    _req(receipt.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(receipt.get("symbols") == list(SYMBOLS), "symbol universe mismatch")
    _req(receipt.get("strategy_evaluation") is False, "strategy evaluation prohibited")
    _req(receipt.get("reserved_final_access") is False, "reserved-final access prohibited")
    _req(receipt.get("broker_writes") is False, "broker writes prohibited")
    _req(receipt.get("capital_authority") is False, "capital authority prohibited")
    window = receipt.get("acquisition_window") or {}
    _req(window.get("start_utc") == expected_start_utc, "tranche start mismatch")
    _req(window.get("end_utc") == expected_end_utc, "tranche end mismatch")

    hashes = {}
    for symbol in SYMBOLS:
        sdir = root / symbol
        manifest = _load(sdir / "snapshot_manifest.json")
        rows = _load(sdir / "canonical_rows.json")
        gap = _load(sdir / "gap_ledger.json")
        raw = sdir / "raw_bundle.bin"

        _req(manifest.get("symbol") == symbol, f"{symbol}: manifest symbol mismatch")
        _req(manifest.get("provider") == "OANDA", f"{symbol}: provider mismatch")
        _req(manifest.get("timeframe") == "M5", f"{symbol}: timeframe mismatch")
        _req(manifest.get("price_components") == ["bid", "ask", "mid"], f"{symbol}: price components mismatch")
        _req(manifest.get("start_utc") == expected_start_utc, f"{symbol}: start mismatch")
        _req(manifest.get("end_utc") == expected_end_utc, f"{symbol}: end mismatch")
        _req(manifest.get("complete") is True, f"{symbol}: manifest incomplete")
        _req(manifest.get("complete_candles_only") is True, f"{symbol}: incomplete candles allowed")
        _req(manifest.get("immutable") is True, f"{symbol}: snapshot not immutable")

        validate_candle_rows(rows)
        actual_instants = [_utc(row.get("timestamp_utc"), f"{symbol}: timestamp") for row in rows]
        _req(actual_instants == sorted(actual_instants), f"{symbol}: timestamps out of order")
        _req(len(actual_instants) == len(set(actual_instants)), f"{symbol}: duplicate timestamps")
        _req(all(start <= ts < end for ts in actual_instants), f"{symbol}: timestamp outside declared window")
        _req(all(ts in expected_set for ts in actual_instants), f"{symbol}: unexpected M5 timestamp")
        _req(manifest.get("row_count") == len(rows), f"{symbol}: row count mismatch")

        canonical_sha = canonical_rows_sha256(rows)
        raw_sha = _sha(raw)
        _req(canonical_sha == manifest.get("canonical_rows_sha256"), f"{symbol}: canonical SHA mismatch")
        _req(raw_sha == manifest.get("sha256"), f"{symbol}: raw SHA mismatch")

        _req(isinstance(gap, dict), f"{symbol}: structured gap ledger required")
        missing = sorted(expected_set - set(actual_instants))
        unexpected = sorted(set(actual_instants) - expected_set)
        ledger_missing = sorted(_normalized_list(gap.get("missing_timestamps"), f"{symbol}: missing timestamp"))
        ledger_unexpected = sorted(_normalized_list(gap.get("unexpected_timestamps"), f"{symbol}: unexpected timestamp"))
        _req(gap.get("expected_count") == len(expected), f"{symbol}: gap expected count mismatch")
        _req(gap.get("actual_count") == len(rows), f"{symbol}: gap actual count mismatch")
        _req(ledger_missing == missing, f"{symbol}: gap ledger missing timestamps mismatch")
        _req(ledger_unexpected == unexpected == [], f"{symbol}: unexpected timestamps present")
        _req(isinstance(gap.get("complete"), bool), f"{symbol}: gap complete flag invalid")
        _req(gap.get("complete") is (len(missing) == 0), f"{symbol}: gap complete flag mismatch")

        hashes[symbol] = {
            "raw_sha256": raw_sha,
            "canonical_sha256": canonical_sha,
        }

    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_fingerprint": CANDIDATE_FINGERPRINT,
        "symbols": list(SYMBOLS),
        "start_utc": expected_start_utc,
        "end_utc": expected_end_utc,
        "hashes": hashes,
        "integrity_pass": True,
        "strategy_evaluation": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }
