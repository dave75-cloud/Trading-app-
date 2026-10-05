#!/usr/bin/env python3
"""RND-0048 Tranche 002 weekly prospective acquisition.

Acquisition/sealing only. No Q003 signals, trades, returns, equity, drawdown,
validation decision, reserved-final access, broker writes, or capital authority.
The runner fails closed until the entire authorized weekly window has elapsed.
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

from rnd0047_fresh_validation_gate import CANDIDATE_FINGERPRINT, SYMBOLS  # noqa: E402
from oanda_historical_acquisition import (  # noqa: E402
    BASE_COMMIT,
    EXPECTED_AUTHORITY,
    EXPECTED_RESERVED,
    INSTRUMENTS,
    VERSION,
    validate_output_target,
)
from oanda_historical_acquire import acquire_symbol  # noqa: E402

AUTH = ROOT / "rnd" / "research" / "RND0048_TRANCHE_002_AUTHORIZATION.json"
EXPECTED_START = "2026-10-05T07:35:00Z"
EXPECTED_END = "2026-10-12T07:35:00Z"


def _json(path):
    return json.loads(Path(path).read_text())


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def _utc(text):
    return datetime.fromisoformat(text[:-1] + "+00:00").astimezone(timezone.utc)


def _validate_authorization(value):
    if value.get("task_id") != "RND-0048" or value.get("tranche_id") != "002":
        raise SystemExit("FAIL_CLOSED: tranche authorization identity mismatch")
    if value.get("state") != "AUTHORIZED_WAITING_FOR_WINDOW_CLOSE":
        raise SystemExit("FAIL_CLOSED: tranche authorization state mismatch")
    if value.get("candidate_id") != "Q003" or value.get("candidate_fingerprint") != CANDIDATE_FINGERPRINT:
        raise SystemExit("FAIL_CLOSED: candidate fingerprint mismatch")
    if value.get("previous_tranche_id") != "001" or value.get("previous_end_utc") != EXPECTED_START:
        raise SystemExit("FAIL_CLOSED: previous tranche continuity mismatch")
    window = value.get("acquisition_window") or {}
    if window.get("start_utc") != EXPECTED_START or window.get("end_utc") != EXPECTED_END:
        raise SystemExit("FAIL_CLOSED: weekly acquisition window mismatch")
    if tuple(value.get("symbols", ())) != tuple(SYMBOLS):
        raise SystemExit("FAIL_CLOSED: symbol universe changed")
    if value.get("timeframe") != "M5" or value.get("price_components") != ["bid", "ask", "mid"]:
        raise SystemExit("FAIL_CLOSED: market-data specification changed")
    for key in ("complete_candles_only", "human_authorized", "early_run_prohibited"):
        if value.get(key) is not True:
            raise SystemExit(f"FAIL_CLOSED: {key} must be TRUE")
    for key in ("synthetic_fill", "strategy_evaluation", "reserved_final_access", "broker_writes", "capital_authority"):
        if value.get(key) is not False:
            raise SystemExit(f"FAIL_CLOSED: {key} must be FALSE")
    return window


def _generic_declaration(window):
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
    start, end = _utc(start_utc), _utc(end_utc)
    out, cursor = [], start
    while cursor < end:
        out.append(cursor.strftime("%Y-%m-%dT%H:%M:%SZ"))
        cursor += timedelta(minutes=5)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    auth = _json(AUTH)
    window = _validate_authorization(auth)
    now = datetime.now(timezone.utc)
    end = _utc(EXPECTED_END)
    if now < end:
        raise SystemExit(f"FAIL_CLOSED: weekly window not closed until {EXPECTED_END}")

    token = os.environ.get("OANDA_PRACTICE_TOKEN")
    account_id = os.environ.get("OANDA_PRACTICE_ACCOUNT_ID")
    if not token or not account_id:
        raise SystemExit("FAIL_CLOSED: required OANDA Practice runtime credentials are absent")

    declaration = _generic_declaration(window)
    expected = _expected_timestamps(EXPECTED_START, EXPECTED_END)
    final_target = validate_output_target(args.output, ROOT)
    final_target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rnd0048-t002-stage-", dir=str(final_target.parent)))
    try:
        manifests = {}
        for symbol in SYMBOLS:
            manifests[symbol] = acquire_symbol(declaration, symbol, token, account_id, expected, stage)
        receipt = {
            "task_id": "RND-0048",
            "tranche_id": "002",
            "candidate_id": "Q003",
            "candidate_fingerprint": CANDIDATE_FINGERPRINT,
            "acquisition_window": dict(window),
            "symbols": list(SYMBOLS),
            "strategy_evaluation": False,
            "reserved_final_access": False,
            "broker_writes": False,
            "capital_authority": False,
            "manifests": manifests,
        }
        _write_json(stage / "rnd0048_tranche002_receipt.json", receipt)
        stage.rename(final_target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    print("RND0048_TRANCHE_002_ACQUISITION: SEALED")
    print(f"candidate_fingerprint={CANDIDATE_FINGERPRINT}")
    print(f"window={EXPECTED_START}..{EXPECTED_END}")
    print("symbols=" + ",".join(SYMBOLS))
    print("strategy_evaluation=FALSE")
    print("reserved_final_access=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"output={final_target}")


if __name__ == "__main__":
    main()
