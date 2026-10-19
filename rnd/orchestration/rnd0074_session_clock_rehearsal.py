"""RND-0074: offline session-clock convention rehearsal, NO market data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PILOT_YEAR = 2019
PARTITION = "DEVELOPMENT_2015_2020"
# Illustrative, predeclared wall-clock conventions, NOT actual venue hours.
CONVENTIONS = {
    "TOKYO": ("Asia/Tokyo", "09:00", "17:00"),
    "LONDON": ("Europe/London", "08:00", "16:00"),
    "NEW_YORK": ("America/New_York", "08:00", "16:00"),
}
PROHIBITED = frozenset({
    "actual_as_released", "consensus", "forecast", "fx_return",
    "returns", "price", "bid", "ask", "spread", "volume",
    "pnl", "equity", "drawdown", "hit_rate", "win_rate", "pair_rank",
    "directional_response", "strategy_signal", "strategy_outcome",
})
AUTHORITY_FALSE = {
    "provider_purchase_authority": False,
    "provider_access_authority": False,
    "strategy_outcome_open": False,
    "validation_open": False,
    "reserved_final_open": False,
    "prospective_outcomes_open": False,
    "promotion_authority": False,
    "broker_write_authority": False,
    "capital_authority": False,
    "live_execution_authority": False,
    "automatic_merge": False,
}

class RND0074Error(ValueError):
    pass

@dataclass(frozen=True)
class SessionInterval:
    session: str
    local_date: str
    timezone: str
    open_local: str
    close_local: str
    open_utc: str
    close_utc: str
    status: str = "SYNTHETIC_CLOCK_CONVENTION_ONLY"


def _time(s: str) -> time:
    if not isinstance(s, str) or len(s) != 5:
        raise RND0074Error("time must be HH:MM")
    try:
        value = time.fromisoformat(s)
    except ValueError as exc:
        raise RND0074Error("invalid wall clock") from exc
    if value.strftime("%H:%M") != s:
        raise RND0074Error("noncanonical wall clock")
    return value


def _date(s: str) -> date:
    try:
        parsed = date.fromisoformat(s)
    except (TypeError, ValueError) as exc:
        raise RND0074Error("invalid date") from exc
    if parsed.isoformat() != s:
        raise RND0074Error("date must be YYYY-MM-DD")
    if parsed.year != PILOT_YEAR:
        raise RND0074Error("outside frozen 2019 timing-fixture year")
    return parsed


def _zoned(local_date: date, wall: time, zone: ZoneInfo) -> datetime:
    naive = datetime.combine(local_date, wall)
    # Never silently choose one side of a DST fold or normalize a nonexistent time.
    a = naive.replace(tzinfo=zone, fold=0)
    b = naive.replace(tzinfo=zone, fold=1)
    if a.utcoffset() != b.utcoffset():
        raise RND0074Error("ambiguous or nonexistent DST wall time")
    utc = a.astimezone(timezone.utc)
    if utc.astimezone(zone).replace(tzinfo=None) != naive:
        raise RND0074Error("nonexistent wall time")
    return utc


def _stamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def reject_outcome_fields(payload: Any) -> None:
    if isinstance(payload, Mapping):
        if any(str(k).casefold() in PROHIBITED for k in payload):
            raise RND0074Error("market or announcement outcome fields prohibited")
        for v in payload.values():
            reject_outcome_fields(v)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            reject_outcome_fields(v)


def session_interval(session: str, local_date: str, *,
                     overrides: Mapping[str, Any] | None = None,
                     partition: str = PARTITION) -> SessionInterval:
    if partition != PARTITION:
        raise RND0074Error("nondevelopment partition prohibited")
    if session not in CONVENTIONS:
        raise RND0074Error("unknown session")
    d = _date(local_date)
    if d.weekday() >= 5:
        raise RND0074Error("weekend session excluded; holiday status not inferred")
    if overrides is not None:
        reject_outcome_fields(overrides)
        raise RND0074Error("session clock overrides not authorized")
    zone_name, opens, closes = CONVENTIONS[session]
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError as exc:
        raise RND0074Error("IANA timezone database unavailable") from exc
    start = _zoned(d, _time(opens), zone)
    end = _zoned(d, _time(closes), zone)
    if end <= start:
        raise RND0074Error("nonpositive convention interval")
    return SessionInterval(
        session=session, local_date=local_date, timezone=zone_name,
        open_local=opens, close_local=closes,
        open_utc=_stamp(start), close_utc=_stamp(end),
    )


def _utc(s: str) -> datetime:
    try:
        value = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise RND0074Error("invalid UTC interval field") from exc
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise RND0074Error("interval must be in UTC")
    return value.astimezone(timezone.utc)


def overlap_minutes(a: SessionInterval, b: SessionInterval) -> int:
    if a.session == b.session:
        raise RND0074Error("overlap needs distinct sessions")
    for item in (a, b):
        if item.status != "SYNTHETIC_CLOCK_CONVENTION_ONLY":
            raise RND0074Error("unapproved session status")
        if item.session not in CONVENTIONS or item.local_date[:4] != str(PILOT_YEAR):
            raise RND0074Error("unapproved session identity or year")
        if item != session_interval(item.session, item.local_date):
            raise RND0074Error("interval not equal to frozen convention")
    begin = max(_utc(a.open_utc), _utc(b.open_utc))
    finish = min(_utc(a.close_utc), _utc(b.close_utc))
    return max(0, int((finish-begin).total_seconds() // 60))


def clock_receipt(local_date: str) -> dict[str, Any]:
    records = [session_interval(name, local_date) for name in CONVENTIONS]
    pairs = [
        ("TOKYO", "LONDON"), ("TOKYO", "NEW_YORK"), ("LONDON", "NEW_YORK")
    ]
    by_name = {r.session: r for r in records}
    overlaps = {"/".join(pair): overlap_minutes(by_name[pair[0]], by_name[pair[1]])
                for pair in pairs}
    material = "|".join(
        f"{r.session}:{r.open_utc}:{r.close_utc}" for r in records
    )
    result = {
        "scope": "RND0074_2019_SYNTHETIC_CLOCK_ONLY",
        "local_date": local_date,
        "record_count": 3,
        "overlap_minutes": overlaps,
        "clock_sha256": sha256(material.encode("utf-8")).hexdigest(),
        "market_data_present": False,
        "holiday_calendar_verified": False,
        "dealer_handoff_verified": False,
        "predictive_edge_verified": False,
        "provider_cost_usd": 0,
    }
    result.update(AUTHORITY_FALSE)
    return result
