import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.models import FormPayload

router = APIRouter(prefix="/api/forms", tags=["forms"])
ConnDep = Annotated[sqlite3.Connection, Depends(get_connection)]

@router.get("")
def list_forms(conn: ConnDep):
    rows = conn.execute(
        "SELECT id, title, description FROM forms ORDER BY title"
    ).fetchall()
    return {"forms": [dict(r) for r in rows]}


@router.post("", status_code=201)
def create_form(payload: FormPayload, conn: ConnDep):
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
def get_form(form_id: str, conn: ConnDep):
    row = conn.execute("SELECT data FROM forms WHERE id = ?", (form_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Not found")
    return json.loads(row["data"])


@router.put("/{form_id}")
def update_form(form_id: str, payload: FormPayload, conn: ConnDep):
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
def delete_form(form_id: str, conn: ConnDep):
    cur = conn.execute("DELETE FROM forms WHERE id = ?", (form_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "Not found")
    return {"id": form_id}
