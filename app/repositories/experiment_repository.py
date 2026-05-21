"""CRUD repository for experiments against Postgres via SQLAlchemy async."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Experiment


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
