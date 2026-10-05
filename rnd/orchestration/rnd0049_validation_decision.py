#!/usr/bin/env python3
"""Pure deterministic classifier for the frozen RND-0049 validation protocol.

No file IO, broker access, strategy execution, data acquisition, or outcome
opening occurs here. The caller supplies already-computed metrics only after a
separate human gate has authorized the one-time prospective readout.
"""

CANDIDATE_FINGERPRINT = "25c21eb8fe8a6e19a1085741585b87d96a2dbf74f009c0470da608bbf60e3dd4"
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


class RND0049DecisionError(ValueError):
    pass


def _req(condition, message):
    if not condition:
        raise RND0049DecisionError(message)


def classify_validation(evidence, metrics=None):
    """Return one of the three frozen RND-0049 classifications."""
    _req(isinstance(evidence, dict), "evidence mapping required")
    _req(evidence.get("candidate_fingerprint") == CANDIDATE_FINGERPRINT, "candidate fingerprint mismatch")
    _req(tuple(evidence.get("symbols", ())) == SYMBOLS, "symbol universe mismatch")
    _req(evidence.get("elapsed_calendar_days", 0) >= 180, "prospective horizon incomplete")
    _req(evidence.get("reserved_final_access") is False, "reserved-final access prohibited")
    _req(evidence.get("broker_writes") is False, "broker writes prohibited")
    _req(evidence.get("capital_authority") is False, "capital authority prohibited")

    structural_pass = all([
        evidence.get("all_post_freeze") is True,
        evidence.get("all_sha_bound") is True,
        evidence.get("chronology_valid") is True,
        evidence.get("all_four_symbols") is True,
        evidence.get("m5_bid_ask_mid_complete_only") is True,
        evidence.get("no_synthetic_fill") is True,
        evidence.get("integrity_verifiers_pass") is True,
        evidence.get("candidate_mechanics_unchanged") is True,
    ])
    if not structural_pass:
        _req(metrics is None, "economic metrics must remain unopened on structural failure")
        return "VALIDATION_INCONCLUSIVE_STRUCTURAL"

    _req(isinstance(metrics, dict), "metrics required after structural pass")
    pair_equity = metrics.get("pair_terminal_net_equity")
    _req(isinstance(pair_equity, dict) and set(pair_equity) == set(SYMBOLS), "exact four-pair equity required")

    positive_pair_contrib = metrics.get("positive_pair_contributions")
    positive_month_contrib = metrics.get("positive_month_contributions")
    _req(isinstance(positive_pair_contrib, dict), "positive pair contributions required")
    _req(isinstance(positive_month_contrib, dict), "positive month contributions required")

    pair_total = sum(float(v) for v in positive_pair_contrib.values() if float(v) > 0)
    month_total = sum(float(v) for v in positive_month_contrib.values() if float(v) > 0)
    max_pair_share = 1.0 if pair_total <= 0 else max([float(v) for v in positive_pair_contrib.values()] or [0.0]) / pair_total
    max_month_share = 1.0 if month_total <= 0 else max([float(v) for v in positive_month_contrib.values()] or [0.0]) / month_total
    positive_month_count = sum(1 for v in positive_month_contrib.values() if float(v) > 0)
    nonnegative_pairs = sum(1 for s in SYMBOLS if float(pair_equity[s]) >= 1.0)

    passed = all([
        float(metrics.get("portfolio_terminal_equity", 0.0)) > 1.0,
        float(metrics.get("portfolio_realized_net_sum", 0.0)) > 0.0,
        nonnegative_pairs >= 3,
        float(metrics.get("portfolio_max_drawdown", -1.0)) >= -0.10,
        max_pair_share <= 0.70,
        max_month_share <= 0.60,
        positive_month_count >= 2,
        metrics.get("reconciliation_integrity_pass") is True,
        metrics.get("observed_bid_ask_costs") is True,
    ])
    return "VALIDATION_SUPPORTED" if passed else "VALIDATION_REJECTED"
