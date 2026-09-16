#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

SIGNAL_COLUMNS = [
    "run_date","signal_id","strategy_version","symbol","side","signal_timestamp",
    "expected_entry_timestamp","model_entry_price","observed_bid","observed_ask",
    "executable_entry_price","entry_slippage","requested_leverage",
    "assigned_leverage","allocation_status","rejection_or_resize_reason",
    "simultaneous_group_id","data_snapshot_hash"
]

POSITION_COLUMNS = [
    "signal_id","symbol","side","entry_timestamp","model_entry_price",
    "executable_entry_price","assigned_leverage","expected_exit_timestamp",
    "model_exit_price","executable_exit_timestamp","executable_exit_price",
    "gross_return","entry_cost","exit_cost","total_cost","net_shadow_return",
    "bars_held","mfe","mae","protocol_exception"
]

LEDGER_COLUMNS = [
    "ts","realized_pnl","unrealized_pnl","equity","drawdown","open_trades",
    "gross_exposure","aud_gross_exposure","eur_gross_exposure",
    "gbp_gross_exposure","usd_gross_exposure","jpy_gross_exposure"
]

DAILY_COLUMNS = [
    "run_date","signals_generated","accepted","resized","rejected",
    "missed_signals","data_quality_exceptions","entry_slippage_sum",
    "exit_slippage_sum","estimated_costs","control_return",
    "candidate_return","max_mtm_drawdown","specification_deviations",
    "review_status","reviewer_notes"
]

def write_empty(path: Path, columns: list[str]) -> None:
    pd.DataFrame(columns=columns).to_csv(path, index=False)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    run = Path(args.run_dir)
    raw = run / "raw"
    logs = run / "logs"
    reports = run / "reports"
    metadata = run / "metadata"

    for p in [raw, logs, reports, metadata]:
        p.mkdir(parents=True, exist_ok=True)

    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    frozen = metadata / "frozen_config.json"
    frozen.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    digest = hashlib.sha256(frozen.read_bytes()).hexdigest()
    (metadata / "frozen_config.sha256").write_text(digest + "\n")

    write_empty(logs / "signals.csv", SIGNAL_COLUMNS)
    write_empty(logs / "positions.csv", POSITION_COLUMNS)
    write_empty(logs / "ledger_5m.csv", LEDGER_COLUMNS)
    write_empty(logs / "daily_reconciliation.csv", DAILY_COLUMNS)

    (metadata / "status.txt").write_text("RUNNING\n")
    (reports / "README.txt").write_text(
        "M005 forward shadow run initialized. Do not alter frozen_config.json.\n"
    )

    print(f"Initialized M005 run: {run}")
    print(f"Frozen config SHA256: {digest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
