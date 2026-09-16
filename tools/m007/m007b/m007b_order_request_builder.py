#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VERSION = "M007b"

MODE = "ORDER_CONSTRUCTION_ZERO_WRITE"

PROVIDER = "OANDA"

PAIR_TO_INSTRUMENT = {
    "AUDUSD": "AUD_USD",
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
}

ALLOWED_EVENT_TYPES = {
    "entry",
    "reversal_entry",
}

ALLOWED_SIDES = {
    "long",
    "short",
}

MAX_ABS_UNITS = 100_000_000


@dataclass(frozen=True)
class ApprovedExecutionInput:
    strategy_version: str
    pair: str
    bar_ts_utc: str
    event_type: str
    old_position: str
    new_position: str
    signed_units: int
    validation_decision: str
    sizing_decision: str


def normalize_pair(pair: str) -> str:
    p = str(pair).strip().upper()

    if p not in PAIR_TO_INSTRUMENT:
        raise ValueError(
            f"Unsupported pair: {pair!r}"
        )

    return p


def normalize_position(value: str) -> str:
    x = str(value).strip().lower()

    aliases = {
        "1": "long",
        "+1": "long",
        "long": "long",
        "-1": "short",
        "short": "short",
        "0": "flat",
        "flat": "flat",
    }

    if x not in aliases:
        raise ValueError(
            f"Unsupported position: {value!r}"
        )

    return aliases[x]


def normalize_event_type(value: str) -> str:
    x = str(value).strip().lower()

    if x not in ALLOWED_EVENT_TYPES:
        raise ValueError(
            "M007b constructs entry-side requests only; "
            f"unsupported event_type={value!r}"
        )

    return x


def canonical_timestamp(value: str) -> str:
    s = str(value).strip()

    # M007b intentionally performs only conservative syntactic
    # canonicalization. It does not invent missing timezone data.
    m = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2})"
        r"(?:\.\d+)?"
        r"(Z|\+00:00)",
        s,
    )

    if not m:
        raise ValueError(
            "bar_ts_utc must be an explicit UTC ISO-8601 timestamp"
        )

    return (
        m.group(1)
        + "Z"
    )


def side_from_units(
    signed_units: int,
) -> str:
    if signed_units == 0:
        raise ValueError(
            "signed_units must be non-zero"
        )

    return (
        "long"
        if signed_units > 0
        else "short"
    )


def validate_transition(
    event_type: str,
    old_position: str,
    new_position: str,
    signed_units: int,
) -> None:
    side = side_from_units(
        signed_units
    )

    if new_position not in ALLOWED_SIDES:
        raise ValueError(
            "entry-side request must end long or short"
        )

    if side != new_position:
        raise ValueError(
            "signed unit direction disagrees with new_position"
        )

    if event_type == "entry":
        if old_position != "flat":
            raise ValueError(
                "entry event must start from flat"
            )

    elif event_type == "reversal_entry":
        # This represents ONLY the second leg of an already-confirmed
        # reversal. The old strategy position names the pre-reversal
        # strategy state, but execution of this entry requires upstream
        # confirmation that the exit leg has completed.
        if old_position == "flat":
            raise ValueError(
                "reversal_entry requires a non-flat prior strategy position"
            )

        if old_position == new_position:
            raise ValueError(
                "reversal_entry must change direction"
            )


def event_identity(
    x: ApprovedExecutionInput,
) -> str:
    pair = normalize_pair(
        x.pair
    )

    ts = canonical_timestamp(
        x.bar_ts_utc
    )

    event_type = normalize_event_type(
        x.event_type
    )

    old_position = normalize_position(
        x.old_position
    )

    new_position = normalize_position(
        x.new_position
    )

    raw = "|".join(
        [
            str(
                x.strategy_version
            ).strip(),
            PROVIDER,
            pair,
            ts,
            event_type,
            old_position,
            new_position,
        ]
    )

    return raw


def event_digest(
    event_id: str,
) -> str:
    return hashlib.sha256(
        event_id.encode(
            "utf-8"
        )
    ).hexdigest()


def client_metadata(
    event_id: str,
) -> dict[str, str]:
    digest = event_digest(
        event_id
    )

    # Deliberately conservative character set.
    # Exact broker-side metadata length acceptance must still be
    # verified before any future network-capable M007 stage.
    return {
        "id":
            "KQ7B-"
            + digest[:24],
        "tag":
            "KQTRL-M007B",
        "comment":
            "ZERO_WRITE-"
            + digest[:16],
    }


