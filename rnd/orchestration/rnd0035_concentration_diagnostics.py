#!/usr/bin/env python3
"""Frozen RND-0035 B concentration diagnostics for the R000 trade ledger.

These diagnostics are outcome-informed descriptive attacks only. They never
remove, reweight, select, promote or modify observations or strategies.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime


class RND0035ConcentrationError(ValueError):
    pass


YEARS = (2015, 2016, 2017, 2018, 2019)
SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")


def _parse_year(trade):
    year = trade.get("exit_year")
    if year is None:
        value = trade.get("exit_timestamp")
        if not isinstance(value, str) or not value.endswith("Z"):
            raise RND0035ConcentrationError("trade requires exit_year or UTC exit_timestamp")
        year = datetime.fromisoformat(value[:-1] + "+00:00").year
    if year not in YEARS:
        raise RND0035ConcentrationError("trade outside authorized development years")
    return year


def _validate_trade(trade):
    symbol = trade.get("symbol")
    if symbol not in SYMBOLS:
        raise RND0035ConcentrationError("trade outside authorized symbol universe")
    value = trade.get("net_return")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RND0035ConcentrationError("finite net_return required")
    return symbol, _parse_year(trade), float(value)


def _summary(values):
    return {
        "trades": len(values),
        "net_return_sum": sum(values),
        "mean_net_return": (sum(values) / len(values)) if values else None,
        "positive_trade_fraction": (
            sum(1 for value in values if value > 0) / len(values) if values else None
        ),
    }


def _top_abs_contribution(values, fraction):
    if not values:
        return {
            "fraction": fraction,
            "selected_trade_count": 0,
            "selected_abs_net_return": 0.0,
            "total_abs_net_return": 0.0,
            "share_of_total_abs_net_return": None,
            "selected_signed_net_return": 0.0,
        }
    count = max(1, math.ceil(len(values) * fraction))
    ordered = sorted(values, key=lambda x: abs(x), reverse=True)
    selected = ordered[:count]
    total_abs = sum(abs(x) for x in values)
    selected_abs = sum(abs(x) for x in selected)
    return {
        "fraction": fraction,
        "selected_trade_count": count,
        "selected_abs_net_return": selected_abs,
        "total_abs_net_return": total_abs,
        "share_of_total_abs_net_return": selected_abs / total_abs if total_abs else None,
        "selected_signed_net_return": sum(selected),
    }


def concentration_diagnostics(trades):
    if not isinstance(trades, list):
        raise RND0035ConcentrationError("trade ledger must be a list")

    normalized = []
    by_pair = defaultdict(list)
    by_year = defaultdict(list)
    by_pair_year = defaultdict(list)
    for trade in trades:
        symbol, year, value = _validate_trade(trade)
        normalized.append((symbol, year, value))
        by_pair[symbol].append(value)
        by_year[year].append(value)
        by_pair_year[(symbol, year)].append(value)

    all_values = [value for _, _, value in normalized]
    early = [value for _, year, value in normalized if year in (2015, 2016)]
    middle = [value for _, year, value in normalized if year == 2017]
    late = [value for _, year, value in normalized if year in (2018, 2019)]

    leave_one_year_out = {}
    for year in YEARS:
        values = [value for _, y, value in normalized if y != year]
        leave_one_year_out[str(year)] = _summary(values)

    leave_one_pair_out = {}
    for symbol in SYMBOLS:
        values = [value for s, _, value in normalized if s != symbol]
        leave_one_pair_out[symbol] = _summary(values)

    return {
        "contract_version": "RND0035-concentration-diagnostics-v1",
        "classification": "OUTCOME_INFORMED",
        "strategy_selection_authority": False,
        "deletion_authority": False,
        "reweighting_authority": False,
        "trade_count": len(normalized),
        "pair": {symbol: _summary(by_pair[symbol]) for symbol in SYMBOLS},
        "year": {str(year): _summary(by_year[year]) for year in YEARS},
        "pair_x_year": {
            symbol: {
                str(year): _summary(by_pair_year[(symbol, year)]) for year in YEARS
            }
            for symbol in SYMBOLS
        },
        "period_concentration": {
            "early_2015_2016": _summary(early),
            "middle_2017": _summary(middle),
            "late_2018_2019": _summary(late),
        },
        "trade_count_density_by_pair_year": {
            symbol: {
                str(year): len(by_pair_year[(symbol, year)]) for year in YEARS
            }
            for symbol in SYMBOLS
        },
        "top_1_percent_absolute_net_return_contribution": _top_abs_contribution(all_values, 0.01),
        "top_5_percent_absolute_net_return_contribution": _top_abs_contribution(all_values, 0.05),
        "leave_one_year_out_reference_aggregation": leave_one_year_out,
        "leave_one_pair_out_reference_aggregation": leave_one_pair_out,
        "status": "PASS",
    }
