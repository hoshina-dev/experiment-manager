import sqlite3
from collections.abc import Generator

from app.config import settings


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def setup() -> None:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forms (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT,
            data        TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
