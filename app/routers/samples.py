"""Router for sample catalogue resources, mounted at /api/samples."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.sample_service as service
from app.database import get_db
from app.models import (
    ExperimentTemplateCreate,
    ExperimentTemplateDetail,
    ExperimentTemplateHistoryResponse,
    ExperimentTemplatesResponse,
    ExperimentTemplateSummary,
    ExperimentTemplateUpdate,
    PdfTemplateBody,
    PdfTemplateResponse,
    SampleCreate,
    SamplesListResponse,
    SampleSummary,
    SampleUpdate,
    SampleWebOrder,
    TemplateWebOrder,
    WebVisibilityUpdate,
)

router = APIRouter(prefix="/api/samples", tags=["samples"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", status_code=201)
async def create_sample(body: SampleCreate, db: DbDep) -> SampleSummary:
    return await service.create_sample(db, body)


@router.get("")
async def list_samples(db: DbDep) -> SamplesListResponse:
    return await service.get_samples(db)


@router.put("/web-order")
async def update_samples_web_order(
    body: SampleWebOrder, db: DbDep
) -> SamplesListResponse:
    return await service.update_samples_web_order(db, body)


@router.get("/{sample_id}")
async def get_sample(sample_id: uuid.UUID, db: DbDep) -> SampleSummary:
    return await service.get_sample(db, sample_id)


@router.put("/{sample_id}")
async def update_sample(
    sample_id: uuid.UUID, body: SampleUpdate, db: DbDep
) -> SampleSummary:
    return await service.update_sample(db, sample_id, body)


@router.delete("/{sample_id}", status_code=204)
async def delete_sample(sample_id: uuid.UUID, db: DbDep) -> None:
    await service.delete_sample(db, sample_id)


# ---------------------------------------------------------------------------
# Experiment templates nested under a sample
# ---------------------------------------------------------------------------


@router.post("/{sample_id}/experiments", status_code=201)
async def create_experiment_template(
    sample_id: uuid.UUID, body: ExperimentTemplateCreate, db: DbDep
) -> ExperimentTemplateDetail:
    return await service.create_experiment_template(db, sample_id, body)


@router.get("/{sample_id}/experiments")
async def list_experiment_templates(
    sample_id: uuid.UUID, db: DbDep
) -> ExperimentTemplatesResponse:
    return await service.get_experiment_templates(db, sample_id)


@router.put("/{sample_id}/experiments/web-order")
async def update_templates_web_order(
    sample_id: uuid.UUID, body: TemplateWebOrder, db: DbDep
) -> ExperimentTemplatesResponse:
    return await service.update_templates_web_order(db, sample_id, body)


@router.patch("/{sample_id}/web-visibility")
async def update_sample_web_visibility(
    sample_id: uuid.UUID, body: WebVisibilityUpdate, db: DbDep
) -> SampleSummary:
    return await service.update_sample_web_visibility(db, sample_id, body)


@router.patch("/{sample_id}/experiments/{lineage_id}/web-visibility")
async def update_template_web_visibility(
    sample_id: uuid.UUID, lineage_id: uuid.UUID, body: WebVisibilityUpdate, db: DbDep
) -> ExperimentTemplateSummary:
    return await service.update_template_web_visibility(db, sample_id, lineage_id, body)


@router.get("/{sample_id}/experiments/{template_id}")
async def get_experiment_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> ExperimentTemplateDetail:
    return await service.get_experiment_template(db, sample_id, template_id)


@router.put("/{sample_id}/experiments/{lineage_id}")
async def update_experiment_template(
    sample_id: uuid.UUID,
    lineage_id: uuid.UUID,
    body: ExperimentTemplateUpdate,
    db: DbDep,
) -> ExperimentTemplateDetail:
    return await service.update_experiment_template(db, sample_id, lineage_id, body)


@router.get("/{sample_id}/experiments/{lineage_id}/history")
async def get_experiment_template_history(
    sample_id: uuid.UUID, lineage_id: uuid.UUID, db: DbDep
) -> ExperimentTemplateHistoryResponse:
    return await service.get_experiment_template_history(db, sample_id, lineage_id)


@router.delete("/{sample_id}/experiments/{template_id}", status_code=204)
async def delete_experiment_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> None:
    await service.delete_experiment_template(db, sample_id, template_id)


# ---------------------------------------------------------------------------
# PDF templates nested under a specific experiment template version
# ---------------------------------------------------------------------------


@router.get("/{sample_id}/experiments/{template_id}/pdf")
async def get_pdf_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> PdfTemplateResponse:
    return await service.get_pdf_template(db, sample_id, template_id)


@router.put("/{sample_id}/experiments/{lineage_id}/pdf")
async def upsert_pdf_template(
    sample_id: uuid.UUID,
    lineage_id: uuid.UUID,
    body: PdfTemplateBody,
    db: DbDep,
) -> PdfTemplateResponse:
    return await service.upsert_pdf_template(db, sample_id, lineage_id, body)


@router.delete("/{sample_id}/experiments/{template_id}/pdf", status_code=204)
async def delete_pdf_template(
    sample_id: uuid.UUID, template_id: uuid.UUID, db: DbDep
) -> None:
    await service.delete_pdf_template(db, sample_id, template_id)
