#!/usr/bin/env python3
"""RND-0047 first prospective fresh-validation evidence acquisition.

GET-only OANDA PRACTICE candle acquisition and immutable sealing. No strategy
signals, trades, equity, validation decision, reserved-final access, broker
writes, or capital authority are permitted here.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
sys.path.insert(0, str(ORCH))

from rnd0047_fresh_validation_gate import (  # noqa: E402
    SYMBOLS,
    validate_declaration as validate_rnd0047_declaration,
)
from oanda_historical_acquisition import (  # noqa: E402
    BASE_COMMIT,
    EXPECTED_AUTHORITY,
    EXPECTED_RESERVED,
    INSTRUMENTS,
    VERSION,
    validate_output_target,
)
from oanda_historical_acquire import acquire_symbol  # noqa: E402


def _json(path):
    return json.loads(Path(path).read_text())


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def _generic_declaration(rnd47):
    window = rnd47["acquisition_window"]
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
            "start_utc": window["start_utc"],
            "end_utc": window["end_utc"],
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


def _expected_timestamps(start_utc, end_utc):
    start = datetime.fromisoformat(start_utc[:-1] + "+00:00")
    end = datetime.fromisoformat(end_utc[:-1] + "+00:00")
    out = []
    cursor = start
    while cursor < end:
        out.append(cursor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        cursor += timedelta(minutes=5)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--authorization",
        default=str(ROOT / "rnd" / "research" / "RND0047_FRESH_ACQUISITION_AUTHORIZATION.json"),
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    authorization = _json(args.authorization)
    gate = validate_rnd0047_declaration(authorization, require_acquisition_authority=True)

    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    if not token or not account_id:
        raise SystemExit("FAIL_CLOSED: required OANDA Practice runtime credentials are absent")

    declaration = _generic_declaration(authorization)
    expected = _expected_timestamps(gate["start_utc"], gate["end_utc"])
    if not expected:
        raise SystemExit("FAIL_CLOSED: empty prospective acquisition window")

    final_target = validate_output_target(args.output, ROOT)
    final_target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rnd0047-stage-", dir=str(final_target.parent)))
    try:
        manifests = {}
        for symbol in SYMBOLS:
            manifests[symbol] = acquire_symbol(
                declaration, symbol, token, account_id, expected, stage
            )
        receipt = {
            "task_id": "RND-0047",
            "candidate_id": authorization["candidate_id"],
            "candidate_fingerprint": authorization["candidate_fingerprint"],
            "acquisition_window": authorization["acquisition_window"],
            "symbols": list(SYMBOLS),
            "strategy_evaluation": False,
            "reserved_final_access": False,
            "broker_writes": False,
            "capital_authority": False,
            "manifests": manifests,
        }
        _write_json(stage / "rnd0047_acquisition_receipt.json", receipt)
        stage.rename(final_target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    print("RND0047_FRESH_VALIDATION_ACQUISITION: SEALED")
    print(f"candidate_fingerprint={authorization['candidate_fingerprint']}")
    print(f"window={gate['start_utc']}..{gate['end_utc']}")
    print(f"symbols={','.join(SYMBOLS)}")
    print("strategy_evaluation=FALSE")
    print("reserved_final_access=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"output={final_target}")


if __name__ == "__main__":
    main()
