"""CRUD repository for experiments against Postgres via SQLAlchemy async."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Experiment, PdfTemplate

logger = logging.getLogger(__name__)

_REPORT_STATUS_PENDING = "pending"
_REPORT_STATUS_PROCESSING = "processing"
_REPORT_STATUS_SUCCESS = "success"
_REPORT_STATUS_FAILED = "failed"


async def create(
    session: AsyncSession,
    exp_id: uuid.UUID,
    state: dict,
) -> Experiment:
    """Insert a new experiment row.

    Uses session.flush() so the PK UNIQUE constraint raises IntegrityError
    immediately on duplicate exp_id, without committing.  The service layer
    catches IntegrityError and commits on success.
    """
    experiment = Experiment(id=exp_id, state=state)
    session.add(experiment)
    await session.flush()
    return experiment


async def any_experiment_uses_template(
    session: AsyncSession, template_id: uuid.UUID
) -> bool:
    """Return True if at least one non-deleted experiment was created from this template version."""
    result = await session.execute(
        select(
            exists().where(
                Experiment.state["template_id"].astext == str(template_id),
                Experiment.deleted_at.is_(None),
            )
        )
    )
    return bool(result.scalar())


async def list_all(session: AsyncSession) -> list[Experiment]:
    result = await session.execute(
        select(Experiment)
        .where(Experiment.deleted_at.is_(None))
        .order_by(Experiment.created_at.desc())
    )
    return list(result.scalars().all())


async def get(session: AsyncSession, exp_id: uuid.UUID) -> Experiment | None:
    result = await session.execute(
        select(Experiment).where(
            Experiment.id == exp_id,
            Experiment.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def update(
    session: AsyncSession,
    exp_id: uuid.UUID,
    state: dict,
) -> Experiment | None:
    experiment = await get(session, exp_id)
    if experiment is None:
        return None
    experiment.state = state
    await session.flush()
    return experiment


async def delete(session: AsyncSession, exp_id: uuid.UUID) -> bool:
    """Soft-delete by setting deleted_at."""
    experiment = await get(session, exp_id)
    if experiment is None:
        return False
    experiment.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True


async def list_orphaned_reports(session: AsyncSession) -> list[Experiment]:
    result = await session.execute(
        select(Experiment).where(
            Experiment.report_status.in_(
                [_REPORT_STATUS_PENDING, _REPORT_STATUS_PROCESSING]
            ),
            Experiment.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def get_pdf_components(session: AsyncSession, template_id: uuid.UUID) -> list:
    result = await session.execute(
        select(PdfTemplate).where(PdfTemplate.template_id == template_id)
    )
    row = result.scalar_one_or_none()
    return row.components if row else []


async def update_report_status(
    session: AsyncSession, exp_id: uuid.UUID, status: str
) -> None:
    experiment = await get(session, exp_id)
    if experiment is None:
        logger.warning(
            "update_report_status: experiment %s not found — status '%s' not written",
            exp_id,
            status,
        )
        return
    experiment.report_status = status
    await session.flush()


async def update_report_success(
    session: AsyncSession, exp_id: uuid.UUID, r2_key: str
) -> None:
    experiment = await get(session, exp_id)
    if experiment is None:
        logger.warning(
            "update_report_success: experiment %s not found — success not written (r2_key=%s)",
            exp_id,
            r2_key,
        )
        return
    experiment.report_status = _REPORT_STATUS_SUCCESS
    experiment.report_r2_key = r2_key
    experiment.report_generated_at = datetime.now(timezone.utc)
    experiment.report_error = None
    await session.flush()


async def update_report_failure(
    session: AsyncSession, exp_id: uuid.UUID, error: str
) -> None:
    experiment = await get(session, exp_id)
    if experiment is None:
        logger.warning(
            "update_report_failure: experiment %s not found — failure not written (error=%s)",
            exp_id,
            error,
        )
        return
    experiment.report_status = _REPORT_STATUS_FAILED
    experiment.report_error = error
    await session.flush()
