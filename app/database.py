"""SQLite database helpers: connection factory and schema initialisation."""

import sqlite3
from collections.abc import Generator

from app.config import settings


def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection for use as a FastAPI dependency.

    Opens a new connection per request, configures ``row_factory`` so that rows
    behave like dicts (accessible by column name), and guarantees the connection
    is closed after the request — even if an exception is raised.

    Yields:
        An open :class:`sqlite3.Connection` with ``row_factory`` set to
        :class:`sqlite3.Row`.
    """
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def setup() -> None:
    """Initialise the database schema on application startup.

    Creates the ``forms`` table if it does not already exist.

    The ``data`` column stores the full :class:`~app.models.FormPayload` as a
    JSON string, allowing the schema to remain simple while preserving the
    complete form structure.
    """
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
