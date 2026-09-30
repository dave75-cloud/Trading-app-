#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

VERSION = "M006f-shadow-v0.1"
ALLOWED_PAIRS = {"AUDUSD", "EURUSD", "GBPUSD", "USDJPY"}
ALLOWED_ACTIONS = {"entry", "exit"}
ALLOWED_SIDES = {"long", "short"}


class ShadowError(ValueError):
    pass


@dataclass
class Position:
    side: str
    units: int
    entry_fill: float
    base_to_aud: float


def _positive_float(value: Any, name: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ShadowError(f"{name} must be numeric")
    if x <= 0:
        raise ShadowError(f"{name} must be positive")
    return x


def _validate_market(event: dict) -> tuple[float, float]:
    bid = _positive_float(event.get("bid"), "bid")
    ask = _positive_float(event.get("ask"), "ask")
    if ask < bid:
        raise ShadowError("ask must be >= bid")
    return bid, ask


def _slip(price: float, bps: float, direction: int) -> float:
    if bps < 0:
        raise ShadowError("slippage_bps must be >= 0")
    return price * (1.0 + direction * bps / 10000.0)


def _event_hash(events: list[dict], initial_equity_aud: float, slippage_bps: float) -> str:
    payload = {
        "version": VERSION,
        "initial_equity_aud": initial_equity_aud,
        "slippage_bps": slippage_bps,
        "events": events,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def simulate(
    events: list[dict],
    *,
    initial_equity_aud: float = 100000.0,
    slippage_bps: float = 0.0,
) -> dict:
    initial_equity_aud = _positive_float(initial_equity_aud, "initial_equity_aud")
    if slippage_bps < 0:
        raise ShadowError("slippage_bps must be >= 0")

    positions: dict[str, Position] = {}
    seen: set[str] = set()
    ledger: list[dict] = []
    equity = initial_equity_aud
    peak = equity
    max_drawdown = 0.0
    max_gross_exposure = 0.0

    for index, event in enumerate(events):
        event_id = str(event.get("event_id", "")).strip()
        if not event_id:
            raise ShadowError(f"event {index}: missing event_id")
        if event_id in seen:
            raise ShadowError(f"duplicate event_id: {event_id}")
        seen.add(event_id)

        pair = str(event.get("pair", "")).strip().upper()
        if pair not in ALLOWED_PAIRS:
            raise ShadowError(f"{event_id}: unsupported pair")

        action = str(event.get("action", "")).strip().lower()
        if action not in ALLOWED_ACTIONS:
            raise ShadowError(f"{event_id}: action must be entry or exit")

        bid, ask = _validate_market(event)
        before = equity
        realized_aud = 0.0

        if action == "entry":
            if pair in positions:
                raise ShadowError(f"{event_id}: pair already open")

            side = str(event.get("side", "")).strip().lower()
            if side not in ALLOWED_SIDES:
                raise ShadowError(f"{event_id}: entry side must be long or short")

            units = event.get("units")
            if not isinstance(units, int) or units <= 0:
                raise ShadowError(f"{event_id}: units must be a positive integer")

            base_to_aud = _positive_float(event.get("base_to_aud"), "base_to_aud")

            if side == "long":
                fill = _slip(ask, slippage_bps, +1)
            else:
                fill = _slip(bid, slippage_bps, -1)

            positions[pair] = Position(
                side=side,
                units=units,
                entry_fill=fill,
                base_to_aud=base_to_aud,
            )

        else:
            if pair not in positions:
                raise ShadowError(f"{event_id}: exit from flat pair")

            pos = positions[pair]
            quote_to_aud = _positive_float(event.get("quote_to_aud"), "quote_to_aud")

            if pos.side == "long":
                fill = _slip(bid, slippage_bps, -1)
                pnl_quote = (fill - pos.entry_fill) * pos.units
            else:
                fill = _slip(ask, slippage_bps, +1)
                pnl_quote = (pos.entry_fill - fill) * pos.units

            realized_aud = pnl_quote * quote_to_aud
            equity += realized_aud
            del positions[pair]

        gross_exposure = sum(
            p.units * p.base_to_aud
            for p in positions.values()
        )
        max_gross_exposure = max(max_gross_exposure, gross_exposure)

        peak = max(peak, equity)
        drawdown = (equity / peak - 1.0) if peak else 0.0
        max_drawdown = min(max_drawdown, drawdown)

        ledger.append({
            "event_id": event_id,
            "timestamp_utc": str(event.get("timestamp_utc", "")),
            "pair": pair,
            "action": action,
            "fill": fill,
            "realized_pnl_aud": realized_aud,
            "equity_before_aud": before,
            "equity_after_aud": equity,
            "drawdown": drawdown,
            "gross_nominal_exposure_aud": gross_exposure,
        })

    return {
        "version": VERSION,
        "mode": "OFFLINE_SHADOW_ONLY",
        "broker_transport": False,
        "network_capability": False,
        "submission_capability": False,
        "initial_equity_aud": initial_equity_aud,
        "slippage_bps": slippage_bps,
        "event_count": len(events),
        "input_sha256": _event_hash(events, initial_equity_aud, slippage_bps),
        "realized_pnl_aud": equity - initial_equity_aud,
        "final_equity_aud": equity,
        "max_drawdown": max_drawdown,
        "max_gross_nominal_exposure_aud": max_gross_exposure,
        "open_positions": {k: asdict(v) for k, v in sorted(positions.items())},
        "ledger": ledger,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--initial-equity-aud", type=float, default=100000.0)
    ap.add_argument("--slippage-bps", type=float, default=0.0)
    args = ap.parse_args()

    events = [
        json.loads(line)
        for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]

    result = simulate(
        events,
        initial_equity_aud=args.initial_equity_aud,
        slippage_bps=args.slippage_bps,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("M006F_SHADOW_SIMULATOR: PASS")
    print(f"events={result['event_count']}")
    print(f"final_equity_aud={result['final_equity_aud']:.6f}")
    print(f"max_drawdown={result['max_drawdown']:.8f}")
    print("network_capability=FALSE")
    print("submission_capability=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
