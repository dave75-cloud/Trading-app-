#!/usr/bin/env python3
"""Verify a sealed RND-0047 fresh-validation acquisition tranche.

Evidence integrity only. This script does not evaluate Q003, generate signals,
simulate trades, access reserved-final evidence, write to the broker, or grant
capital authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from historical_data_reconstruction import canonical_rows_sha256  # noqa: E402
from rnd0047_fresh_validation_gate import (  # noqa: E402
    CANDIDATE_FINGERPRINT,
    SYMBOLS,
)

EXPECTED_START = "2026-10-05T07:25:00Z"
EXPECTED_END = "2026-10-05T07:35:00Z"
EXPECTED_TIMESTAMPS = ["2026-10-05T07:25:00Z", "2026-10-05T07:30:00Z"]


class VerifyError(ValueError):
    pass


def req(condition, message):
    if not condition:
        raise VerifyError(message)


def load_json(path):
    return json.loads(Path(path).read_text())


def sha256_bytes(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tranche", required=True)
    args = parser.parse_args()

    root = Path(args.tranche).expanduser().resolve()
    req(root.is_dir(), "tranche directory missing")

    receipt = load_json(root / "rnd0047_acquisition_receipt.json")
    req(receipt.get("task_id") == "RND-0047", "receipt task mismatch")
    req(receipt.get("candidate_id") == "Q003", "candidate id mismatch")
    req(receipt.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    req(receipt.get("symbols") == list(SYMBOLS), "symbol universe mismatch")
    req(receipt.get("strategy_evaluation") is False, "strategy evaluation authority drift")
    req(receipt.get("reserved_final_access") is False, "reserved-final authority drift")
    req(receipt.get("broker_writes") is False, "broker-write authority drift")
    req(receipt.get("capital_authority") is False, "capital authority drift")
    window = receipt.get("acquisition_window") or {}
    req(window.get("start_utc") == EXPECTED_START, "tranche start mismatch")
    req(window.get("end_utc") == EXPECTED_END, "tranche end mismatch")

    rows_by_symbol = {}
    raw_sha_by_symbol = {}
    canonical_sha_by_symbol = {}

    for symbol in SYMBOLS:
        sdir = root / symbol
        manifest = load_json(sdir / "snapshot_manifest.json")
        rows = load_json(sdir / "canonical_rows.json")
        gap_ledger = load_json(sdir / "gap_ledger.json")
        raw_bundle = sdir / "raw_bundle.bin"

        req(manifest.get("symbol") == symbol, f"{symbol}: manifest symbol mismatch")
        req(manifest.get("provider") == "OANDA", f"{symbol}: provider mismatch")
        req(manifest.get("timeframe") == "M5", f"{symbol}: timeframe mismatch")
        req(manifest.get("price_components") == ["bid", "ask", "mid"], f"{symbol}: price components mismatch")
        req(manifest.get("start_utc") == EXPECTED_START, f"{symbol}: start mismatch")
        req(manifest.get("end_utc") == EXPECTED_END, f"{symbol}: end mismatch")
        req(manifest.get("complete") is True, f"{symbol}: manifest incomplete")
        req(manifest.get("complete_candles_only") is True, f"{symbol}: incomplete candles allowed")
        req(manifest.get("immutable") is True, f"{symbol}: snapshot not immutable")
        req(manifest.get("row_count") == 2, f"{symbol}: expected exactly two rows")
        req(len(rows) == 2, f"{symbol}: canonical row count mismatch")

        timestamps = [row.get("timestamp_utc") for row in rows]
        req(timestamps == EXPECTED_TIMESTAMPS, f"{symbol}: timestamp sequence mismatch")
        req(all(row.get("complete") is True for row in rows), f"{symbol}: incomplete canonical row")

        canonical_sha = canonical_rows_sha256(rows)
        req(canonical_sha == manifest.get("canonical_rows_sha256"), f"{symbol}: canonical SHA mismatch")
        raw_sha = sha256_bytes(raw_bundle)
        req(raw_sha == manifest.get("sha256"), f"{symbol}: raw bundle SHA mismatch")

        # With a two-slot tranche, any gap entry means the evidence is not a full
        # two-candle structural smoke test and must fail closed.
        req(gap_ledger in ([], {}), f"{symbol}: unexpected gap ledger entries")

        rows_by_symbol[symbol] = len(rows)
        raw_sha_by_symbol[symbol] = raw_sha
        canonical_sha_by_symbol[symbol] = canonical_sha

    print("RND0047_FRESH_TRANCHE_VERIFY: PASS")
    print(f"candidate_fingerprint={CANDIDATE_FINGERPRINT}")
    print(f"window={EXPECTED_START}..{EXPECTED_END}")
    print("symbols=" + ",".join(SYMBOLS))
    print("rows=" + ",".join(f"{s}:{rows_by_symbol[s]}" for s in SYMBOLS))
    print("strategy_evaluation=FALSE")
    print("reserved_final_access=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    for s in SYMBOLS:
        print(f"{s}_raw_sha256={raw_sha_by_symbol[s]}")
        print(f"{s}_canonical_sha256={canonical_sha_by_symbol[s]}")


if __name__ == "__main__":
    main()
