from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_db_url() -> str:
    # Prefer Postgres/RDS via DB_URL, otherwise fall back to sqlite file.
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url
    db_path = os.getenv("DB_PATH", "./data/app.db")
    return f"sqlite:///{db_path}"


class Base(DeclarativeBase):
    pass


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asof_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    horizon: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timeframe: Mapped[str] = mapped_column(String, nullable=False)

    side: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prob_up: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_move: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    entry_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    entry_px: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sl_px: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tp_px: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tif: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # JSONB on Postgres, JSON elsewhere.
    raw: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("asof_ts", "horizon", "symbol", "timeframe", name="uq_signals_key"),
        Index("idx_signals_lookup", "symbol", "timeframe", "horizon", "asof_ts"),
    )


@dataclass
class Store:
    engine: Engine

    def init(self) -> None:
        Base.metadata.create_all(self.engine)

    def upsert_signal(self, payload: Dict[str, Any]) -> None:
        self.init()

        asof_raw = payload.get("asof_ts") or payload.get("asof") or payload.get("now")
        try:
            asof_ts = datetime.fromisoformat(str(asof_raw).replace("Z", "+00:00")) if asof_raw else utc_now()
            if asof_ts.tzinfo is None:
                asof_ts = asof_ts.replace(tzinfo=timezone.utc)
        except Exception:
            asof_ts = utc_now()
        horizon = str(payload.get("horizon", "30m"))
        symbol = str(payload.get("symbol", os.getenv("SYMBOL", "GBPUSD")))
        timeframe = str(payload.get("timeframe", f"{os.getenv('BAR_MINUTES','5')}m"))
        suggestion = payload.get("suggestion") or {}

        row = dict(
            asof_ts=asof_ts,
            horizon=horizon,
            symbol=symbol,
            timeframe=timeframe,
            side=payload.get("side"),
            prob_up=payload.get("prob_up"),
            expected_move=payload.get("expected_move"),
            entry_type=suggestion.get("entry_type"),
            entry_px=suggestion.get("entry_px"),
            sl_px=suggestion.get("sl_px"),
            tp_px=suggestion.get("tp_px"),
            size=suggestion.get("size"),
            tif=suggestion.get("tif"),
            source=payload.get("source"),
            raw=payload,
            created_at=utc_now(),
        )

        db_url = str(self.engine.url)
        is_sqlite = db_url.startswith("sqlite")

        with Session(self.engine) as s:
            # Cross-DB "upsert": lookup then update/insert. Fine for MVP volumes.
            existing = s.scalar(
                select(Signal).where(
                    Signal.asof_ts == asof_ts,
                    Signal.horizon == horizon,
                    Signal.symbol == symbol,
                    Signal.timeframe == timeframe,
                )
            )
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
            else:
                s.add(Signal(**row))
            s.commit()

    def fetch_signals(
        self,
        days: int = 30,
        horizon: str = "30m",
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        self.init()
        days = max(1, min(int(days), 3650))
        limit = max(1, min(int(limit), 20000))
        symbol = symbol or os.getenv("SYMBOL", "GBPUSD")
        timeframe = timeframe or f"{os.getenv('BAR_MINUTES','5')}m"

        with Session(self.engine) as s:
            cutoff = utc_now() - timedelta(days=days)
            rows = s.scalars(
                select(Signal)
                .where(
                    Signal.symbol == symbol,
                    Signal.timeframe == timeframe,
                    Signal.horizon == horizon,
                    Signal.asof_ts >= cutoff,
                )
                .order_by(Signal.asof_ts.asc())
                .limit(limit)
            ).all()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "asof_ts": r.asof_ts.isoformat().replace("+00:00", "Z"),
                    "horizon": r.horizon,
                    "symbol": r.symbol,
                    "timeframe": r.timeframe,
                    "side": r.side,
                    "prob_up": r.prob_up,
                    "expected_move": r.expected_move,
                    "entry_type": r.entry_type,
                    "entry_px": r.entry_px,
                    "sl_px": r.sl_px,
                    "tp_px": r.tp_px,
                    "size": r.size,
                    "tif": r.tif,
                    "source": r.source,
                    "raw": r.raw,
                    "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at),
                }
            )
        return out


def get_store(db_url: Optional[str] = None) -> Store:
    url = db_url or default_db_url()
    engine = create_engine(url, pool_pre_ping=True)
    return Store(engine=engine)
