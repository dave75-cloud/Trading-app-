#!/usr/bin/env python3
"""Verify sealed RND-0048 Tranche 002 evidence without evaluating Q003."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from historical_data_reconstruction import canonical_rows_sha256  # noqa: E402
from rnd0047_fresh_validation_gate import CANDIDATE_FINGERPRINT, SYMBOLS  # noqa: E402

EXPECTED_START = "2026-10-05T07:35:00Z"
EXPECTED_END = "2026-10-12T07:35:00Z"
EXPECTED_SLOTS = 7 * 24 * 12


class VerifyError(ValueError):
    pass


def req(condition, message):
    if not condition:
        raise VerifyError(message)


def load_json(path):
    return json.loads(Path(path).read_text())


def sha256_bytes(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(text):
    if not isinstance(text, str) or not text.endswith("Z"):
        raise VerifyError("invalid UTC timestamp")
    base = text[:-1]
    if "." in base:
        base = base.split(".", 1)[0]
    return datetime.fromisoformat(base + "+00:00").astimezone(timezone.utc)


def expected_grid():
    start, end = norm(EXPECTED_START), norm(EXPECTED_END)
    out, cursor = [], start
    while cursor < end:
        out.append(cursor)
        cursor += timedelta(minutes=5)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tranche", required=True)
    args = parser.parse_args()

    root = Path(args.tranche).expanduser().resolve()
    req(root.is_dir(), "tranche directory missing")
    receipt = load_json(root / "rnd0048_tranche002_receipt.json")
    req(receipt.get("task_id") == "RND-0048", "task mismatch")
    req(receipt.get("tranche_id") == "002", "tranche id mismatch")
    req(receipt.get("candidate_id") == "Q003", "candidate id mismatch")
    req(receipt.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    req(receipt.get("symbols") == list(SYMBOLS), "symbol universe mismatch")
    for key in ("strategy_evaluation", "reserved_final_access", "broker_writes", "capital_authority"):
        req(receipt.get(key) is False, f"{key}: authority drift")
    window = receipt.get("acquisition_window") or {}
    req(window.get("start_utc") == EXPECTED_START, "start mismatch")
    req(window.get("end_utc") == EXPECTED_END, "end mismatch")

    exp = expected_grid()
    req(len(exp) == EXPECTED_SLOTS, "internal expected-slot mismatch")
    summaries = {}
    for symbol in SYMBOLS:
        sdir = root / symbol
        manifest = load_json(sdir / "snapshot_manifest.json")
        rows = load_json(sdir / "canonical_rows.json")
        gap = load_json(sdir / "gap_ledger.json")
        raw = sdir / "raw_bundle.bin"

        req(manifest.get("symbol") == symbol, f"{symbol}: manifest symbol mismatch")
        req(manifest.get("provider") == "OANDA", f"{symbol}: provider mismatch")
        req(manifest.get("timeframe") == "M5", f"{symbol}: timeframe mismatch")
        req(manifest.get("price_components") == ["bid", "ask", "mid"], f"{symbol}: price component mismatch")
        req(manifest.get("start_utc") == EXPECTED_START and manifest.get("end_utc") == EXPECTED_END, f"{symbol}: window mismatch")
        req(manifest.get("complete") is True and manifest.get("complete_candles_only") is True, f"{symbol}: completeness drift")
        req(manifest.get("immutable") is True, f"{symbol}: snapshot not immutable")

        actual = [norm(r.get("timestamp_utc")) for r in rows]
        req(all(r.get("complete") is True for r in rows), f"{symbol}: incomplete canonical row")
        req(actual == sorted(actual), f"{symbol}: timestamps unordered")
        req(len(set(actual)) == len(actual), f"{symbol}: duplicate timestamps")
        req(all(EXPECTED_START <= t.strftime("%Y-%m-%dT%H:%M:%SZ") < EXPECTED_END for t in actual), f"{symbol}: timestamp outside window")

        csha = canonical_rows_sha256(rows)
        rsha = sha256_bytes(raw)
        req(csha == manifest.get("canonical_rows_sha256"), f"{symbol}: canonical SHA mismatch")
        req(rsha == manifest.get("sha256"), f"{symbol}: raw SHA mismatch")
        req(isinstance(gap, dict), f"{symbol}: gap ledger malformed")
        req(gap.get("expected_count") == EXPECTED_SLOTS, f"{symbol}: expected grid count mismatch")
        req(gap.get("actual_count") == len(rows), f"{symbol}: actual count mismatch")
        req(gap.get("unexpected_timestamps") == [], f"{symbol}: unexpected timestamp")
        # Real provider/market gaps are preserved rather than synthetically filled.
        req(gap.get("complete") is (len(gap.get("missing_timestamps", [])) == 0), f"{symbol}: gap completion flag inconsistent")

        summaries[symbol] = {
            "rows": len(rows),
            "missing": len(gap.get("missing_timestamps", [])),
            "raw_sha": rsha,
            "canonical_sha": csha,
        }

    print("RND0048_TRANCHE_002_VERIFY: PASS")
    print(f"candidate_fingerprint={CANDIDATE_FINGERPRINT}")
    print(f"window={EXPECTED_START}..{EXPECTED_END}")
    print("symbols=" + ",".join(SYMBOLS))
    print("strategy_evaluation=FALSE")
    print("reserved_final_access=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    for s in SYMBOLS:
        x = summaries[s]
        print(f"{s}_rows={x['rows']}")
        print(f"{s}_missing_expected_slots={x['missing']}")
        print(f"{s}_raw_sha256={x['raw_sha']}")
        print(f"{s}_canonical_sha256={x['canonical_sha']}")


if __name__ == "__main__":
    main()
