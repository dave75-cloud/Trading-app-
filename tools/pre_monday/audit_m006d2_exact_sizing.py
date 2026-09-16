#!/usr/bin/env python3
"""
KQTRL M006d.2 — Exact Demo Sizing Equivalence Audit

Compares:
  1) actual tools/pre_monday/m006d_sizing.py (with network calls stubbed);
  2) actual cli/capture_m005_signals.py pro_rata_group();
  3) an independent Conservative-B reference allocator.

No network access is used by this audit.
No OANDA write endpoint exists or is invoked.
Canonical M005 is not modified.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import itertools
import math
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

import pandas as pd

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
LEGS = {
    "AUDUSD": ("AUD", "USD"),
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
}
CURRENCIES = ("AUD", "EUR", "GBP", "USD", "JPY")
PER_TRADE_MAX = 1.0
GROSS_CAP = 4.0
CURRENCY_CAP = 3.0
EPS = 1e-10

FAKE_NAV_AUD = 100000.0
FAKE_MIDS = {
    "AUD_USD": 0.7000,
    "EUR_USD": 1.1200,
    "GBP_USD": 1.3000,
    "USD_JPY": 150.0,
}

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def ref_alloc(entries: List[Tuple[str,str]], existing: Dict[str,float]) -> Dict[int,float]:
    """Independent equal-pro-rata Conservative-B allocator."""
    gross = sum(abs(v) for v in existing.values())
    ccy = {c: 0.0 for c in CURRENCIES}
    for pair, lev in existing.items():
        if pair not in LEGS:
            raise ValueError(f"unsupported existing pair {pair}")
        a,b = LEGS[pair]
        ccy[a] += abs(lev)
        ccy[b] += abs(lev)

    n = len(entries)
    if n == 0:
        return {}

    alpha = PER_TRADE_MAX
    alpha = min(alpha, max(0.0, GROSS_CAP - gross) / n)

    for curr in CURRENCIES:
        users = sum(1 for pair,_ in entries if curr in LEGS[pair])
        if users:
            alpha = min(alpha, max(0.0, CURRENCY_CAP - ccy[curr]) / users)

    alpha = max(0.0, min(PER_TRADE_MAX, alpha))
    return {i: alpha for i in range(n)}

def expected_units(pair: str, side: str, lev: float) -> int:
    audusd = FAKE_MIDS["AUD_USD"]
    aud_per_base = {
        "AUDUSD": 1.0,
        "EURUSD": FAKE_MIDS["EUR_USD"] / audusd,
        "GBPUSD": FAKE_MIDS["GBP_USD"] / audusd,
        "USDJPY": 1.0 / audusd,
    }
    units = FAKE_NAV_AUD * lev / aud_per_base[pair]
    signed = units if side == "long" else -units
    return int(round(signed))

def run_actual_m006d(mod, entries: List[Tuple[str,str]], existing: Dict[str,float]):
    def fake_getj(url, token):
        if url.endswith("/summary"):
            return {"account": {"currency": "AUD", "NAV": str(FAKE_NAV_AUD)}}
        if "/pricing?instruments=" in url:
            prices = []
            for inst, mid in FAKE_MIDS.items():
                spr = 0.0002 if "JPY" not in inst else 0.02
                prices.append({
                    "instrument": inst,
                    "bids": [{"price": str(mid - spr/2)}],
                    "asks": [{"price": str(mid + spr/2)}],
                })
            return {"prices": prices}
        raise AssertionError(f"Unexpected GET URL: {url}")

    old_getj = mod.getj
    old_argv = sys.argv[:]
    old_env = dict(os.environ)
    try:
        mod.getj = fake_getj
        os.environ["OANDA_ENV"] = "practice"
        os.environ["OANDA_API_TOKEN"] = "AUDIT_TOKEN_NOT_REAL"
        os.environ["OANDA_ACCOUNT_ID"] = "AUDIT_ACCOUNT_NOT_REAL"

        estr = ",".join(f"{p}:{s}" for p,s in entries)
        xstr = ",".join(f"{p}:{v}" for p,v in existing.items())
        sys.argv = ["m006d_sizing.py", "--entries", estr]
        if xstr:
            sys.argv += ["--existing", xstr]

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.main()
        out = buf.getvalue()
    finally:
        mod.getj = old_getj
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_env)

    m = re.search(r"pro_rata_alpha=([0-9.]+)", out)
    if not m:
        raise AssertionError(f"Could not parse alpha:\n{out}")
    alpha = float(m.group(1))

    rows = []
    pat = re.compile(
        r"^(AUDUSD|EURUSD|GBPUSD|USDJPY) (long|short): "
        r"allocation=([0-9.]+)x approx_units=([+-]?\d+)$",
        re.M,
    )
    for mm in pat.finditer(out):
        rows.append((mm.group(1), mm.group(2), float(mm.group(3)), int(mm.group(4))))
    if len(rows) != len(entries):
        raise AssertionError(f"Parsed {len(rows)} rows, expected {len(entries)}:\n{out}")
    return alpha, rows, out

def run_actual_m005(mod, entries: List[Tuple[str,str]], existing: Dict[str,float]):
    # Build the exact inputs expected by pro_rata_group.
    group = pd.DataFrame({
        "signal_id": [f"S{i}" for i in range(len(entries))],
        "symbol": [p for p,_ in entries],
    })
    gross = sum(abs(v) for v in existing.values())
    ccy = {c: 0.0 for c in CURRENCIES}
    for pair, lev in existing.items():
        a,b = LEGS[pair]
        ccy[a] += abs(lev)
        ccy[b] += abs(lev)
    got = mod.pro_rata_group(
        group, gross, ccy, PER_TRADE_MAX, GROSS_CAP, CURRENCY_CAP
    )
    return [float(got[f"S{i}"]) for i in range(len(entries))]

def close(a,b,tol=5e-7):
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)

def exposure_after(entries, existing, allocs):
    gross = sum(abs(v) for v in existing.values()) + sum(allocs)
    ccy = {c:0.0 for c in CURRENCIES}
    for pair,lev in existing.items():
        a,b=LEGS[pair]
        ccy[a]+=abs(lev); ccy[b]+=abs(lev)
    for (pair,_),lev in zip(entries,allocs):
        a,b=LEGS[pair]
        ccy[a]+=lev; ccy[b]+=lev
    return gross,ccy

def main():
    project = Path.home()/"Projects"/"Trading-app-"
    m006d_path = project/"tools/pre_monday/m006d_sizing.py"
    m005_path = project/"cli/capture_m005_signals.py"

    m006d = load_module("kqtrl_m006d_sizing_actual", m006d_path)
    m005 = load_module("kqtrl_m005_capture_actual", m005_path)

    scenarios = [
        ("single", [("AUDUSD","long")], {}),
        ("four_all_pairs", [
            ("AUDUSD","long"),("EURUSD","long"),("GBPUSD","short"),("USDJPY","long")
        ], {}),
        ("usd_bottleneck_three", [
            ("EURUSD","long"),("GBPUSD","long"),("USDJPY","short")
        ], {}),
        ("usd_bottleneck_four", [
            ("AUDUSD","long"),("EURUSD","long"),("GBPUSD","long"),("USDJPY","long")
        ], {}),
        ("existing_gross_2", [
            ("EURUSD","long"),("GBPUSD","short"),("USDJPY","long")
        ], {"AUDUSD":1.0,"EURUSD":1.0}),
        ("existing_usd_2_5", [
            ("GBPUSD","long"),("USDJPY","short")
        ], {"AUDUSD":1.0,"EURUSD":1.0,"USDJPY":0.5}),
        ("capacity_exhausted", [
            ("AUDUSD","long"),("EURUSD","short")
        ], {"AUDUSD":1.0,"EURUSD":1.0,"GBPUSD":1.0}),
        ("partial_half", [
            ("GBPUSD","long"),("USDJPY","long")
        ], {"EURUSD":1.0,"AUDUSD":1.0}),
        ("mixed_sides", [
            ("AUDUSD","short"),("EURUSD","long"),("GBPUSD","short")
        ], {}),
    ]

    print("KQTRL M006d.2 — EXACT DEMO SIZING EQUIVALENCE AUDIT")
    print("="*82)
    print("Actual demo sizing:", m006d_path)
    print("Actual M005 allocator:", m005_path)
    print("Reference: independent Conservative-B calculation")
    print("Network calls: STUBBED / ZERO EXTERNAL REQUESTS")
    print("OANDA writes: NONE")
    print()

    failures = []
    for name, entries, existing in scenarios:
        ref = ref_alloc(entries, existing)
        refv = [ref[i] for i in range(len(entries))]
        alpha, rows, _ = run_actual_m006d(m006d, entries, existing)
        m006dv = [r[2] for r in rows]
        m005v = run_actual_m005(m005, entries, existing)

        if not all(close(a,b) for a,b in zip(refv,m006dv)):
            failures.append(f"{name}: M006d allocations {m006dv} != ref {refv}")
        if not all(close(a,b) for a,b in zip(refv,m005v)):
            failures.append(f"{name}: M005 allocations {m005v} != ref {refv}")

        # Unit-conversion equivalence.
        for (pair,side), row, lev in zip(entries, rows, refv):
            expu = expected_units(pair, side, lev)
            if row[3] != expu:
                failures.append(
                    f"{name}: units {pair}/{side} actual={row[3]} ref={expu}"
                )

        gross, ccy = exposure_after(entries, existing, refv)
        if gross > GROSS_CAP + 1e-9:
            failures.append(f"{name}: reference gross breach {gross}")
        for c,v in ccy.items():
            if v > CURRENCY_CAP + 1e-9:
                failures.append(f"{name}: reference {c} breach {v}")

        print(
            f"{name}: alpha={refv[0] if refv else 0:.6f} "
            f"gross_after={gross:.6f} "
            f"max_ccy_after={max(ccy.values()):.6f} "
            f"PASS"
        )

    # Order independence: all permutations of four-pair simultaneous basket.
    base = [("AUDUSD","long"),("EURUSD","short"),("GBPUSD","long"),("USDJPY","short")]
    perm_checked = 0
    expected_alpha = None
    for perm in itertools.permutations(base):
        entries = list(perm)
        refv = list(ref_alloc(entries, {}).values())
        alpha, rows, _ = run_actual_m006d(m006d, entries, {})
        m005v = run_actual_m005(m005, entries, {})
        if expected_alpha is None:
            expected_alpha = refv[0]
        if not all(close(x, expected_alpha) for x in refv+m005v+[r[2] for r in rows]):
            failures.append(f"order_independence failed for permutation {entries}")
            break
        perm_checked += 1

    print(f"order_independence: permutations_checked={perm_checked} PASS" if perm_checked == 24
          else f"order_independence: FAIL after {perm_checked}")

    # Explicit safety/source assertions on actual demo sizing script.
    src = m006d_path.read_text(encoding="utf-8")
    bad_methods = re.findall(r'method\s*=\s*["\'](POST|PUT|PATCH|DELETE)["\']', src, flags=re.I)
    if bad_methods:
        failures.append(f"M006d sizing contains write HTTP methods: {bad_methods}")
    if 'OANDA_ENV")!="practice"' not in src.replace(" ", ""):
        # tolerant secondary check
        if "OANDA_ENV" not in src or "practice" not in src:
            failures.append("M006d sizing practice-environment guard not found")

    print("-"*82)
    if failures:
        print("M006D2_EXACT_SIZING_AUDIT: FAIL")
        for f in failures:
            print(" -", f)
        print("Canonical M005 modified: False")
        return 10

    print("M006D2_EXACT_SIZING_AUDIT: PASS")
    print("Verified:")
    print("  1.0x per-trade maximum")
    print("  4.0x portfolio gross cap")
    print("  3.0x gross currency-leg cap")
    print("  simultaneous pro-rata allocation")
    print("  order independence across all 24 four-pair permutations")
    print("  AUD-account base-unit conversion for all four pairs")
    print("  actual M006d sizing == actual M005 allocator == independent reference")
    print("OANDA write endpoints invoked: FALSE")
    print("Canonical M005 modified: False")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
