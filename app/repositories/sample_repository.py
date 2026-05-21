"""Read-only repository for sample types and analysis templates."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import ExperimentTemplate, SampleType


async def list_sample_types(session: AsyncSession) -> list[SampleType]:
    result = await session.execute(
        select(SampleType)
        .where(SampleType.deleted_at.is_(None))
        .order_by(SampleType.name)
    )
    return list(result.scalars().all())


async def get_sample_type(
    session: AsyncSession, sample_type_id: uuid.UUID
) -> SampleType | None:
    result = await session.execute(
        select(SampleType).where(
            SampleType.id == sample_type_id,
            SampleType.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_templates(
    session: AsyncSession, sample_type_id: uuid.UUID
) -> list[ExperimentTemplate]:
    result = await session.execute(
        select(ExperimentTemplate)
        .where(
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.deleted_at.is_(None),
        )
        .order_by(ExperimentTemplate.name)
    )
    return list(result.scalars().all())


async def get_templates_by_ids(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    template_ids: list[uuid.UUID],
) -> list[ExperimentTemplate]:
    """Fetch templates belonging to a sample type by a list of IDs.

    Unknown IDs are silently omitted from the result.
    """
    result = await session.execute(
        select(ExperimentTemplate).where(
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.id.in_(template_ids),
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    rows = {r.id: r for r in result.scalars().all()}
    return [rows[tid] for tid in template_ids if tid in rows]
