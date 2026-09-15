#!/usr/bin/env python3
"""
KQTRL M006e.2 — Event-driven Twelve validator.

READ ONLY / ZERO WRITE.

Architecture:
    OANDA M006e.1 authoritative event
        -> Twelve same-bar independent validation
        -> validation decision only

Rules:
- OANDA remains authoritative.
- Consume actual M006e.1 event rows; do not infer events from post-event state.
- Entry:
    * authoritative event age <= 20 min
    * matching Twelve completed M5 bar required
    * Twelve age <= 10 min
    * delayed direction must agree
    * OANDA and Twelve volatility eligibility must agree
    * authoritative OANDA volatility must be eligible
    * 5-10 bps close divergence = warning
    * >10 bps close divergence = block
- Exit:
    * risk-reducing exit is never vetoed by Twelve disagreement,
      missing Twelve data, or stale signal-event age.
- Reversal:
    * split into risk-reducing exit leg
    * separately gate the new entry leg
- No order construction.
- No OANDA network calls.
- No OANDA write methods.
- No modification of canonical M005 or M006c state.

OANDA spot-price freshness remains an M006e.3 integrated execution-policy
check because M006e.2 receives completed M5 event records, not a live
pricing snapshot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from m006e1_oanda_authoritative_observer import (
    PAIRS,
    add_indicators,
)


DEFAULT_EVENT_MAX_AGE_MIN = 20.0
DEFAULT_TWELVE_MAX_AGE_MIN = 10.0
DEFAULT_WARNING_BPS = 5.0
DEFAULT_BLOCK_BPS = 10.0


def boolish(v) -> bool:
    if isinstance(v, bool):
        return v

    if v is None:
        return False

    if isinstance(v, (int, float)):
        return bool(v)

    return str(v).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "t",
    }


def position_to_int(v) -> int:
    if isinstance(v, (int, float)):
        n = int(v)

        if n in (-1, 0, 1):
            return n

    s = str(v).strip().lower()

    mapping = {
        "short": -1,
        "-1": -1,
        "flat": 0,
        "0": 0,
        "long": 1,
        "1": 1,
    }

    if s not in mapping:
        raise ValueError(
            f"Unrecognized position value: {v!r}"
        )

    return mapping[s]


def age_minutes(
    ts: pd.Timestamp,
    now: pd.Timestamp,
) -> float:
    return (
        now - ts
    ).total_seconds() / 60.0


def bps_diff(
    authoritative: float,
    validator: float,
) -> float:
    if authoritative == 0:
        return float("inf")

    return (
        abs(authoritative - validator)
        / abs(authoritative)
        * 10000.0
    )


def load_twelve(
    path: Path,
    pair: str,
) -> pd.DataFrame:
    f = path / f"{pair}_5m.csv"

    if not f.exists():
        raise RuntimeError(
            f"Missing Twelve file: {f}"
        )

    df = pd.read_csv(f)

    if df.empty:
        raise RuntimeError(
            f"Empty Twelve file: {f}"
        )

    df["ts"] = pd.to_datetime(
        df["ts"],
        utc=True,
        errors="raise",
    )

    for c in ("o", "h", "l", "c"):
        df[c] = pd.to_numeric(
            df[c],
            errors="raise",
        )

    return (
        df[
            ["ts", "o", "h", "l", "c"]
        ]
        .sort_values("ts")
        .drop_duplicates(
            "ts",
            keep="last",
        )
        .reset_index(drop=True)
    )


def latest_event_file(
    root: Path,
) -> Path | None:
    files = sorted(
        (root / "events").glob(
            "cycle_*.csv"
        )
    )

    if not files:
        return None

    return files[-1]


def event_identity(event: dict) -> str:
    fields = [
        str(event.get("cycle_id", "")),
        str(event.get("provider", "")),
        str(event.get("pair", "")),
        str(event.get("bar_ts_utc", "")),
        str(event.get("event_type", "")),
        str(event.get("old_position", "")),
        str(event.get("new_position", "")),
    ]

    return "|".join(fields)


def matching_twelve_row(
    enriched: pd.DataFrame | None,
    event_ts: pd.Timestamp,
):
    if enriched is None:
        return None

    m = enriched[
        enriched["ts"] == event_ts
    ]

    if m.empty:
        return None

    return m.iloc[-1]


def common_output(
    event: dict,
    leg: str,
) -> dict:
    return {
        "event_id": event_identity(event),
        "cycle_id": str(
            event.get("cycle_id", "")
        ),
        "pair": str(
            event.get("pair", "")
        ),
        "bar_ts_utc": str(
            event.get("bar_ts_utc", "")
        ),
        "authoritative_event_type": str(
            event.get("event_type", "")
        ).strip().lower(),
        "validation_leg": leg,
        "old_position": str(
            event.get("old_position", "")
        ),
        "new_position": str(
            event.get("new_position", "")
        ),
    }


def validate_entry_leg(
    event: dict,
    twelve_row,
    now: pd.Timestamp,
    event_max_age_min: float,
    twelve_max_age_min: float,
    warning_bps: float,
    block_bps: float,
) -> dict:
    out = common_output(
        event,
        "entry",
    )

    reasons = []
    warnings = []

    event_ts = pd.to_datetime(
        event["bar_ts_utc"],
        utc=True,
    )

    event_age = age_minutes(
        event_ts,
        now,
    )

    authoritative_signal = int(
        event[
            "desired_delayed_signal"
        ]
    )

    authoritative_vol_ok = boolish(
        event["volatility_ok"]
    )

    authoritative_close = float(
        event["close"]
    )

    out.update(
        {
            "oanda_signal":
                authoritative_signal,
            "oanda_volatility":
                float(
                    event["volatility"]
                ),
            "oanda_vol_ok":
                authoritative_vol_ok,
            "oanda_close":
                authoritative_close,
            "event_age_min":
                event_age,
        }
    )

    if authoritative_signal == 0:
        reasons.append(
            "AUTHORITATIVE_ENTRY_SIGNAL_ZERO"
        )

    if not authoritative_vol_ok:
        reasons.append(
            "OANDA_VOL_NOT_ELIGIBLE"
        )

    if event_age > event_max_age_min:
        reasons.append(
            f"AUTHORITATIVE_EVENT_STALE_"
            f"{event_age:.2f}M"
        )

    if twelve_row is None:
        reasons.append(
            "TWELVE_MATCHING_BAR_MISSING"
        )

        out.update(
            {
                "twelve_bar_ts_utc":
                    None,
                "twelve_signal":
                    None,
                "twelve_vol_ok":
                    None,
                "twelve_close":
                    None,
                "twelve_age_min":
                    None,
                "price_divergence_bps":
                    None,
            }
        )

    else:
        twelve_ts = pd.Timestamp(
            twelve_row["ts"]
        )

        twelve_age = age_minutes(
            twelve_ts,
            now,
        )

        twelve_signal = int(
            twelve_row[
                "delayed_signal"
            ]
        )

        twelve_vol_ok = bool(
            twelve_row["vol_ok"]
        )

        twelve_close = float(
            twelve_row["c"]
        )

        divergence = bps_diff(
            authoritative_close,
            twelve_close,
        )

        out.update(
            {
                "twelve_bar_ts_utc":
                    twelve_ts.isoformat(),
                "twelve_signal":
                    twelve_signal,
                "twelve_vol_ok":
                    twelve_vol_ok,
                "twelve_close":
                    twelve_close,
                "twelve_age_min":
                    twelve_age,
                "price_divergence_bps":
                    divergence,
            }
        )

        if twelve_age > twelve_max_age_min:
            reasons.append(
                f"TWELVE_STALE_"
                f"{twelve_age:.2f}M"
            )

        if (
            twelve_signal
            != authoritative_signal
        ):
            reasons.append(
                "DIRECTION_DISAGREEMENT_"
                f"OANDA_"
                f"{authoritative_signal}_"
                f"TWELVE_"
                f"{twelve_signal}"
            )

        if (
            twelve_vol_ok
            != authoritative_vol_ok
        ):
            reasons.append(
                "VOL_ELIGIBILITY_DISAGREEMENT_"
                f"OANDA_"
                f"{authoritative_vol_ok}_"
                f"TWELVE_"
                f"{twelve_vol_ok}"
            )

        if divergence > block_bps:
            reasons.append(
                "PRICE_DIVERGENCE_BLOCK_"
                f"{divergence:.3f}BPS"
            )

        elif divergence >= warning_bps:
            warnings.append(
                "PRICE_DIVERGENCE_WARNING_"
                f"{divergence:.3f}BPS"
            )

    warnings.append(
        "OANDA_SPOT_PRICE_FRESHNESS_"
        "DEFERRED_TO_M006E3"
    )

    decision = (
        "BLOCK"
        if reasons
        else "ALLOW_DRY_RUN_VALIDATION"
    )

    out.update(
        {
            "decision": decision,
            "status": decision,
            "reasons": reasons,
            "warnings": warnings,
        }
    )

    return out


def validate_exit_leg(
    event: dict,
    twelve_row,
    now: pd.Timestamp,
) -> dict:
    out = common_output(
        event,
        "exit",
    )

    warnings = []

    event_ts = pd.to_datetime(
        event["bar_ts_utc"],
        utc=True,
    )

    out["event_age_min"] = (
        age_minutes(
            event_ts,
            now,
        )
    )

    out["oanda_signal"] = int(
        event[
            "desired_delayed_signal"
        ]
    )

    if twelve_row is None:
        out.update(
            {
                "twelve_bar_ts_utc":
                    None,
                "twelve_signal":
                    None,
                "twelve_vol_ok":
                    None,
                "twelve_close":
                    None,
                "twelve_age_min":
                    None,
                "price_divergence_bps":
                    None,
            }
        )

        warnings.append(
            "TWELVE_MATCHING_BAR_MISSING_"
            "EXIT_NOT_BLOCKED"
        )

    else:
        twelve_ts = pd.Timestamp(
            twelve_row["ts"]
        )

        twelve_signal = int(
            twelve_row[
                "delayed_signal"
            ]
        )

        out.update(
            {
                "twelve_bar_ts_utc":
                    twelve_ts.isoformat(),
                "twelve_signal":
                    twelve_signal,
                "twelve_vol_ok":
                    bool(
                        twelve_row[
                            "vol_ok"
                        ]
                    ),
                "twelve_close":
                    float(
                        twelve_row["c"]
                    ),
                "twelve_age_min":
                    age_minutes(
                        twelve_ts,
                        now,
                    ),
                "price_divergence_bps":
                    bps_diff(
                        float(
                            event[
                                "close"
                            ]
                        ),
                        float(
                            twelve_row[
                                "c"
                            ]
                        ),
                    ),
            }
        )

        if twelve_signal != int(
            event[
                "desired_delayed_signal"
            ]
        ):
            warnings.append(
                "TWELVE_DISAGREES_BUT_"
                "EXIT_NOT_BLOCKED"
            )

    out.update(
        {
            "decision":
                "ALLOW_RISK_REDUCING_EXIT",
            "status":
                "ALLOW_RISK_REDUCING_EXIT",
            "reasons": [],
            "warnings": warnings,
        }
    )

    return out


def valid_transition(
    event_type: str,
    old_position: int,
    new_position: int,
) -> bool:
    if event_type == "entry":
        return (
            old_position == 0
            and new_position in (-1, 1)
        )

    if event_type == "exit":
        return (
            old_position in (-1, 1)
            and new_position == 0
        )

    if event_type == "reversal":
        return (
            old_position in (-1, 1)
            and new_position in (-1, 1)
            and old_position
            == -new_position
        )

    return False


def malformed_event_result(
    event: dict,
) -> list[dict]:
    out = common_output(
        event,
        "invalid",
    )

    out.update(
        {
            "decision": "BLOCK",
            "status": "BLOCK",
            "reasons": [
                "INVALID_AUTHORITATIVE_"
                "EVENT_TRANSITION"
            ],
            "warnings": [],
        }
    )

    return [out]


def validate_event(
    event: dict,
    twelve_enriched: pd.DataFrame | None,
    now: pd.Timestamp,
    event_max_age_min:
        float = DEFAULT_EVENT_MAX_AGE_MIN,
    twelve_max_age_min:
        float = DEFAULT_TWELVE_MAX_AGE_MIN,
    warning_bps:
        float = DEFAULT_WARNING_BPS,
    block_bps:
        float = DEFAULT_BLOCK_BPS,
) -> list[dict]:
    event_type = str(
        event.get(
            "event_type",
            "",
        )
    ).strip().lower()

    old_position = position_to_int(
        event.get(
            "old_position",
            "",
        )
    )

    new_position = position_to_int(
        event.get(
            "new_position",
            "",
        )
    )

    if not valid_transition(
        event_type,
        old_position,
        new_position,
    ):
        return malformed_event_result(
            event
        )

    event_ts = pd.to_datetime(
        event["bar_ts_utc"],
        utc=True,
    )

    twelve_row = matching_twelve_row(
        twelve_enriched,
        event_ts,
    )

    if event_type == "entry":
        return [
            validate_entry_leg(
                event,
                twelve_row,
                now,
                event_max_age_min,
                twelve_max_age_min,
                warning_bps,
                block_bps,
            )
        ]

    if event_type == "exit":
        return [
            validate_exit_leg(
                event,
                twelve_row,
                now,
            )
        ]

    # Reversal is deliberately decomposed:
    # risk-reducing exit first, then separately
    # validated new entry.
    exit_result = validate_exit_leg(
        event,
        twelve_row,
        now,
    )

    exit_result[
        "validation_leg"
    ] = "reversal_exit"

    entry_result = validate_entry_leg(
        event,
        twelve_row,
        now,
        event_max_age_min,
        twelve_max_age_min,
        warning_bps,
        block_bps,
    )

    entry_result[
        "validation_leg"
    ] = "reversal_entry"

    return [
        exit_result,
        entry_result,
    ]


def validate_events(
    events: list[dict],
    twelve_by_pair:
        dict[str, pd.DataFrame | None],
    now: pd.Timestamp,
    event_max_age_min:
        float = DEFAULT_EVENT_MAX_AGE_MIN,
    twelve_max_age_min:
        float = DEFAULT_TWELVE_MAX_AGE_MIN,
    warning_bps:
        float = DEFAULT_WARNING_BPS,
    block_bps:
        float = DEFAULT_BLOCK_BPS,
) -> list[dict]:
    rows = []

    for event in events:
        pair = str(
            event["pair"]
        )

        rows.extend(
            validate_event(
                event,
                twelve_by_pair.get(
                    pair
                ),
                now,
                event_max_age_min,
                twelve_max_age_min,
                warning_bps,
                block_bps,
            )
        )

    return rows


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--m006e-root",
        default=(
            "./data/research_runs/"
            "M006E_OANDA_AUTHORITATIVE"
        ),
    )

    ap.add_argument(
        "--twelve-dir",
        default="./data/live_5m_twelve",
    )

    ap.add_argument(
        "--event-file",
        default=None,
    )

    ap.add_argument(
        "--event-max-age-min",
        type=float,
        default=DEFAULT_EVENT_MAX_AGE_MIN,
    )

    ap.add_argument(
        "--twelve-max-age-min",
        type=float,
        default=DEFAULT_TWELVE_MAX_AGE_MIN,
    )

    ap.add_argument(
        "--warning-bps",
        type=float,
        default=DEFAULT_WARNING_BPS,
    )

    ap.add_argument(
        "--block-bps",
        type=float,
        default=DEFAULT_BLOCK_BPS,
    )

    args = ap.parse_args()

    root = Path(
        args.m006e_root
    )

    state_path = (
        root
        / "state"
        / "observer_state.json"
    )

    if not state_path.exists():
        raise SystemExit(
            "FAIL_CLOSED: "
            "M006e.1 observer state "
            "does not exist"
        )

    state = json.loads(
        state_path.read_text()
    )

    if state.get(
        "authority"
    ) != "OANDA":
        raise SystemExit(
            "FAIL_CLOSED: "
            "M006e.1 state is not "
            "OANDA-authoritative"
        )

    if args.event_file:
        event_path = Path(
            args.event_file
        )
    else:
        event_path = (
            latest_event_file(
                root
            )
        )

    if (
        event_path is None
        or not event_path.exists()
    ):
        raise SystemExit(
            "FAIL_CLOSED: "
            "No M006e.1 event file found"
        )

    try:
        event_df = pd.read_csv(
            event_path
        )
    except pd.errors.EmptyDataError:
        event_df = pd.DataFrame()

    events = (
        event_df.to_dict(
            orient="records"
        )
        if not event_df.empty
        else []
    )

    twelve_by_pair = {}

    for pair in PAIRS:
        try:
            twelve = load_twelve(
                Path(
                    args.twelve_dir
                ),
                pair,
            )

            twelve_by_pair[pair] = (
                add_indicators(
                    twelve,
                    pair,
                )
            )

        except Exception:
            # Missing validator evidence is
            # represented as None. Entry logic
            # will fail closed; exits remain
            # risk-reducing.
            twelve_by_pair[pair] = (
                None
            )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    rows = validate_events(
        events,
        twelve_by_pair,
        now,
        args.event_max_age_min,
        args.twelve_max_age_min,
        args.warning_bps,
        args.block_bps,
    )

    rid = now.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    outdir = (
        root
        / "validation"
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        outdir
        / (
            "m006e2_event_validation_"
            f"{rid}.json"
        )
    )

    payload = {
        "run_id": rid,
        "mode":
            "READ_ONLY_ZERO_WRITE",
        "authority": "OANDA",
        "validator": "Twelve Data",
        "source_event_file":
            str(event_path),
        "authoritative_events":
            len(events),
        "validation_rows":
            len(rows),
        "rows": rows,
        "oanda_spot_price_freshness":
            "DEFERRED_TO_M006E3",
        "order_payloads_constructed":
            0,
        "oanda_network_calls":
            0,
        "oanda_write_requests_performed":
            0,
        "order_endpoints_invoked":
            False,
        "canonical_m005_modified":
            False,
        "m006c_state_modified":
            False,
    }

    report_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print(
        "KQTRL M006e.2 — "
        "EVENT-DRIVEN TWELVE VALIDATOR"
    )

    print("=" * 78)
    print("Authority: OANDA")
    print(
        "Validator: Twelve Data"
    )
    print(
        "Mode: READ ONLY / ZERO WRITE"
    )
    print(
        "Source event file:",
        event_path,
    )
    print(
        "Authoritative events:",
        len(events),
    )
    print(
        "Validation rows:",
        len(rows),
    )
    print()

    if not rows:
        print(
            "No authoritative events "
            "requiring validation."
        )

    for row in rows:
        print(
            row["pair"],
            "leg=",
            row[
                "validation_leg"
            ],
            "decision=",
            row["decision"],
            "reasons=",
            row["reasons"],
            "warnings=",
            row["warnings"],
        )

    print()
    print(
        "Report:",
        report_path,
    )
    print(
        "OANDA network calls: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA write requests performed: 0"
    )
    print(
        "Order endpoints invoked: FALSE"
    )
    print(
        "Canonical M005 modified: FALSE"
    )
    print(
        "M006c state modified: FALSE"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
