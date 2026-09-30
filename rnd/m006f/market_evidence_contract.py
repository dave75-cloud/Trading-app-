#!/usr/bin/env python3

import argparse
import json
import math
from datetime import datetime
from pathlib import Path


VERSION = "M006f-market-evidence-v0.1"

PAIRS = {
    "AUDUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
}

ENTRY_LEGS = {
    "entry",
    "reversal_entry",
}

EXIT_LEGS = {
    "exit",
    "reversal_exit",
}

LEGS = ENTRY_LEGS | EXIT_LEGS


class ContractError(ValueError):
    pass


def positive_number(value, name):
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ContractError(f"{name} must be numeric")

    if not math.isfinite(x) or x <= 0:
        raise ContractError(f"{name} must be positive and finite")

    return x


def utc_timestamp(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty UTC timestamp")

    text = value.strip()

    if text.endswith("Z"):
        parse_text = text[:-1] + "+00:00"
    else:
        parse_text = text

    try:
        dt = datetime.fromisoformat(parse_text)
    except ValueError:
        raise ContractError(f"{name} is not valid ISO-8601")

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ContractError(f"{name} must contain a UTC offset")

    if dt.utcoffset().total_seconds() != 0:
        raise ContractError(f"{name} must be UTC")

    return text


def validate_record(row):
    if not isinstance(row, dict):
        raise ContractError("record must be a JSON object")

    if row.get("contract_version") != VERSION:
        raise ContractError("unsupported contract_version")

    event_id = str(row.get("event_id", "")).strip()
    if not event_id:
        raise ContractError("event_id is required")

    leg = str(row.get("leg", "")).strip()
    if leg not in LEGS:
        raise ContractError("unsupported leg")

    pair = str(row.get("pair", "")).strip().upper()
    if pair not in PAIRS:
        raise ContractError("unsupported pair")

    utc_timestamp(
        row.get("event_timestamp_utc"),
        "event_timestamp_utc",
    )

    utc_timestamp(
        row.get("price_timestamp_utc"),
        "price_timestamp_utc",
    )

    bid = positive_number(row.get("bid"), "bid")
    ask = positive_number(row.get("ask"), "ask")

    if ask < bid:
        raise ContractError("ask must be >= bid")

    provider = str(row.get("source_provider", "")).strip()
    if not provider:
        raise ContractError("source_provider is required")

    artifact = str(row.get("source_artifact", "")).strip()
    if not artifact:
        raise ContractError("source_artifact is required")

    digest = str(row.get("source_artifact_sha256", "")).strip().lower()

    if (
        len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ):
        raise ContractError(
            "source_artifact_sha256 must be a 64-character hex digest"
        )

    if leg in ENTRY_LEGS:
        positive_number(
            row.get("base_to_aud"),
            "base_to_aud",
        )

        if row.get("quote_to_aud") not in (None, ""):
            raise ContractError(
                "entry leg must not provide quote_to_aud"
            )

    else:
        positive_number(
            row.get("quote_to_aud"),
            "quote_to_aud",
        )

        if row.get("base_to_aud") not in (None, ""):
            raise ContractError(
                "exit leg must not provide base_to_aud"
            )

    return {
        "event_id": event_id,
        "leg": leg,
        "pair": pair,
    }


def validate_rows(rows):
    seen = set()

    for index, row in enumerate(rows, 1):
        try:
            key_data = validate_record(row)
        except ContractError as exc:
            raise ContractError(
                f"record {index}: {exc}"
            ) from exc

        key = (
            key_data["event_id"],
            key_data["leg"],
        )

        if key in seen:
            raise ContractError(
                f"record {index}: duplicate event_id + leg"
            )

        seen.add(key)

    return {
        "contract_version": VERSION,
        "records": len(rows),
        "unique_event_legs": len(seen),
        "network_capability": False,
        "automatic_promotion": False,
        "human_review_required": True,
    }


def load_jsonl(path):
    rows = []

    for number, line in enumerate(
        path.read_text().splitlines(),
        1,
    ):
        if not line.strip():
            continue

        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(
                f"line {number}: invalid JSON"
            ) from exc

        rows.append(row)

    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    rows = load_jsonl(Path(args.input))
    result = validate_rows(rows)

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
