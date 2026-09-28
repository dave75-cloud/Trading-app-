#!/usr/bin/env python3
"""RND-0030 year-sharded OANDA Practice historical quarantine runner.

This runner may acquire historical candle bytes through the pre-existing
GET-only Practice candle capability. It cannot seal unresolved history and has
no strategy, order, trade, position, capital, promotion or merge authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from historical_data_reconstruction import canonical_rows_sha256  # noqa: E402
from oanda_historical_acquisition import (  # noqa: E402
    INSTRUMENTS,
    aggregate_raw_bundle_bytes,
    aggregate_raw_bundle_sha256,
    build_candle_url,
    fetch_page,
    merge_canonical_pages,
    parse_page,
    plan_chunks,
    raw_page_evidence,
    validate_declaration as validate_acquisition_declaration,
    validate_page_window,
)
from oanda_market_calendar import (  # noqa: E402
    SYMBOLS,
    YEARS,
    build_discrepancy_ledger,
    schedule_sha256,
    standard_session_schedule,
    validate_declaration as validate_calendar_declaration,
    year_shards,
)


def _json(path):
    return json.loads(Path(path).read_text())


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write_json(path, value):
    path.write_bytes(_json_bytes(value))


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _source_declaration_sha256(value):
    return _sha256_bytes(_json_bytes(value))


def _validate_source_binding(acquisition, calendar):
    validate_acquisition_declaration(acquisition)
    validate_calendar_declaration(calendar)
    horizon = calendar["horizon"]
    if acquisition["state"] != "ACQUISITION_READY" or acquisition["acquisition_window"] != {
        "start_utc": horizon["start_utc"],
        "end_utc": horizon["end_utc"],
        "human_approved": True,
    }:
        raise SystemExit("FAIL_CLOSED: acquisition declaration is not bound to RND-0030 horizon")
    reserved = calendar["reserved_final_test"]
    if (
        acquisition["reserved_test"].get("start_utc") != reserved["start_utc"]
        or acquisition["reserved_test"].get("end_utc") != reserved["end_utc"]
        or acquisition["reserved_test"].get("state") != "SEALED_BOUNDARY_BOUND"
    ):
        raise SystemExit("FAIL_CLOSED: acquisition/final-test boundary mismatch")
    return True


def _shard_declaration(acquisition, shard):
    value = copy.deepcopy(acquisition)
    value["state"] = "ACQUISITION_READY"
    value["acquisition_window"] = {
        "start_utc": shard["start_utc"],
        "end_utc": shard["end_utc"],
        "human_approved": True,
    }
    validate_acquisition_declaration(value)
    return value


def _validate_selection(symbols, years):
    if any(symbol not in SYMBOLS for symbol in symbols):
        raise SystemExit("FAIL_CLOSED: unsupported symbol selection")
    if any(year not in YEARS for year in years):
        raise SystemExit("FAIL_CLOSED: year outside predeclared horizon")


def acquire_shard(acquisition, calendar, symbol, shard, token, account_id, stage, delay):
    _validate_source_binding(acquisition, calendar)
    value = _shard_declaration(acquisition, shard)
    expected = standard_session_schedule(shard["start_utc"], shard["end_utc"])
    chunks = plan_chunks(value)

    raw_pages = []
    parsed_pages = []
    page_records = []

    for index, chunk in enumerate(chunks):
        request_url = build_candle_url(value, account_id, symbol, chunk)
        fetched = fetch_page(request_url, token)
        raw = fetched["raw_bytes"]
        rows = parse_page(raw, INSTRUMENTS[symbol])
        validate_page_window(rows, chunk)
        raw_pages.append(raw)
        parsed_pages.append(rows)
        page_records.append(
            raw_page_evidence(raw, request_url, fetched.get("request_id"))
        )
        if index + 1 < len(chunks):
            time.sleep(delay)

    rows = merge_canonical_pages(parsed_pages)
    actual_timestamps = [row["timestamp_utc"] for row in rows]
    discrepancy = build_discrepancy_ledger(actual_timestamps, expected)
    bundle = aggregate_raw_bundle_bytes(raw_pages)

    raw_dir = stage / "raw"
    raw_dir.mkdir(parents=True)
    for i, raw in enumerate(raw_pages, 1):
        (raw_dir / f"page-{i:04d}.json").write_bytes(raw)

    bundle_path = stage / "raw_bundle.bin"
    canonical_path = stage / "canonical_rows.json"
    page_evidence_path = stage / "page_evidence.json"
    schedule_path = stage / "standard_schedule.json"
    discrepancy_path = stage / "discrepancy_ledger.json"

    bundle_path.write_bytes(bundle)
    _write_json(canonical_path, rows)
    _write_json(page_evidence_path, page_records)
    _write_json(schedule_path, expected)
    _write_json(discrepancy_path, discrepancy)

    acquired = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = {
        "contract_version": "RND-oanda-quarantine-shard-v0.1",
        "task_id": "RND-0030",
        "status": (
            "QUARANTINED_STANDARD_MATCH"
            if discrepancy["resolved"]
            else "QUARANTINED_UNRESOLVED_DISCREPANCIES"
        ),
        "symbol": symbol,
        "source_instrument": INSTRUMENTS[symbol],
        "year": shard["year"],
        "start_utc": shard["start_utc"],
        "end_utc": shard["end_utc"],
        "provider": "OANDA",
        "environment": "PRACTICE",
        "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "complete_candles_only": True,
        "row_count": len(rows),
        "expected_standard_session_count": len(expected),
        "raw_page_count": len(raw_pages),
        "aggregate_raw_bundle_sha256": aggregate_raw_bundle_sha256(raw_pages),
        "canonical_rows_sha256": canonical_rows_sha256(rows),
        "standard_schedule_sha256": schedule_sha256(expected),
        "raw_bundle_file_sha256": _sha256_file(bundle_path),
        "canonical_rows_file_sha256": _sha256_file(canonical_path),
        "page_evidence_file_sha256": _sha256_file(page_evidence_path),
        "standard_schedule_file_sha256": _sha256_file(schedule_path),
        "discrepancy_ledger_file_sha256": _sha256_file(discrepancy_path),
        "source_acquisition_declaration_sha256": _source_declaration_sha256(acquisition),
        "source_calendar_declaration_sha256": _source_declaration_sha256(calendar),
        "missing_count": discrepancy["missing_count"],
        "unexpected_count": discrepancy["unexpected_count"],
        "seal_allowed": False,
        "seal_block_reason": (
            "RND-0030_QUARANTINE_ONLY"
            if discrepancy["resolved"]
            else "UNRESOLVED_CALENDAR_DISCREPANCIES"
        ),
        "account_identity_recorded": False,
        "credentials_recorded": False,
        "acquired_utc": acquired,
    }
    _write_json(stage / "quarantine_manifest.json", manifest)
    return manifest


def verify_existing_shard(path, symbol, shard, acquisition, calendar):
    path = Path(path)
    manifest_path = path / "quarantine_manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        manifest = _json(manifest_path)
    except Exception:
        return False
    expected_identity = {
        "contract_version": "RND-oanda-quarantine-shard-v0.1",
        "task_id": "RND-0030",
        "symbol": symbol,
        "source_instrument": INSTRUMENTS[symbol],
        "year": shard["year"],
        "start_utc": shard["start_utc"],
        "end_utc": shard["end_utc"],
        "provider": "OANDA",
        "environment": "PRACTICE",
        "timeframe": "M5",
        "price_components": ["bid", "ask", "mid"],
        "complete_candles_only": True,
        "seal_allowed": False,
        "account_identity_recorded": False,
        "credentials_recorded": False,
    }
    if any(manifest.get(k) != v for k, v in expected_identity.items()):
        return False
    if manifest.get("source_acquisition_declaration_sha256") != _source_declaration_sha256(acquisition):
        return False
    if manifest.get("source_calendar_declaration_sha256") != _source_declaration_sha256(calendar):
        return False
    files = {
        "raw_bundle_file_sha256": "raw_bundle.bin",
        "canonical_rows_file_sha256": "canonical_rows.json",
        "page_evidence_file_sha256": "page_evidence.json",
        "standard_schedule_file_sha256": "standard_schedule.json",
        "discrepancy_ledger_file_sha256": "discrepancy_ledger.json",
    }
    for key, name in files.items():
        file_path = path / name
        if not file_path.is_file() or manifest.get(key) != _sha256_file(file_path):
            return False

    try:
        canonical_rows = _json(path / "canonical_rows.json")
        schedule = _json(path / "standard_schedule.json")
        discrepancy = _json(path / "discrepancy_ledger.json")
        page_evidence = _json(path / "page_evidence.json")
    except Exception:
        return False

    if canonical_rows_sha256(canonical_rows) != manifest.get("canonical_rows_sha256"):
        return False
    if schedule_sha256(schedule) != manifest.get("standard_schedule_sha256"):
        return False
    rebuilt = build_discrepancy_ledger(
        [row["timestamp_utc"] for row in canonical_rows], schedule
    )
    if rebuilt != discrepancy:
        return False

    raw_dir = path / "raw"
    raw_paths = sorted(raw_dir.glob("page-*.json")) if raw_dir.is_dir() else []
    if len(raw_paths) != manifest.get("raw_page_count") or len(page_evidence) != len(raw_paths):
        return False
    raw_pages = [item.read_bytes() for item in raw_paths]
    if aggregate_raw_bundle_sha256(raw_pages) != manifest.get("aggregate_raw_bundle_sha256"):
        return False
    if aggregate_raw_bundle_bytes(raw_pages) != (path / "raw_bundle.bin").read_bytes():
        return False
    for raw, record in zip(raw_pages, page_evidence):
        if hashlib.sha256(raw).hexdigest() != record.get("raw_sha256"):
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--acquisition-declaration",
        default=str(ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"),
    )
    parser.add_argument(
        "--calendar-declaration",
        default=str(ROOT / "rnd" / "research" / "OANDA_CALENDAR_QUARANTINE_DECLARATION.json"),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--symbol", action="append", choices=SYMBOLS)
    parser.add_argument("--year", action="append", type=int, choices=YEARS)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--request-delay-seconds", type=float, default=0.6)
    args = parser.parse_args()

    if args.request_delay_seconds < 0.5 or args.request_delay_seconds > 5.0:
        raise SystemExit("FAIL_CLOSED: request delay must be between 0.5 and 5.0 seconds")

    acquisition = _json(args.acquisition_declaration)
    calendar = _json(args.calendar_declaration)
    validate_acquisition_declaration(acquisition)
    validate_calendar_declaration(calendar)

    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    if not token or not account_id:
        raise SystemExit("FAIL_CLOSED: required OANDA Practice runtime credentials are absent")

    symbols = args.symbol or SYMBOLS
    years = args.year or YEARS
    _validate_selection(symbols, years)
    shard_by_year = {item["year"]: item for item in year_shards()}

    output = Path(args.output).expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        raise SystemExit("FAIL_CLOSED: quarantine output must remain outside repository")
    if output.exists() and not args.resume:
        raise SystemExit("FAIL_CLOSED: output exists; use a new target or verified --resume")
    output.mkdir(parents=True, exist_ok=True)

    completed = []
    skipped = []
    for symbol in symbols:
        for year in years:
            shard = shard_by_year[year]
            final = output / symbol / str(year)
            if final.exists():
                if args.resume and verify_existing_shard(final, symbol, shard, acquisition, calendar):
                    skipped.append(f"{symbol}:{year}")
                    continue
                raise SystemExit(
                    f"FAIL_CLOSED: existing shard failed verification or resume not authorized: {symbol}:{year}"
                )
            final.parent.mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=f".{year}-stage-", dir=str(final.parent)))
            try:
                manifest = acquire_shard(
                    acquisition, calendar, symbol, shard, token, account_id,
                    stage, args.request_delay_seconds,
                )
                stage.rename(final)
                completed.append({
                    "symbol": symbol,
                    "year": year,
                    "status": manifest["status"],
                    "missing_count": manifest["missing_count"],
                    "unexpected_count": manifest["unexpected_count"],
                })
            except Exception:
                shutil.rmtree(stage, ignore_errors=True)
                raise

    run_summary = {
        "contract_version": "RND-oanda-quarantine-run-v0.1",
        "task_id": "RND-0030",
        "completed": completed,
        "verified_skipped": skipped,
        "seal_authority": False,
        "strategy_evaluation_authority": False,
    }
    summary_name = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ.json")
    _write_json(output / summary_name, run_summary)

    print("RND0030_QUARANTINE: COMPLETE")
    print(f"completed_shards={len(completed)}")
    print(f"verified_skipped_shards={len(skipped)}")
    print("sealed=FALSE")
    print("strategy_evaluation=FALSE")
    print(f"output={output}")


if __name__ == "__main__":
    main()