def validate_input(
    x: ApprovedExecutionInput,
) -> dict[str, Any]:
    pair = normalize_pair(
        x.pair
    )

    ts = canonical_timestamp(
        x.bar_ts_utc
    )

    event_type = normalize_event_type(
        x.event_type
    )

    old_position = normalize_position(
        x.old_position
    )

    new_position = normalize_position(
        x.new_position
    )

    if not isinstance(
        x.signed_units,
        int,
    ):
        raise TypeError(
            "signed_units must be an integer"
        )

    if x.signed_units == 0:
        raise ValueError(
            "signed_units must be non-zero"
        )

    if abs(
        x.signed_units
    ) > MAX_ABS_UNITS:
        raise ValueError(
            "signed_units exceeds M007b defensive construction limit"
        )

    if (
        str(
            x.validation_decision
        ).strip()
        != "APPROVED"
    ):
        raise ValueError(
            "validation_decision must be APPROVED"
        )

    if (
        str(
            x.sizing_decision
        ).strip()
        != "APPROVED"
    ):
        raise ValueError(
            "sizing_decision must be APPROVED"
        )

    validate_transition(
        event_type,
        old_position,
        new_position,
        x.signed_units,
    )

    return {
        "strategy_version":
            str(
                x.strategy_version
            ).strip(),
        "pair":
            pair,
        "instrument":
            PAIR_TO_INSTRUMENT[
                pair
            ],
        "bar_ts_utc":
            ts,
        "event_type":
            event_type,
        "old_position":
            old_position,
        "new_position":
            new_position,
        "signed_units":
            x.signed_units,
    }


def build_market_order_request(
    x: ApprovedExecutionInput,
) -> dict[str, Any]:
    v = validate_input(
        x
    )

    eid = event_identity(
        x
    )

    metadata = client_metadata(
        eid
    )

    # Pure data construction only.
    #
    # No account ID.
    # No URL.
    # No endpoint.
    # No HTTP method.
    # No transport.
    #
    # Future M007 stages must independently validate this structure
    # against the then-current OANDA practice API before any write.
    order = {
        "order": {
            "type":
                "MARKET",
            "instrument":
                v[
                    "instrument"
                ],
            "units":
                str(
                    v[
                        "signed_units"
                    ]
                ),
            "timeInForce":
                "FOK",
            "positionFill":
                "DEFAULT",
            "clientExtensions":
                metadata,
        }
    }

    return {
        "version":
            VERSION,
        "mode":
            MODE,
        "provider":
            PROVIDER,
        "event_id":
            eid,
        "event_sha256":
            event_digest(
                eid
            ),
        "validated_input":
            v,
        "request_body":
            order,
        "network_capability":
            False,
        "order_submission_capability":
            False,
        "sizing_recalculated":
            False,
    }


def load_input(
    path: Path,
) -> ApprovedExecutionInput:
    d = json.loads(
        path.read_text()
    )

    return ApprovedExecutionInput(
        strategy_version=
            d[
                "strategy_version"
            ],
        pair=
            d[
                "pair"
            ],
        bar_ts_utc=
            d[
                "bar_ts_utc"
            ],
        event_type=
            d[
                "event_type"
            ],
        old_position=
            d[
                "old_position"
            ],
        new_position=
            d[
                "new_position"
            ],
        signed_units=
            d[
                "signed_units"
            ],
        validation_decision=
            d[
                "validation_decision"
            ],
        sizing_decision=
            d[
                "sizing_decision"
            ],
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--input",
        required=True,
        help=(
            "Synthetic/already-approved JSON execution input."
        ),
    )

    ap.add_argument(
        "--json-out",
    )

    args = ap.parse_args()

    x = load_input(
        Path(
            args.input
        )
    )

    result = (
        build_market_order_request(
            x
        )
    )

    print("=" * 78)
    print(
        "KQTRL M007b — "
        "ORDER REQUEST CONSTRUCTION / ZERO WRITE"
    )
    print("=" * 78)

    print(
        "Event ID:",
        result[
            "event_id"
        ],
    )

    print(
        "Instrument:",
        result[
            "validated_input"
        ][
            "instrument"
        ],
    )

    print(
        "Signed units:",
        result[
            "validated_input"
        ][
            "signed_units"
        ],
    )

    print()
    print(
        json.dumps(
            result[
                "request_body"
            ],
            indent=2,
            sort_keys=True,
        )
    )

    print()
    print(
        "Sizing recalculated:",
        result[
            "sizing_recalculated"
        ],
    )

    print(
        "Network capability:",
        result[
            "network_capability"
        ],
    )

    print(
        "Order submission capability:",
        result[
            "order_submission_capability"
        ],
    )

    if args.json_out:
        out = Path(
            args.json_out
        )

        out.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        out.write_text(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print(
            "Local JSON:",
            out,
        )


if __name__ == "__main__":
    main()
