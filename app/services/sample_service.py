"""Business logic for the sample catalogue, with OTEL spans on every operation."""

import uuid

from fastapi import HTTPException
from opentelemetry import trace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.experiment_repository as experiment_repo
import app.repositories.sample_repository as repo
from app.db_models import ExperimentTemplate
from app.models import (ExperimentTemplateCreate, ExperimentTemplateDetail,
                        ExperimentTemplateHistoryResponse,
                        ExperimentTemplatesResponse, ExperimentTemplateSummary,
                        ExperimentTemplateUpdate, SampleCreate,
                        SamplesListResponse, SampleSummary, SampleUpdate)

tracer = trace.get_tracer(__name__)


def _to_summary(t: ExperimentTemplate) -> ExperimentTemplateSummary:
    return ExperimentTemplateSummary(
        id=t.id,
        lineage_id=t.lineage_id,
        name=t.name,
        description=t.description,
        version=t.version,
        is_current=t.is_current,
    )


def _to_detail(t: ExperimentTemplate) -> ExperimentTemplateDetail:
    return ExperimentTemplateDetail(
        id=t.id,
        lineage_id=t.lineage_id,
        name=t.name,
        version=t.version,
        is_current=t.is_current,
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


async def get_sample(session: AsyncSession, sample_id: uuid.UUID) -> SampleSummary:
    with tracer.start_as_current_span("sample_service.get_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        row = await repo.get_sample_type(session, sample_id)
        if row is None:
            raise HTTPException(404, f'Sample "{sample_id}" not found')
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def create_sample(session: AsyncSession, body: SampleCreate) -> SampleSummary:
    with tracer.start_as_current_span("sample_service.create_sample"):
        try:
            row = await repo.create_sample_type(session, body.name, body.description)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(409, f'Sample "{body.name}" already exists')
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def update_sample(
    session: AsyncSession, sample_id: uuid.UUID, body: SampleUpdate
) -> SampleSummary:
    with tracer.start_as_current_span("sample_service.update_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        try:
            row = await repo.update_sample_type(
                session, sample_id, body.name, body.description
            )
            if row is None:
                raise HTTPException(404, f'Sample "{sample_id}" not found')
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(409, f'Sample name "{body.name}" already taken')
        return SampleSummary(id=row.id, name=row.name, description=row.description)


async def delete_sample(session: AsyncSession, sample_id: uuid.UUID) -> None:
    with tracer.start_as_current_span("sample_service.delete_sample") as span:
        span.set_attribute("sample.id", str(sample_id))
        if not await repo.delete_sample_type(session, sample_id):
            raise HTTPException(404, f'Sample "{sample_id}" not found')
        await session.commit()


async def get_experiment_templates(
    session: AsyncSession, sample_id: uuid.UUID
) -> ExperimentTemplatesResponse:
    with tracer.start_as_current_span(
        "sample_service.get_experiment_templates"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        sample = await repo.get_sample_type(session, sample_id)
        if sample is None:
            raise HTTPException(404, f'Sample "{sample_id}" not found')
        templates = await repo.list_templates(session, sample_id)
        return ExperimentTemplatesResponse(
            sample_id=sample.id,
            experiments=[_to_summary(t) for t in templates],
        )


async def get_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> ExperimentTemplateDetail:
    with tracer.start_as_current_span("sample_service.get_experiment_template") as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        row = await repo.get_template(session, sample_id, template_id)
        if row is None:
            raise HTTPException(404, f'Experiment template "{template_id}" not found')
        return _to_detail(row)


async def get_experiment_template_history(
    session: AsyncSession, sample_id: uuid.UUID, lineage_id: uuid.UUID
) -> ExperimentTemplateHistoryResponse:
    with tracer.start_as_current_span(
        "sample_service.get_experiment_template_history"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("lineage.id", str(lineage_id))
        rows = await repo.list_template_history(session, sample_id, lineage_id)
        if not rows:
            raise HTTPException(404, f'Template lineage "{lineage_id}" not found')
        return ExperimentTemplateHistoryResponse(
            lineage_id=lineage_id,
            versions=[_to_summary(t) for t in rows],
        )


async def create_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, body: ExperimentTemplateCreate
) -> ExperimentTemplateDetail:
    with tracer.start_as_current_span(
        "sample_service.create_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        if await repo.get_sample_type(session, sample_id) is None:
            raise HTTPException(404, f'Sample "{sample_id}" not found')
        template_data = body.model_dump(exclude_none=True)
        try:
            row = await repo.create_template(
                session, sample_id, body.title, body.description, template_data
            )
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                409,
                f'Experiment template "{body.title}" already exists for this sample',
            )
        return _to_detail(row)


async def update_experiment_template(
    session: AsyncSession,
    sample_id: uuid.UUID,
    lineage_id: uuid.UUID,
    body: ExperimentTemplateUpdate,
) -> ExperimentTemplateDetail:
    with tracer.start_as_current_span(
        "sample_service.update_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("lineage.id", str(lineage_id))

        current = await repo.get_current_template_by_lineage(
            session, sample_id, lineage_id
        )
        if current is None:
            raise HTTPException(404, f'Template lineage "{lineage_id}" not found')

        template_data = body.model_dump(exclude_none=True)
        has_experiments = await experiment_repo.any_experiment_uses_template(
            session, current.id
        )

        try:
            if has_experiments:
                row = await repo.create_new_template_version(
                    session,
                    sample_id,
                    lineage_id,
                    body.title,
                    body.description,
                    template_data,
                )
            else:
                row = await repo.update_template_in_place(
                    session,
                    sample_id,
                    current.id,
                    body.title,
                    body.description,
                    template_data,
                )
            assert (
                row is not None
            )  # current validated non-None above; both paths only return None if current is None
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                409,
                f'Experiment template "{body.title}" already exists for this sample',
            )
        return _to_detail(row)


async def delete_experiment_template(
    session: AsyncSession, sample_id: uuid.UUID, template_id: uuid.UUID
) -> None:
    with tracer.start_as_current_span(
        "sample_service.delete_experiment_template"
    ) as span:
        span.set_attribute("sample.id", str(sample_id))
        span.set_attribute("template.id", str(template_id))
        if not await repo.delete_template(session, sample_id, template_id):
            raise HTTPException(404, f'Experiment template "{template_id}" not found')
        await session.commit()
