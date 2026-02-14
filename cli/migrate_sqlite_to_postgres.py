"""One-time migration: SQLite signal history -> Postgres (RDS).

Usage:
  export DB_PATH=./data/app.db
  export DB_URL=postgresql://user:pass@host:5432/signals
  python cli/migrate_sqlite_to_postgres.py
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from storage.db_store import get_store


def _sqlite_rows(db_path: str):
    con = sqlite3.connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT raw_json
            FROM signals
            ORDER BY asof_ts ASC;
            """
        )
        for r in cur.fetchall():
            yield r["raw_json"]
    finally:
        con.close()


def main() -> int:
    db_path = os.getenv("DB_PATH", "./data/app.db")
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise SystemExit("DB_URL is required (postgresql://...)")

    store = get_store(db_url)
    store.init()

    import json

    n = 0
    for raw_json in _sqlite_rows(db_path):
        try:
            payload = json.loads(raw_json)
        except Exception:
            continue
        store.upsert_signal(payload)
        n += 1
        if n % 500 == 0:
            print(f"migrated {n}...")

    print(f"done. migrated {n} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
