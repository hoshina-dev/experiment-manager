"""SQLite connection factory and schema bootstrap for experiment storage."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

from app.config import settings

_DB_PATH = Path(settings.db_path)


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def setup() -> None:
    """Create the experiments table if it does not exist."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            exp_id              TEXT PRIMARY KEY,
            sample_id           TEXT NOT NULL,
            requested_analyses  TEXT NOT NULL,
            form                TEXT NOT NULL,
            created_at          TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
