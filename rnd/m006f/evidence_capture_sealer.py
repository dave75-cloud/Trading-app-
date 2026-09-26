#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
from pathlib import Path

from market_evidence_contract import VERSION, validate_record


CAPTURE_VERSION = "M006f-capture-source-v0.1"

PAIRS = {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}
ENTRY_LEGS = {"entry", "reversal_entry"}
EXIT_LEGS = {"exit", "reversal_exit"}
LEGS = ENTRY_LEGS | EXIT_LEGS


class CaptureError(ValueError):
    pass


def finite_positive(value, name):
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise CaptureError(f"{name} must be numeric")

    if not math.isfinite(x) or x <= 0:
        raise CaptureError(f"{name} must be positive and finite")

    return x


def pair_price(snapshot, pair):
    prices = snapshot.get("prices")
    if not isinstance(prices, dict):
        raise CaptureError("prices must be an object")

    row = prices.get(pair)
    if not isinstance(row, dict):
        raise CaptureError(f"missing price evidence for {pair}")

    bid = finite_positive(row.get("bid"), f"{pair}.bid")
    ask = finite_positive(row.get("ask"), f"{pair}.ask")

    if ask < bid:
        raise CaptureError(f"{pair}: ask must be >= bid")

    return bid, ask, (bid + ask) / 2.0


def conversion(snapshot, pair, leg):
    _, _, aud_mid = pair_price(snapshot, "AUDUSD")

    if pair == "AUDUSD":
        if leg in ENTRY_LEGS:
            return "base_to_aud", 1.0
        return "quote_to_aud", 1.0 / aud_mid

    _, _, pair_mid = pair_price(snapshot, pair)

    if pair in {"EURUSD", "GBPUSD"}:
        if leg in ENTRY_LEGS:
            return "base_to_aud", pair_mid / aud_mid
        return "quote_to_aud", 1.0 / aud_mid

    if pair == "USDJPY":
        if leg in ENTRY_LEGS:
            return "base_to_aud", 1.0 / aud_mid
        return "quote_to_aud", 1.0 / (pair_mid * aud_mid)

    raise CaptureError(f"unsupported pair: {pair}")


def seal(snapshot_path, artifact_label=None):
    raw = snapshot_path.read_bytes()
    snapshot = json.loads(raw.decode("utf-8"))

    if snapshot.get("capture_version") != CAPTURE_VERSION:
        raise CaptureError("unsupported capture_version")

    event_id = str(snapshot.get("event_id", "")).strip()
    if not event_id:
        raise CaptureError("event_id is required")

    leg = str(snapshot.get("leg", "")).strip()
    if leg not in LEGS:
        raise CaptureError("unsupported leg")

    pair = str(snapshot.get("pair", "")).strip().upper()
    if pair not in PAIRS:
        raise CaptureError("unsupported pair")

    bid, ask, _ = pair_price(snapshot, pair)

    factor_name, factor = conversion(
        snapshot,
        pair,
        leg,
    )

    record = {
        "contract_version": VERSION,
        "event_id": event_id,
        "leg": leg,
        "pair": pair,
        "event_timestamp_utc": snapshot.get(
            "event_timestamp_utc"
        ),
        "price_timestamp_utc": snapshot.get(
            "price_timestamp_utc"
        ),
        "bid": bid,
        "ask": ask,
        factor_name: factor,
        "source_provider": str(
            snapshot.get("source_provider", "")
        ).strip(),
        "source_artifact": (
            artifact_label
            if artifact_label
            else snapshot_path.name
        ),
        "source_artifact_sha256": hashlib.sha256(raw).hexdigest(),
    }

    # Reuse the frozen RND-0012 contract as the final gate.
    validate_record(record)

    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--artifact-label", default=None)
    args = ap.parse_args()

    record = seal(
        Path(args.snapshot),
        artifact_label=args.artifact_label,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(record, sort_keys=True) + "\n"
    )

    print("M006F_EVIDENCE_CAPTURE_SEALER: PASS")
    print("records=1")
    print("network_capability=FALSE")
    print("automatic_promotion=FALSE")
    print("human_review_required=TRUE")


if __name__ == "__main__":
    main()
