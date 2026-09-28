#!/usr/bin/env python3
"""RND-0028 controlled OANDA Practice historical acquisition runner.

The committed declaration is intentionally UNBOUND_WINDOW, so this runner fails
closed until a later human-approved declaration binds a research window.
Credentials are read from environment variables and are never written to the
sealed evidence package.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from historical_data_reconstruction import (  # noqa: E402
    canonical_rows_sha256,
    validate_snapshot_evidence,
)
from oanda_historical_acquisition import (  # noqa: E402
    INSTRUMENTS,
    aggregate_raw_bundle_bytes,
    aggregate_raw_bundle_sha256,
    build_candle_url,
    build_gap_ledger,
    evidence_summary,
    fetch_page,
    merge_canonical_pages,
    parse_page,
    plan_chunks,
    raw_page_evidence,
    validate_declaration,
    validate_output_target,
    validate_page_window,
)


def _json(path):
    return json.loads(Path(path).read_text())


def _write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def acquire_symbol(declaration, symbol, token, account_id, expected_timestamps, target):
    chunks = plan_chunks(declaration)
    raw_pages = []
    parsed_pages = []
    page_records = []

    for chunk in chunks:
        request_url = build_candle_url(declaration, account_id, symbol, chunk)
        fetched = fetch_page(request_url, token)
        raw = fetched["raw_bytes"]
        rows = parse_page(raw, INSTRUMENTS[symbol])
        validate_page_window(rows, chunk)
        raw_pages.append(raw)
        parsed_pages.append(rows)
        page_records.append(
            raw_page_evidence(raw, request_url, fetched.get("request_id"))
        )

    rows = merge_canonical_pages(parsed_pages)
    gap_ledger = build_gap_ledger(rows, expected_timestamps)
    summary = evidence_summary(raw_pages, rows, page_records, gap_ledger)
    bundle = aggregate_raw_bundle_bytes(raw_pages)

    window = declaration["acquisition_window"]
    acquired = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snapshot_id = (
        f"OANDA-{symbol}-M5-"
        f"{window['start_utc'].replace(':', '').replace('-', '')}-"
        f"{window['end_utc'].replace(':', '').replace('-', '')}-"
        f"{summary['aggregate_raw_bundle_sha256'][:16]}"
    )
    manifest = {
        "contract_version": "RND-historical-snapshot-v0.1",
        "snapshot_id": snapshot_id,
        "sha256": aggregate_raw_bundle_sha256(raw_pages),
        "canonical_rows_sha256": canonical_rows_sha256(rows),
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
            "OANDA fxTrade Practice account instrument candles; RND-0028 GET-only "
            "acquisition; page RequestIDs retained; account identity excluded."
        ),
        "acquired_utc": acquired,
        "immutable": True,
    }
    validate_snapshot_evidence(manifest, bundle, rows, expected_timestamps)

    symbol_dir = target / symbol
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--declaration",
        default=str(ROOT / "rnd" / "research" / "OANDA_HISTORICAL_ACQUISITION_DECLARATION.json"),
    )
    parser.add_argument("--expected-timestamps", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--symbol", action="append", choices=sorted(INSTRUMENTS))
    args = parser.parse_args()

    declaration = _json(args.declaration)
    validate_declaration(declaration)
    if declaration["state"] != "ACQUISITION_READY":
        raise SystemExit("FAIL_CLOSED: acquisition window is not human-approved")

    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    if not token or not account_id:
        raise SystemExit("FAIL_CLOSED: required OANDA Practice runtime credentials are absent")

    schedule = _json(args.expected_timestamps)
    symbols = args.symbol or sorted(INSTRUMENTS)
    if not isinstance(schedule, dict) or any(
        s not in schedule or not isinstance(schedule[s], list) for s in symbols
    ):
        raise SystemExit("FAIL_CLOSED: expected timestamp schedule missing selected symbol")

    final_target = validate_output_target(args.output, ROOT)
    final_target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rnd0028-stage-", dir=str(final_target.parent)))
    try:
        manifests = {}
        for symbol in symbols:
            manifests[symbol] = acquire_symbol(
                declaration, symbol, token, account_id, schedule[symbol], stage
            )
        _write_json(stage / "acquisition_manifests.json", manifests)
        stage.rename(final_target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    print("RND0028_ACQUISITION: SEALED")
    print(f"symbols={','.join(symbols)}")
    print(f"output={final_target}")


if __name__ == "__main__":
    main()
