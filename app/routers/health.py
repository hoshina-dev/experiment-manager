from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import r2_settings
from app.database import get_db
from app.pdf.r2_client import check_connection

router = APIRouter(tags="health")

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/ready")
async def ready_check(db: DbDep):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable",
        )

    try:
        check_connection(r2_settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"storage unavailable",
        )

    return {"status": "ready"}
