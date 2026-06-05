"""Business logic for the sample catalogue, with OTEL spans on every operation."""

import uuid

from fastapi import HTTPException
from opentelemetry import trace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.sample_repository as repo
from app.db_models import ExperimentTemplate
from app.models import (ExperimentTemplateCreate, ExperimentTemplateDetail,
                        ExperimentTemplatesResponse, ExperimentTemplateSummary,
                        ExperimentTemplateUpdate, SampleCreate,
                        SamplesListResponse, SampleSummary, SampleUpdate)

tracer = trace.get_tracer(__name__)


def _to_experiment_template_detail(t: ExperimentTemplate) -> ExperimentTemplateDetail:
    return ExperimentTemplateDetail(id=t.id, **t.template)


async def get_samples(session: AsyncSession) -> SamplesListResponse:
    with tracer.start_as_current_span("sample_service.get_samples"):
        rows = await repo.list_sample_types(session)
        return SamplesListResponse(
            samples=[
                SampleSummary(id=r.id, name=r.name, description=r.description)
                for r in rows
            ]
        )


async def get_sample(
    session: AsyncSession, sample_id: uuid.UUID
) -> SampleSummary | None:
    with tracer.start_as_current_span("sample_service.get_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        row = await repo.get_sample_type(session, sample_id)
        if row is None:
            return None
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def create_sample(session: AsyncSession, body: SampleCreate) -> SampleSummary:
    with tracer.start_as_current_span("sample_service.create_sample"):
        try:
            row = await repo.create_sample_type(session, body.name, body.description)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409, detail=f'Sample "{body.name}" already exists'
            )
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def update_sample(
    session: AsyncSession, sample_id: uuid.UUID, body: SampleUpdate
) -> SampleSummary | None:
    with tracer.start_as_current_span("sample_service.update_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        try:
            row = await repo.update_sample_type(
                session, sample_id, body.name, body.description
            )
            if row is None:
                return None
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409, detail=f'Sample name "{body.name}" already exists'
            )
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def delete_sample(session: AsyncSession, sample_id: uuid.UUID) -> bool:
    with tracer.start_as_current_span("sample_service.delete_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        deleted = await repo.delete_sample_type(session, sample_id)
        if deleted:
            await session.commit()
        return deleted


async def get_experiment_templates(
    session: AsyncSession, sample_id: uuid.UUID
) -> ExperimentTemplatesResponse | None:
    with tracer.start_as_current_span(
        "sample_service.get_experiment_templates"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        sample = await repo.get_sample_type(session, sample_id)
        if sample is None:
            return None
        templates = await repo.list_templates(session, sample_id)
        return ExperimentTemplatesResponse(
            sample_id=sample.id,
            experiments=[
                ExperimentTemplateSummary(
                    id=t.id, name=t.name, description=t.description
                )
                for t in templates
            ],
        )


async def get_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> ExperimentTemplateDetail | None:
    with tracer.start_as_current_span("sample_service.get_experiment_template") as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        row = await repo.get_template(session, sample_id, template_id)
        if row is None:
            return None
        return _to_experiment_template_detail(row)


async def create_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, body: ExperimentTemplateCreate
) -> ExperimentTemplateDetail | None:
    with tracer.start_as_current_span(
        "sample_service.create_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        sample = await repo.get_sample_type(session, sample_id)
        if sample is None:
            return None
        template_data = body.model_dump(exclude_none=True)
        try:
            row = await repo.create_template(
                session, sample_id, body.title, body.description, template_data
            )
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail=f'Experiment template "{body.title}" already exists for this sample',
            )
        return _to_experiment_template_detail(row)


async def update_experiment_template(
    session: AsyncSession,
    sample_id: uuid.UUID,
    template_id: uuid.UUID,
    body: ExperimentTemplateUpdate,
) -> ExperimentTemplateDetail | None:
    with tracer.start_as_current_span(
        "sample_service.update_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        template_data = body.model_dump(exclude_none=True)
        try:
            row = await repo.update_template(
                session,
                sample_id,
                template_id,
                body.title,
                body.description,
                template_data,
            )
            if row is None:
                return None
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail=f'Experiment template "{body.title}" already exists for this sample',
            )
        return _to_experiment_template_detail(row)


async def delete_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> bool:
    with tracer.start_as_current_span(
        "sample_service.delete_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        deleted = await repo.delete_template(session, sample_id, template_id)
        if deleted:
            await session.commit()
        return deleted
