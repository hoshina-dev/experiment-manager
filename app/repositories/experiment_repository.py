"""CRUD operations for experiments against the SQLite database."""

import json
import sqlite3
from datetime import datetime, timezone

from app.models import AnalysisTemplate, ExperimentDetail, ExperimentSummary


def create(
    conn: sqlite3.Connection,
    exp_id: str,
    sample_id: str,
    requested_analyses: list[str],
    form_snapshot: list[AnalysisTemplate],
) -> ExperimentSummary:
    created_at = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO experiments (exp_id, sample_id, requested_analyses, form, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            exp_id,
            sample_id,
            json.dumps(requested_analyses),
            json.dumps([t.model_dump() for t in form_snapshot]),
            created_at.isoformat(),
        ),
    )
    conn.commit()
    return ExperimentSummary(
        exp_id=exp_id,
        sample_id=sample_id,
        requested_analyses=requested_analyses,
        created_at=created_at,
    )


def list_all(conn: sqlite3.Connection) -> list[ExperimentSummary]:
    rows = conn.execute(
        "SELECT exp_id, sample_id, requested_analyses, created_at FROM experiments ORDER BY created_at DESC"
    ).fetchall()
    return [
        ExperimentSummary(
            exp_id=row["exp_id"],
            sample_id=row["sample_id"],
            requested_analyses=json.loads(row["requested_analyses"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def get(conn: sqlite3.Connection, exp_id: str) -> ExperimentDetail | None:
    row = conn.execute(
        "SELECT * FROM experiments WHERE exp_id = ?", (exp_id,)
    ).fetchone()
    if row is None:
        return None
    return ExperimentDetail(
        exp_id=row["exp_id"],
        sample_id=row["sample_id"],
        requested_analyses=json.loads(row["requested_analyses"]),
        form=[AnalysisTemplate(**t) for t in json.loads(row["form"])],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def update(
    conn: sqlite3.Connection,
    exp_id: str,
    requested_analyses: list[str],
    form_snapshot: list[AnalysisTemplate],
) -> ExperimentSummary | None:
    row = conn.execute(
        "SELECT sample_id, created_at FROM experiments WHERE exp_id = ?", (exp_id,)
    ).fetchone()
    if row is None:
        return None
    conn.execute(
        "UPDATE experiments SET requested_analyses = ?, form = ? WHERE exp_id = ?",
        (
            json.dumps(requested_analyses),
            json.dumps([t.model_dump() for t in form_snapshot]),
            exp_id,
        ),
    )
    conn.commit()
    return ExperimentSummary(
        exp_id=exp_id,
        sample_id=row["sample_id"],
        requested_analyses=requested_analyses,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def delete(conn: sqlite3.Connection, exp_id: str) -> bool:
    cur = conn.execute("DELETE FROM experiments WHERE exp_id = ?", (exp_id,))
    conn.commit()
    return cur.rowcount > 0
