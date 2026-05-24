"""Router for sample catalogue resources, mounted at /api/samples."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.sample_service as service
from app.database import get_db
from app.models import (ExperimentTemplateCreate, ExperimentTemplateDetail,
                        ExperimentTemplatesResponse, ExperimentTemplateUpdate,
                        SampleCreate, SampleSummary, SamplesListResponse, SampleUpdate)

router = APIRouter(prefix="/api/samples", tags=["samples"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", status_code=201)
async def create_sample(body: SampleCreate, db: DbDep) -> SampleSummary:
    return await service.create_sample(db, body)


@router.get("")
async def list_samples(db: DbDep) -> SamplesListResponse:
    return await service.get_samples(db)


@router.get("/{sample_id}")
async def get_sample(sample_id: uuid.UUID, db: DbDep) -> SampleSummary:
    result = await service.get_sample(db, sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.put("/{sample_id}")
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
# Experiment templates nested under a sample
# ---------------------------------------------------------------------------


@router.post("/{sample_id}/experiments", status_code=201)
async def create_experiment_template(
    sample_id: uuid.UUID, body: ExperimentTemplateCreate, db: DbDep
) -> ExperimentTemplateDetail:
    result = await service.create_experiment_template(db, sample_id, body)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.get("/{sample_id}/experiments")
async def list_experiment_templates(
    sample_id: uuid.UUID, db: DbDep
) -> ExperimentTemplatesResponse:
    result = await service.get_experiment_templates(db, sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result


@router.get("/{sample_id}/experiments/{template_id}")
async def get_experiment_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> ExperimentTemplateDetail:
    result = await service.get_experiment_template(db, sample_id, template_id)
    if result is None:
        raise HTTPException(404, f'Experiment template "{template_id}" not found')
    return result


@router.put("/{sample_id}/experiments/{template_id}")
async def update_experiment_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, body: ExperimentTemplateUpdate, db: DbDep
) -> ExperimentTemplateDetail:
    result = await service.update_experiment_template(db, sample_id, template_id, body)
    if result is None:
        raise HTTPException(404, f'Experiment template "{template_id}" not found')
    return result


@router.delete("/{sample_id}/experiments/{template_id}", status_code=204)
async def delete_experiment_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> None:
    if not await service.delete_experiment_template(db, sample_id, template_id):
        raise HTTPException(404, f'Experiment template "{template_id}" not found')
