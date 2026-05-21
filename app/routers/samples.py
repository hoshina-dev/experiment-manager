"""Router for sample catalogue resources, mounted at /api/samples."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.sample_service as service
from app.database import get_db
from app.models import AnalysesListResponse, SamplesListResponse

router = APIRouter(prefix="/api/samples", tags=["samples"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=SamplesListResponse)
async def list_samples(db: DbDep) -> SamplesListResponse:
    return await service.get_samples(db)


@router.get("/{sample_id}/analyses", response_model=AnalysesListResponse)
async def list_analyses(sample_id: uuid.UUID, db: DbDep) -> AnalysesListResponse:
    result = await service.get_analyses(db, sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result
