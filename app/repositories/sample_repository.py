"""Repository for sample types and analysis templates."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_models import ExperimentTemplate, PdfTemplate, SampleType


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
    """Return only the current version of each template for a sample."""
    result = await session.execute(
        select(ExperimentTemplate)
        .where(
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.is_current.is_(True),
            ExperimentTemplate.deleted_at.is_(None),
        )
        .order_by(ExperimentTemplate.name)
    )
    return list(result.scalars().all())


async def list_template_history(
    session: AsyncSession, sample_type_id: uuid.UUID, lineage_id: uuid.UUID
) -> list[ExperimentTemplate]:
    """Return all versions for a lineage, newest first."""
    result = await session.execute(
        select(ExperimentTemplate)
        .where(
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.lineage_id == lineage_id,
            ExperimentTemplate.deleted_at.is_(None),
        )
        .order_by(ExperimentTemplate.version.desc())
    )
    return list(result.scalars().all())


async def get_template(
    session: AsyncSession, sample_type_id: uuid.UUID, template_id: uuid.UUID
) -> ExperimentTemplate | None:
    """Fetch a specific version row by its id."""
    result = await session.execute(
        select(ExperimentTemplate).where(
            ExperimentTemplate.id == template_id,
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_current_template_by_lineage(
    session: AsyncSession, sample_type_id: uuid.UUID, lineage_id: uuid.UUID
) -> ExperimentTemplate | None:
    """Fetch the current version of a template by lineage_id.

    Eagerly loads pdf_template so callers can access it without triggering
    async lazy loading (which raises MissingGreenlet in SQLAlchemy async).
    """
    result = await session.execute(
        select(ExperimentTemplate)
        .options(selectinload(ExperimentTemplate.pdf_template))
        .where(
            ExperimentTemplate.lineage_id == lineage_id,
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.is_current.is_(True),
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_templates_by_ids(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    template_ids: list[uuid.UUID],
) -> list[ExperimentTemplate]:
    """Fetch specific version rows by a list of ids. Unknown ids are silently omitted."""
    result = await session.execute(
        select(ExperimentTemplate).where(
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.id.in_(template_ids),
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    rows = {r.id: r for r in result.scalars().all()}
    return [rows[tid] for tid in template_ids if tid in rows]


# ---------------------------------------------------------------------------
# SampleType writes
# ---------------------------------------------------------------------------


async def create_sample_type(
    session: AsyncSession, name: str, description: str | None
) -> SampleType:
    row = SampleType(name=name, description=description)
    session.add(row)
    await session.flush()
    return row


async def update_sample_type(
    session: AsyncSession, sample_id: uuid.UUID, name: str, description: str | None
) -> SampleType | None:
    row = await get_sample_type(session, sample_id)
    if row is None:
        return None
    row.name = name
    row.description = description
    await session.flush()
    return row


async def delete_sample_type(session: AsyncSession, sample_id: uuid.UUID) -> bool:
    row = await get_sample_type(session, sample_id)
    if row is None:
        return False
    row.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True


# ---------------------------------------------------------------------------
# ExperimentTemplate writes
# ---------------------------------------------------------------------------


async def create_template(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    name: str,
    description: str | None,
    template_data: dict,
) -> ExperimentTemplate:
    """Insert a brand-new template (v1, starts its own lineage)."""
    new_lineage_id = uuid.uuid4()
    row = ExperimentTemplate(
        lineage_id=new_lineage_id,
        sample_type_id=sample_type_id,
        name=name,
        description=description,
        version=1,
        is_current=True,
        template=template_data,
    )
    session.add(row)
    await session.flush()
    return row


async def update_template_in_place(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    template_id: uuid.UUID,
    name: str,
    description: str | None,
    template_data: dict,
) -> ExperimentTemplate | None:
    """Mutate the current version row directly — only safe when no experiments reference it."""
    row = await get_template(session, sample_type_id, template_id)
    if row is None:
        return None
    row.name = name
    row.description = description
    row.template = template_data
    await session.flush()
    return row


async def create_new_template_version(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    lineage_id: uuid.UUID,
    name: str,
    description: str | None,
    template_data: dict,
) -> ExperimentTemplate | None:
    """SCD2 write: retire the current version and insert a new one.

    Also clones the existing PdfTemplate components to the new version row so
    old experiments keep their frozen PDF layout while the editor starts from
    the previous layout.
    """
    current = await get_current_template_by_lineage(session, sample_type_id, lineage_id)
    if current is None:
        return None

    # Snapshot pdf components before retiring the current row
    old_pdf_components: list = []
    if current.pdf_template is not None:
        old_pdf_components = list(current.pdf_template.components)

    current.is_current = False
    await session.flush()

    new_row = ExperimentTemplate(
        lineage_id=lineage_id,
        sample_type_id=sample_type_id,
        name=name,
        description=description,
        version=current.version + 1,
        is_current=True,
        template=template_data,
    )
    session.add(new_row)
    await session.flush()

    # Clone PDF layout to new version so editor inherits the previous layout
    new_pdf = PdfTemplate(template_id=new_row.id, components=old_pdf_components)
    session.add(new_pdf)
    await session.flush()

    return new_row


async def delete_template(
    session: AsyncSession, sample_type_id: uuid.UUID, template_id: uuid.UUID
) -> bool:
    """Soft-delete a specific version row.

    If the deleted row was current, the lineage has no current version until
    the caller decides how to handle it (promote previous or leave retired).
    """
    row = await get_template(session, sample_type_id, template_id)
    if row is None:
        return False
    row.deleted_at = datetime.now(timezone.utc)
    if row.is_current:
        row.is_current = False
    await session.flush()
    return True
