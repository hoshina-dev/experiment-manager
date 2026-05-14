"""CRUD router for form resources, mounted at ``/api/forms``."""

import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.models import FormPayload, FormsListResponse, FormSummary

router = APIRouter(prefix="/api/forms", tags=["forms"])

# When FastAPI sees this type on a parameter,
# it automatically calls get_connection() and passes the result in.
# So each route gets a database connection without having to ask for it manually.
ConnDep = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("")
def list_forms(conn: ConnDep) -> FormsListResponse:
    """Return a summary list of all forms, ordered alphabetically by title.
    """
    rows = conn.execute("SELECT id, title, description FROM forms ORDER BY title").fetchall()
    return FormsListResponse(forms=[FormSummary(**dict(r)) for r in rows])


@router.post("", status_code=201)
def create_form(payload: FormPayload, conn: ConnDep) -> dict[str, str]:
    """Persist a new form and return its id.

    The full payload is serialised to JSON and stored in the ``data`` column so
    that all fields (including nested dicts) survive round-trips without
    requiring additional columns.

    Raises:
        HTTPException(409): If a form with ``payload.id`` already exists
            (``UNIQUE`` constraint violation on the primary key).
    """
    try:
        conn.execute(
            "INSERT INTO forms (id, title, description, data) VALUES (?, ?, ?, ?)",
            (payload.id, payload.title, payload.description, payload.model_dump_json()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, f'Form with id "{payload.id}" already exists')
    return {"id": payload.id}


@router.get("/{form_id}")
def get_form(form_id: str, conn: ConnDep) -> FormPayload:
    """Fetch a single form by its id.

    Only the ``data`` column is retrieved; the full :class:`~app.models.FormPayload`
    is reconstructed by deserialising that JSON blob.

    Raises:
        HTTPException(404): If no form with ``form_id`` exists.
    """
    row = conn.execute("SELECT data FROM forms WHERE id = ?", (form_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Not found")
    return FormPayload(**json.loads(row["data"]))


@router.put("/{form_id}")
def update_form(form_id: str, payload: FormPayload, conn: ConnDep) -> dict[str, str]:
    """Create or fully replace a form.

    Uses an ``INSERT … ON CONFLICT … DO UPDATE`` statement so the operation is
    idempotent: if the form does not exist it is created; if it does, all
    mutable columns are overwritten.

    Raises:
        HTTPException(400): If ``payload.id`` differs from ``form_id``.
    """
    if payload.id != form_id:
        raise HTTPException(400, f'Body id "{payload.id}" does not match URL id "{form_id}"')
    conn.execute(
        """INSERT INTO forms (id, title, description, data) VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             title = excluded.title,
             description = excluded.description,
             data = excluded.data""",
        (payload.id, payload.title, payload.description, payload.model_dump_json()),
    )
    conn.commit()
    return {"id": form_id}


@router.delete("/{form_id}")
def delete_form(form_id: str, conn: ConnDep) -> dict[str, str]:
    """Delete a form by its id.

    Checks ``cursor.rowcount`` after the DELETE to distinguish a successful
    deletion from an attempt to delete a non-existent form.

    Raises:
        HTTPException(404): If no form with ``form_id`` exists.
    """
    cur = conn.execute("DELETE FROM forms WHERE id = ?", (form_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "Not found")
    return {"id": form_id}
