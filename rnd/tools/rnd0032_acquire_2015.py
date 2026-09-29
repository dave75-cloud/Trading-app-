#!/usr/bin/env python3
"""Bounded RND-0032 launcher: EURUSD/GBPUSD/USDJPY, UTC year 2015 only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "rnd" / "tools" / "oanda_historical_quarantine.py"
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")


def build_command(output, delay, resume=False):
    command = [
        sys.executable,
        str(RUNNER),
        "--output",
        str(output),
        "--year",
        "2015",
        "--request-delay-seconds",
        str(delay),
    ]
    for symbol in SYMBOLS:
        command.extend(["--symbol", symbol])
    if resume:
        command.append("--resume")
    return command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--request-delay-seconds", type=float, default=0.6)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.request_delay_seconds < 0.5 or args.request_delay_seconds > 5.0:
        raise SystemExit("FAIL_CLOSED: request delay must be between 0.5 and 5.0 seconds")

    output = Path(args.output).expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        raise SystemExit("FAIL_CLOSED: RND-0032 evidence must remain outside repository")

    result = subprocess.run(
        build_command(output, args.request_delay_seconds, args.resume),
        cwd=str(ROOT),
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)

    print("RND0032_ACQUISITION: COMPLETE")
    print("symbols=EURUSD,GBPUSD,USDJPY")
    print("year=2015")
    print("strategy_evaluation=FALSE")
    print("calendar_promotion=FALSE")


if __name__ == "__main__":
    main()
