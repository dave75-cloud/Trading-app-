#!/usr/bin/env python3
"""Governed RND-0043 signal-to-friction development study."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "rnd" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from oanda_historical_quarantine import _json  # noqa: E402
from rnd0035_development_runner import PLAN_PATH, _verify_evidence  # noqa: E402
from rnd0035_trial_plan import load_plan  # noqa: E402
from rnd0038_full_development_r000 import _load_2020_rows, _validate_assembly_report  # noqa: E402
from rnd0038_reference_diagnostics_adapter import analyze_reference_results_2015_2020  # noqa: E402
from rnd0043_signal_friction_kernel import AUTHORIZED_ARMS, reconstruct_pair  # noqa: E402

AUTH_PATH = ROOT / "rnd" / "research" / "RND0043_DEVELOPMENT_OUTCOME_AUTHORIZATION.json"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
ARMS = ("F000", "F001", "F002", "F003")
YEARS = tuple(str(y) for y in range(2015, 2021))
START = "2015-01-01T00:00:00Z"
END = "2020-12-31T19:15:00Z"


class RND0043DevelopmentError(ValueError):
    pass


def req(condition, message):
    if not condition:
        raise RND0043DevelopmentError(message)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_authorization(path=AUTH_PATH):
    v = _json(path)
    req(v.get("task_id") == "RND-0043" and v.get("status") == "ACTIVE", "authorization inactive")
    req(v.get("scope") == "PREDECLARED_SIGNAL_FRICTION_DEVELOPMENT_ONLY", "authorization scope changed")
    req(v.get("authorized_interval") == {"start_inclusive_utc": START, "end_exclusive_utc": END}, "interval changed")
    req(v.get("symbols") == list(SYMBOLS), "symbol universe changed")
    req(v.get("authorized_arms") == AUTHORIZED_ARMS, "predeclared arm set changed")
    req(v.get("development_outcomes_authorized") is True, "development outcomes not authorized")
    for key in (
        "parameter_expansion", "pair_specific_ratios", "strategy_selection",
        "validation_access", "reserved_final_open", "portfolio_sizing",
        "broker_writes", "capital_authority", "automatic_promotion", "automatic_merge",
    ):
        req(v.get(key) is False, f"prohibited authority opened: {key}")
    req(v.get("human_review_required") is True, "human review requirement removed")
    return v


def ratio_summary(values):
    values = sorted(float(x) for x in values)
    if not values:
        return {"count": 0, "min": None, "median": None, "p25": None, "p75": None, "max": None}
    def q(p):
        if len(values) == 1:
            return values[0]
        pos = (len(values) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        frac = pos - lo
        return values[lo] * (1.0 - frac) + values[hi] * frac
    return {
        "count": len(values), "min": values[0], "median": statistics.median(values),
        "p25": q(0.25), "p75": q(0.75), "max": values[-1],
    }


def pair_summary(result):
    return {
        "rows": result["row_count"],
        "episodes": result["contiguous_episode_count"],
        "gaps": result["gap_count"],
        "trades": result["completed_trade_count"],
        "hit_rate": result["net_hit_rate"],
        "gross_equity_index": result["completed_trade_gross_equity_index"],
        "net_equity_index": result["completed_trade_net_equity_index"],
        "net_return_sum": result["completed_trade_net_return_sum"],
        "net_max_drawdown": result["completed_trade_net_max_drawdown"],
        "execution_cost_drag": result["total_execution_cost_drag"],
        "rejected_entry_signal_count": result["rejected_entry_signal_count"],
        "actual_entry_ratio_summary": ratio_summary(result["actual_entry_signal_to_friction_ratios"]),
    }


def yearly_pair_sums(per_symbol):
    out = {y: {s: 0.0 for s in SYMBOLS} for y in YEARS}
    for symbol, result in per_symbol.items():
        for trade in result["trades"]:
            year = str(trade["exit_year"])
            req(year in out, f"unexpected exit year: {year}")
            out[year][symbol] += float(trade["net_return"])
    return out


def aggregate_years(year_pair):
    return {year: sum(pairs.values()) for year, pairs in year_pair.items()}


def positive_concentration(values):
    positive = [float(v) for v in values if float(v) > 0]
    total = sum(positive)
    return max(positive) / total if total > 0 else 0.0


def contribution_tail_shares(per_symbol):
    vals = sorted((abs(float(t["net_return"])) for r in per_symbol.values() for t in r["trades"]), reverse=True)
    total = sum(vals)
    if not vals or total == 0:
        return {"top_1pct_absolute_share": 0.0, "top_5pct_absolute_share": 0.0}
    n = len(vals)
    n1 = max(1, int((n * 0.01) + 0.999999999))
    n5 = max(1, int((n * 0.05) + 0.999999999))
    return {
        "top_1pct_absolute_share": sum(vals[:n1]) / total,
        "top_5pct_absolute_share": sum(vals[:n5]) / total,
    }


def loo_improvement(reference, treatment):
    ref_year_pair = yearly_pair_sums(reference)
    trt_year_pair = yearly_pair_sums(treatment)
    by_year = {}
    for excluded in YEARS:
        ref = sum(sum(ref_year_pair[y].values()) for y in YEARS if y != excluded)
        trt = sum(sum(trt_year_pair[y].values()) for y in YEARS if y != excluded)
        by_year[excluded] = trt - ref
    by_pair = {}
    for excluded in SYMBOLS:
        ref = sum(v for y in YEARS for s, v in ref_year_pair[y].items() if s != excluded)
        trt = sum(v for y in YEARS for s, v in trt_year_pair[y].items() if s != excluded)
        by_pair[excluded] = trt - ref
    return {
        "leave_one_year_out_improvement": by_year,
        "leave_one_pair_out_improvement": by_pair,
        "year_majority_positive": sum(v > 0 for v in by_year.values()) > len(by_year) / 2,
        "pair_majority_positive": sum(v > 0 for v in by_pair.values()) > len(by_pair) / 2,
    }


def classify(arms):
    base = arms["F000"]
    base_net = base["portfolio_net_return_sum"]
    base_dd = base["diagnostics"]["G_four_pair_concurrent_reference"]["equal_unit_normalized_max_drawdown"]
    stricter = ["F001", "F002", "F003"]
    net_better = {a: arms[a]["portfolio_net_return_sum"] > base_net for a in stricter}
    dd_ok = {a: arms[a]["diagnostics"]["G_four_pair_concurrent_reference"]["equal_unit_normalized_max_drawdown"] >= base_dd for a in stricter}
    consecutive_net = (net_better["F001"] and net_better["F002"]) or (net_better["F002"] and net_better["F003"])
    consecutive_dd = (dd_ok["F001"] and dd_ok["F002"]) or (dd_ok["F002"] and dd_ok["F003"])
    coherent = [a for a in stricter if net_better[a] and dd_ok[a]]
    best = max(coherent, key=lambda a: arms[a]["portfolio_net_return_sum"], default=None)
    if best is None:
        return "MECHANISM_FALSIFIED", {"best_coherent_arm": None, "consecutive_net_improvement": consecutive_net, "consecutive_drawdown_nonworsening": consecutive_dd}
    base_pairs = base["per_symbol"]
    best_pairs = arms[best]["per_symbol"]
    pair_nonworsening = sum(best_pairs[s]["net_equity_index"] >= base_pairs[s]["net_equity_index"] for s in SYMBOLS) >= 3
    year_concentration_ok = arms[best]["max_positive_year_contribution_share"] <= 0.70
    loo = arms[best]["leave_one_out_vs_F000"]
    loo_ok = loo["year_majority_positive"] and loo["pair_majority_positive"]
    support = consecutive_net and consecutive_dd and pair_nonworsening and year_concentration_ok and loo_ok
    details = {
        "best_coherent_arm": best,
        "consecutive_net_improvement": consecutive_net,
        "consecutive_drawdown_nonworsening": consecutive_dd,
        "at_least_3_pairs_nonworsening": pair_nonworsening,
        "year_concentration_ok": year_concentration_ok,
        "leave_one_out_majorities_positive": loo_ok,
    }
    if support:
        return "MECHANISM_SUPPORTED_FOR_FURTHER_RESEARCH", details
    return "MECHANISM_MIXED_OR_NON_MONOTONIC", details


def run(audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root, development_2020_root, assembly_report):
    load_authorization()
    _validate_assembly_report(assembly_report)
    plan = load_plan(PLAN_PATH)
    req(plan.get("validation_open") is False and plan.get("final_test_open") is False, "validation/final unexpectedly open")
    ids_old, verified, historical_rows = _verify_evidence(plan, audusd_2015_shard, cross_pair_2015_root, development_2016_2019_root, load_rows=True)
    req(verified == 20, "2015-2019 evidence verification not 20/20")
    ids_2020, rows_2020 = _load_2020_rows(development_2020_root)
    full_rows = {}
    for symbol in SYMBOLS:
        rows = list(historical_rows[symbol]) + list(rows_2020[symbol])
        ts = [r["timestamp_utc"] for r in rows]
        req(ts == sorted(ts) and len(ts) == len(set(ts)), f"{symbol}: chronology/identity failure")
        req(ts[0] >= START and ts[-1] < END, f"{symbol}: development boundary breach")
        full_rows[symbol] = rows

    raw_results = {}
    arms = {}
    for arm in ARMS:
        per_symbol = {s: reconstruct_pair(s, full_rows[s], arm) for s in SYMBOLS}
        raw_results[arm] = per_symbol
        year_pair = yearly_pair_sums(per_symbol)
        year_total = aggregate_years(year_pair)
        diagnostics = analyze_reference_results_2015_2020(per_symbol)
        arms[arm] = {
            "ratio_threshold": AUTHORIZED_ARMS[arm],
            "per_symbol": {s: pair_summary(per_symbol[s]) for s in SYMBOLS},
            "portfolio_net_return_sum": sum(float(t["net_return"]) for s in SYMBOLS for t in per_symbol[s]["trades"]),
            "year_pair_net_return_sum": year_pair,
            "year_net_return_sum": year_total,
            "max_positive_year_contribution_share": positive_concentration(year_total.values()),
            "tail_contribution_shares": contribution_tail_shares(per_symbol),
            "diagnostics": diagnostics,
        }

    for arm in ARMS[1:]:
        arms[arm]["leave_one_out_vs_F000"] = loo_improvement(raw_results["F000"], raw_results[arm])
    arms["F000"]["leave_one_out_vs_F000"] = None
    classification, interpretation = classify(arms)

    return {
        "contract_version": "RND0043-signal-friction-development-v1",
        "task_id": "RND-0043",
        "development_interval": {"start_inclusive_utc": START, "end_exclusive_utc": END},
        "evidence_identity": {
            "verified_2015_2019": "20/20", "verified_2020": "4/4", "pair_years": "24/24",
            "identities_2015_2019": ids_old, "identities_2020": ids_2020,
        },
        "arms": arms,
        "classification": classification,
        "classification_details": interpretation,
        "authorized_arms_only": True,
        "parameter_expansion": False,
        "strategy_selection": False,
        "validation_access": False,
        "reserved_final_open": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
        "automatic_merge": False,
        "status": "COMPLETE_REQUIRES_HUMAN_REVIEW",
    }


def write_new(path, value):
    path = Path(path).expanduser().resolve()
    req(not path.exists(), "report exists; overwrite prohibited")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audusd-2015-shard", required=True)
    p.add_argument("--cross-pair-2015-root", required=True)
    p.add_argument("--development-2016-2019-root", required=True)
    p.add_argument("--development-2020-root", required=True)
    p.add_argument("--rnd0037-assembly-report", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args(argv)
    value = run(a.audusd_2015_shard, a.cross_pair_2015_root, a.development_2016_2019_root, a.development_2020_root, a.rnd0037_assembly_report)
    out = write_new(a.report, value)
    print("RND0043_SIGNAL_FRICTION_DEVELOPMENT: COMPLETE")
    print("verified_2015_2019=20/20")
    print("verified_2020=4/4")
    print("pair_years=24/24")
    print("arms=F000,F001,F002,F003")
    print(f"classification={value['classification']}")
    print("strategy_selection=FALSE")
    print("validation_access=FALSE")
    print("reserved_final_open=FALSE")
    print("broker_writes=FALSE")
    print("capital_authority=FALSE")
    print(f"report={out}")
    print(f"report_sha256={sha256_file(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
