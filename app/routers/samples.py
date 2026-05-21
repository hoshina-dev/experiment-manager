"""Router for sample catalogue resources, mounted at /api/samples."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.sample_service as service
from app.database import get_db
from app.models import (AnalysesListResponse, AnalysisTemplate, SamplesListResponse,
                        SampleCreate, SampleSummary, SampleUpdate,
                        TemplateCreate, TemplateUpdate)

router = APIRouter(prefix="/api/samples", tags=["samples"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=SampleSummary, status_code=201)
async def create_sample(body: SampleCreate, db: DbDep) -> SampleSummary:
    return await service.create_sample(db, body)


@router.get("", response_model=SamplesListResponse)
async def list_samples(db: DbDep) -> SamplesListResponse:
    return await service.get_samples(db)


@router.get("/{sample_id}", response_model=SampleSummary)
async def get_sample(sample_id: uuid.UUID, db: DbDep) -> SampleSummary:
    result = await service.get_sample(db, sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.put("/{sample_id}", response_model=SampleSummary)
async def update_sample(
    sample_id: uuid.UUID, body: SampleUpdate, db: DbDep
) -> SampleSummary:
    result = await service.update_sample(db, sample_id, body)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.delete("/{sample_id}", status_code=204)
async def delete_sample(sample_id: uuid.UUID, db: DbDep) -> None:
    if not await service.delete_sample(db, sample_id):
        raise HTTPException(404, f'Sample "{sample_id}" not found')


# ---------------------------------------------------------------------------
# Analysis templates nested under a sample
# ---------------------------------------------------------------------------


@router.post("/{sample_id}/analyses", response_model=AnalysisTemplate, status_code=201)
async def create_analysis(
    sample_id: uuid.UUID, body: TemplateCreate, db: DbDep
) -> AnalysisTemplate:
    result = await service.create_analysis(db, sample_id, body)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.get("/{sample_id}/analyses", response_model=AnalysesListResponse)
async def list_analyses(sample_id: uuid.UUID, db: DbDep) -> AnalysesListResponse:
    result = await service.get_analyses(db, sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.get("/{sample_id}/analyses/{template_id}", response_model=AnalysisTemplate)
async def get_analysis(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> AnalysisTemplate:
    result = await service.get_analysis(db, sample_id, template_id)
    if result is None:
        raise HTTPException(404, f'Template "{template_id}" not found')
    return result


@router.put("/{sample_id}/analyses/{template_id}", response_model=AnalysisTemplate)
async def update_analysis(
    sample_id: uuid.UUID, template_id: uuid.UUID, body: TemplateUpdate, db: DbDep
) -> AnalysisTemplate:
    result = await service.update_analysis(db, sample_id, template_id, body)
    if result is None:
        raise HTTPException(404, f'Template "{template_id}" not found')
    return result


@router.delete("/{sample_id}/analyses/{template_id}", status_code=204)
async def delete_analysis(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> None:
    if not await service.delete_analysis(db, sample_id, template_id):
        raise HTTPException(404, f'Template "{template_id}" not found')
