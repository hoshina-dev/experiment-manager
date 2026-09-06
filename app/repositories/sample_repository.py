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
        .options(selectinload(ExperimentTemplate.pdf_template))
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
        .options(selectinload(ExperimentTemplate.pdf_template))
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
        select(ExperimentTemplate)
        .options(selectinload(ExperimentTemplate.pdf_template))
        .where(
            ExperimentTemplate.id == template_id,
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_current_template_by_lineage(
    session: AsyncSession,
    sample_type_id: uuid.UUID,
    lineage_id: uuid.UUID,
    lock: bool = False,
) -> ExperimentTemplate | None:
    """Fetch the current version of a template by lineage_id.

    Eagerly loads pdf_template so callers can access it without triggering
    async lazy loading (which raises MissingGreenlet in SQLAlchemy async).

    `lock=True` takes a `SELECT ... FOR UPDATE` row lock, held until the
    caller's transaction commits/rolls back. Every caller that decides
    in-place-mutate-vs-fork based on "does an experiment reference this row
    yet" (`update_experiment_template`, `upsert_pdf_template`) and every
    caller that creates an experiment against this row (`create_experiment`)
    must pass `lock=True` — they all need to serialize on the same row so
    the has-experiments check can't go stale between reading it and acting
    on it.
    """
    stmt = (
        select(ExperimentTemplate)
        .options(selectinload(ExperimentTemplate.pdf_template))
        .where(
            ExperimentTemplate.lineage_id == lineage_id,
            ExperimentTemplate.sample_type_id == sample_type_id,
            ExperimentTemplate.is_current.is_(True),
            ExperimentTemplate.deleted_at.is_(None),
        )
    )
    if lock:
        stmt = stmt.with_for_update()
    result = await session.execute(stmt)
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
    row.pdf_template = None  # brand-new row, avoid triggering a lazy load
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
    override_pdf_components: list | None = None,
) -> ExperimentTemplate | None:
    """SCD2 write: retire the current version and insert a new one.

    Clones the existing PdfTemplate to the new row by default. Pass
    override_pdf_components to replace the layout instead of cloning — used
    when the editor saves a PDF-only change.
    """
    current = await get_current_template_by_lineage(session, sample_type_id, lineage_id)
    if current is None:
        return None

    # Snapshot pdf components before retiring the current row
    old_pdf_components: list = []
    if current.pdf_template is not None:
        old_pdf_components = list(current.pdf_template.components)
        current.pdf_template.is_current = False

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

    final_components = override_pdf_components if override_pdf_components is not None else old_pdf_components
    new_pdf = PdfTemplate(template_id=new_row.id, components=final_components, is_current=True)
    session.add(new_pdf)
    await session.flush()
    new_row.pdf_template = new_pdf  # keep in-memory relationship consistent, avoid a lazy load

    return new_row


# ---------------------------------------------------------------------------
# PdfTemplate writes
# ---------------------------------------------------------------------------


async def get_pdf_template(
    session: AsyncSession, template_id: uuid.UUID
) -> PdfTemplate | None:
    result = await session.execute(
        select(PdfTemplate).where(PdfTemplate.template_id == template_id)
    )
    return result.scalar_one_or_none()


async def create_pdf_template(
    session: AsyncSession, template_id: uuid.UUID, components: list
) -> PdfTemplate:
    row = PdfTemplate(template_id=template_id, components=components, is_current=True)
    session.add(row)
    await session.flush()
    return row


async def update_pdf_template_in_place(
    session: AsyncSession, template_id: uuid.UUID, components: list
) -> PdfTemplate | None:
    row = await get_pdf_template(session, template_id)
    if row is None:
        return None
    row.components = components
    await session.flush()
    return row


async def delete_pdf_template(
    session: AsyncSession, template_id: uuid.UUID
) -> bool:
    row = await get_pdf_template(session, template_id)
    if row is None:
        return False
    await session.delete(row)
    await session.flush()
    return True


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
