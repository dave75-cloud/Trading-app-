"""Pure development-only RND-0060T cross-pair lead-lag measurement/classifier kernel.

No strategy simulation, P&L, validation/final access, Q003/activity-state input,
threshold search, broker access, or execution authority.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

SYMBOLS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
ORIENTATION = {"AUDUSD": -1.0, "EURUSD": -1.0, "GBPUSD": -1.0, "USDJPY": 1.0}
AUTHORIZED_YEARS = frozenset({2015, 2016, 2017, 2018, 2019, 2020})
OBS_HOUR = 11
OBS_MINUTE = 30
LOOKBACK_BARS = 6
FORWARD_BARS = 6
M5_SECONDS = 300

RELATIONSHIPS = (
    ("EU_TO_AUDUSD", ("EURUSD", "GBPUSD"), "AUDUSD"),
    ("EU_TO_USDJPY", ("EURUSD", "GBPUSD"), "USDJPY"),
    ("PACIFIC_TO_EURUSD", ("AUDUSD", "USDJPY"), "EURUSD"),
    ("PACIFIC_TO_GBPUSD", ("AUDUSD", "USDJPY"), "GBPUSD"),
)


class RND0060TError(ValueError):
    pass


def _req(ok, message):
    if not ok:
        raise RND0060TError(message)


def _num(value, role, positive=False):
    _req(not isinstance(value, bool), f"{role}: finite number required")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise RND0060TError(f"{role}: finite number required") from exc
    _req(math.isfinite(out), f"{role}: finite number required")
    if positive:
        _req(out > 0.0, f"{role}: positive number required")
    return out


def _utc(value):
    _req(isinstance(value, str) and value.endswith("Z"), "UTC Z timestamp required")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RND0060TError("invalid timestamp") from exc
    _req(int(dt.timestamp()) % M5_SECONDS == 0, "timestamp off M5 grid")
    _req(dt.year in AUTHORIZED_YEARS, "development years 2015-2020 only")
    return dt


def validate_rows(rows):
    _req(isinstance(rows, list) and rows, "rows: non-empty list required")
    required = {"timestamp_utc", "complete", "mid_close"}
    out = []
    previous = None
    for i, row in enumerate(rows):
        _req(isinstance(row, dict), f"rows[{i}]: mapping required")
        _req(required.issubset(row), f"rows[{i}]: required fields missing")
        _req(row["complete"] is True, f"rows[{i}]: incomplete candle prohibited")
        dt = _utc(row["timestamp_utc"])
        _req(previous is None or dt > previous, "rows: timestamps must be unique and ordered")
        mid = _num(row["mid_close"], "mid_close", positive=True)
        out.append({"dt": dt, "mid": mid})
        previous = dt
    return out


def _average_ranks(values):
    pairs = sorted((float(v), i) for i, v in enumerate(values))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        rank = ((i + 1) + j) / 2.0
        for k in range(i, j):
            ranks[pairs[k][1]] = rank
        i = j
    return ranks


def _pearson(x, y):
    _req(len(x) == len(y) and len(x) >= 2, "correlation requires matched observations")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    sx = sum(v * v for v in dx)
    sy = sum(v * v for v in dy)
    _req(sx > 0.0 and sy > 0.0, "correlation undefined for constant input")
    return sum(a * b for a, b in zip(dx, dy)) / math.sqrt(sx * sy)


def spearman(x, y):
    return _pearson(_average_ranks(x), _average_ranks(y))


def extract_observations(rows_by_symbol):
    _req(isinstance(rows_by_symbol, dict) and set(rows_by_symbol) == set(SYMBOLS), "exact four-symbol row set required")
    parsed = {s: validate_rows(rows_by_symbol[s]) for s in SYMBOLS}
    by_dt = {s: {r["dt"]: r for r in parsed[s]} for s in SYMBOLS}
    candidate_days = sorted(set.intersection(*[
        {r["dt"].date() for r in parsed[s] if r["dt"].weekday() < 5 and r["dt"].hour == OBS_HOUR and r["dt"].minute == OBS_MINUTE}
        for s in SYMBOLS
    ]))

    observations = []
    exclusions = []
    for day in candidate_days:
        obs_dt = datetime(day.year, day.month, day.day, OBS_HOUR, OBS_MINUTE, tzinfo=timezone.utc)
        start_dt = obs_dt - timedelta(minutes=5 * LOOKBACK_BARS)
        end_dt = obs_dt + timedelta(minutes=5 * FORWARD_BARS)
        required = (start_dt, obs_dt, end_dt)
        if any(any(dt not in by_dt[s] for dt in required) for s in SYMBOLS):
            exclusions.append({"timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": "REQUIRED_CROSS_SECTION_OBSERVATION_MISSING"})
            continue

        current = {}
        forward = {}
        for s in SYMBOLS:
            start_mid = by_dt[s][start_dt]["mid"]
            obs_mid = by_dt[s][obs_dt]["mid"]
            end_mid = by_dt[s][end_dt]["mid"]
            current[s] = ORIENTATION[s] * (obs_mid / start_mid - 1.0)
            forward[s] = ORIENTATION[s] * (end_mid / obs_mid - 1.0)

        eu_leader = (current["EURUSD"] + current["GBPUSD"]) / 2.0
        pacific_leader = (current["AUDUSD"] + current["USDJPY"]) / 2.0
        observations.append({
            "timestamp_utc": obs_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": obs_dt.year,
            "leaders": {
                "EUROPEAN": eu_leader,
                "PACIFIC": pacific_leader,
            },
            "targets": {
                "AUDUSD": forward["AUDUSD"],
                "USDJPY": forward["USDJPY"],
                "EURUSD": forward["EURUSD"],
                "GBPUSD": forward["GBPUSD"],
            },
            "current_usd_oriented_returns": current,
            "forward_usd_oriented_returns": forward,
        })
    return {"observations": observations, "exclusions": exclusions}


def _relationship_value(record, relationship_name):
    if relationship_name == "EU_TO_AUDUSD":
        return record["leaders"]["EUROPEAN"], record["targets"]["AUDUSD"]
    if relationship_name == "EU_TO_USDJPY":
        return record["leaders"]["EUROPEAN"], record["targets"]["USDJPY"]
    if relationship_name == "PACIFIC_TO_EURUSD":
        return record["leaders"]["PACIFIC"], record["targets"]["EURUSD"]
    if relationship_name == "PACIFIC_TO_GBPUSD":
        return record["leaders"]["PACIFIC"], record["targets"]["GBPUSD"]
    raise RND0060TError("unknown relationship")


def classify_observations(observations, exclusions=None):
    _req(isinstance(observations, list) and len(observations) >= 4, "at least four observations required")
    relationship_correlations = {}
    for name, _, _ in RELATIONSHIPS:
        pairs = [_relationship_value(r, name) for r in observations]
        relationship_correlations[name] = spearman([p[0] for p in pairs], [p[1] for p in pairs])

    aggregate = sum(relationship_correlations.values()) / len(relationship_correlations)
    annual = {}
    for year in sorted(AUTHORIZED_YEARS):
        rows = [r for r in observations if r["year"] == year]
        _req(len(rows) >= 2, f"{year}: insufficient annual observations")
        values = []
        for name, _, _ in RELATIONSHIPS:
            pairs = [_relationship_value(r, name) for r in rows]
            values.append(spearman([p[0] for p in pairs], [p[1] for p in pairs]))
        annual[year] = sum(values) / len(values)

    positive_years = sum(v > 0.0 for v in annual.values())
    positive_relationships = sum(v > 0.0 for v in relationship_correlations.values())
    criteria = {
        "aggregate_primary_gte_0_05": aggregate >= 0.05,
        "at_least_4_of_6_annual_aggregate_positive": positive_years >= 4,
        "at_least_3_of_4_relationship_correlations_positive": positive_relationships >= 3,
        "integrity_reconciliation_pass": True,
    }
    return {
        "classification": "CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE_DETECTED" if all(criteria.values()) else "NO_REPRODUCIBLE_CROSS_PAIR_LEAD_LAG_DIRECTIONAL_STRUCTURE",
        "criteria": criteria,
        "eligible_observation_count": len(observations),
        "excluded_observation_count": len(exclusions or []),
        "aggregate_primary_statistic": aggregate,
        "relationship_correlations": relationship_correlations,
        "annual_aggregate_statistics": annual,
        "positive_year_count": positive_years,
        "positive_relationship_count": positive_relationships,
        "trial_count": 1,
        "parameter_search": False,
        "threshold_search": False,
        "trade_simulation": False,
        "pnl": False,
        "strategy_candidate": False,
        "q003_reference": False,
        "activity_state_directional_input": False,
        "validation_open": False,
        "final_test_open": False,
        "reserved_final_access": False,
        "broker_writes": False,
        "capital_authority": False,
        "automatic_promotion": False,
    }


def summarize(rows_by_symbol):
    extracted = extract_observations(rows_by_symbol)
    result = classify_observations(extracted["observations"], extracted["exclusions"])
    result["observations"] = extracted["observations"]
    result["exclusions"] = extracted["exclusions"]
    result["development_only"] = True
    return result
