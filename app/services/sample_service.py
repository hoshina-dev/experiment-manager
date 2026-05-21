"""Business logic for the sample catalogue, with OTEL spans on every operation."""

import uuid

from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.sample_repository as repo
from app.models import (AnalysesListResponse, AnalysisSummary,
                        SamplesListResponse, SampleSummary)

tracer = trace.get_tracer(__name__)


async def get_samples(session: AsyncSession) -> SamplesListResponse:
    with tracer.start_as_current_span("sample_service.get_samples"):
        rows = await repo.list_sample_types(session)
        return SamplesListResponse(
            samples=[
                SampleSummary(id=r.id, name=r.name, description=r.description)
                for r in rows
            ]
        )


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
                AnalysisSummary(id=t.id, label=t.name, description=t.description)
                for t in templates
            ],
        )
