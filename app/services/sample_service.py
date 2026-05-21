"""Business logic for the sample catalogue, with OTEL spans on every operation."""

import uuid

from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.sample_repository as repo
from app.db_models import ExperimentTemplate
from app.models import (AnalysesListResponse, AnalysisSummary, AnalysisTemplate,
                        SamplesListResponse, SampleCreate, SampleSummary,
                        SampleUpdate, TemplateCreate, TemplateUpdate)

tracer = trace.get_tracer(__name__)


def _template_to_analysis(t: ExperimentTemplate) -> AnalysisTemplate:
    return AnalysisTemplate(
        id=t.id,
        name=t.name,
        description=t.description,
        **t.template,
    )


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


async def create_sample(
    session: AsyncSession, body: SampleCreate
) -> SampleSummary:
    with tracer.start_as_current_span("sample_service.create_sample"):
        row = await repo.create_sample_type(session, body.name, body.description)
        await session.commit()
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def update_sample(
    session: AsyncSession, sample_id: uuid.UUID, body: SampleUpdate
) -> SampleSummary | None:
    with tracer.start_as_current_span("sample_service.update_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        row = await repo.update_sample_type(session, sample_id, body.name, body.description)
        if row is None:
            return None
        await session.commit()
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def delete_sample(session: AsyncSession, sample_id: uuid.UUID) -> bool:
    with tracer.start_as_current_span("sample_service.delete_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        deleted = await repo.delete_sample_type(session, sample_id)
        if deleted:
            await session.commit()
        return deleted


async def get_analyses(
    session: AsyncSession, sample_type_id: uuid.UUID
) -> AnalysesListResponse | None:
    with tracer.start_as_current_span("sample_service.get_analyses") as span:
        span.set_attribute("sample.id", str(sample_type_id))
        sample = await repo.get_sample_type(session, sample_type_id)
        if sample is None:
            return None
        templates = await repo.list_templates(session, sample_type_id)
        return AnalysesListResponse(
            sample_id=sample.id,
            analyses=[
                AnalysisSummary(id=t.id, name=t.name, description=t.description)
                for t in templates
            ],
        )


async def get_analysis(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> AnalysisTemplate | None:
    with tracer.start_as_current_span("sample_service.get_analysis") as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        row = await repo.get_template(session, sample_id, template_id)
        if row is None:
            return None
        return _template_to_analysis(row)


async def create_analysis(
    session: AsyncSession, sample_id: uuid.UUID, body: TemplateCreate
) -> AnalysisTemplate | None:
    with tracer.start_as_current_span("sample_service.create_analysis") as span:
        span.set_attribute("sample.id", str(sample_id))
        sample = await repo.get_sample_type(session, sample_id)
        if sample is None:
            return None
        template_data = body.model_dump(exclude={"name", "description"}, exclude_none=True)
        row = await repo.create_template(
            session, sample_id, body.name, body.description, template_data
        )
        await session.commit()
        return _template_to_analysis(row)


async def update_analysis(
    session: AsyncSession,
    sample_id: uuid.UUID,
    template_id: uuid.UUID,
    body: TemplateUpdate,
) -> AnalysisTemplate | None:
    with tracer.start_as_current_span("sample_service.update_analysis") as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        template_data = body.model_dump(exclude={"name", "description"}, exclude_none=True)
        row = await repo.update_template(
            session, sample_id, template_id, body.name, body.description, template_data
        )
        if row is None:
            return None
        await session.commit()
        return _template_to_analysis(row)


async def delete_analysis(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> bool:
    with tracer.start_as_current_span("sample_service.delete_analysis") as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        deleted = await repo.delete_template(session, sample_id, template_id)
        if deleted:
            await session.commit()
        return deleted
