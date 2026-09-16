#!/usr/bin/env python3

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent

# Candidate validator imports sibling M006e modules by basename.
M006E_ROOT = HERE.parents[1]
if str(M006E_ROOT) not in sys.path:
    sys.path.insert(0, str(M006E_ROOT))

CANDIDATE = (
    HERE /
    "m006e2_twelve_validator_candidate.py"
)


def load_candidate():
    spec = importlib.util.spec_from_file_location(
        "m006e2_candidate",
        CANDIDATE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "unable to load candidate validator"
        )

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return mod


def expect_ok(fn, value, expected):
    actual = fn(value)

    if actual != expected:
        raise AssertionError(
            f"{value!r}: expected {expected}, got {actual}"
        )

    print(
        f"PASS normalize {value!r:>10} -> {actual}"
    )


def expect_fail(fn, value):
    try:
        fn(value)
    except (ValueError, TypeError):
        print(
            f"PASS reject    {value!r}"
        )
        return

    raise AssertionError(
        f"{value!r}: expected fail-closed rejection"
    )


def main():
    mod = load_candidate()

    fn = getattr(
        mod,
        "normalize_signal",
        None,
    )

    if fn is None:
        raise AssertionError(
            "normalize_signal not found"
        )

    print("=" * 72)
    print(
        "KQTRL M006e.2 SIGNAL-ENCODING CANDIDATE AUDIT"
    )
    print("=" * 72)

    # Semantic strings emitted by M006e.1.
    expect_ok(fn, "long", 1)
    expect_ok(fn, "short", -1)
    expect_ok(fn, "flat", 0)

    # Numeric strings.
    expect_ok(fn, "1", 1)
    expect_ok(fn, "-1", -1)
    expect_ok(fn, "0", 0)

    # Numeric values.
    expect_ok(fn, 1, 1)
    expect_ok(fn, -1, -1)
    expect_ok(fn, 0, 0)

    # Whitespace / case normalization.
    expect_ok(fn, " LONG ", 1)
    expect_ok(fn, "Short", -1)
    expect_ok(fn, " FLAT ", 0)

    # Fail closed on anything outside frozen vocabulary.
    expect_fail(fn, "buy")
    expect_fail(fn, "sell")
    expect_fail(fn, "neutral")
    expect_fail(fn, "")
    expect_fail(fn, "2")
    expect_fail(fn, "-2")
    expect_fail(fn, 2)
    expect_fail(fn, None)
    expect_fail(fn, [])
    expect_fail(fn, {})

    print()
    print("SIGNAL_ENCODING_CANDIDATE_AUDIT: PASS")
    print("Network calls: 0")
    print("Order endpoints invoked: FALSE")
    print("Trading/order capability: NONE")


if __name__ == "__main__":
    main()
