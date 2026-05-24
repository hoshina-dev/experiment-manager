"""Business logic for experiments, with OTEL spans on every operation."""

import uuid

from fastapi import HTTPException
from opentelemetry import trace
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.experiment_repository as experiment_repo
import app.repositories.sample_repository as sample_repo
from app.db_models import ExperimentTemplate
from app.models import (ExperimentCreate, ExperimentDetail,
                        ExperimentsListResponse, ExperimentSummary,
                        ExperimentUpdate)

tracer = trace.get_tracer(__name__)


def _full_template_snapshot(t: ExperimentTemplate) -> dict:
    """Build the full template dict stored in experiment state."""
    return {
        "id": str(t.id),
        "name": t.name,
        "description": t.description,
        **t.template,
    }


def _row_to_summary(row) -> ExperimentSummary:
    state = row.state
    return ExperimentSummary(
        exp_id=row.id,
        sample_id=state["sample_id"],
        template_id=state["template_id"],
        created_at=row.created_at,
    )


def _row_to_detail(row) -> ExperimentDetail:
    state = row.state
    return ExperimentDetail(
        exp_id=row.id,
        sample_id=state["sample_id"],
        template_id=state["template_id"],
        state=state["snapshot"],
        created_at=row.created_at,
    )


async def create_experiment(
    session: AsyncSession, body: ExperimentCreate
) -> ExperimentDetail:
    with tracer.start_as_current_span("experiment_service.create") as span:
        span.set_attribute("exp_id", str(body.exp_id))
        span.set_attribute("sample.id", str(body.sample_id))

        sample = await sample_repo.get_sample_type(session, body.sample_id)
        if sample is None:
            raise HTTPException(status_code=404, detail=f'Sample "{body.sample_id}" not found')

        template_row = await sample_repo.get_template(
            session, body.sample_id, body.template_id
        )
        if template_row is None:
            raise HTTPException(status_code=404, detail=f'Template "{body.template_id}" not found for sample "{body.sample_id}"')

        state = {
            "sample_id": str(body.sample_id),
            "template_id": str(body.template_id),
            "snapshot": _full_template_snapshot(template_row),
        }

        try:
            row = await experiment_repo.create(session, body.exp_id, state)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail=f'Experiment "{body.exp_id}" already exists')

        return _row_to_detail(row)


async def list_experiments(session: AsyncSession) -> ExperimentsListResponse:
    with tracer.start_as_current_span("experiment_service.list"):
        rows = await experiment_repo.list_all(session)
        return ExperimentsListResponse(experiments=[_row_to_summary(r) for r in rows])


async def get_experiment(
    session: AsyncSession, exp_id: uuid.UUID
) -> ExperimentDetail | None:
    with tracer.start_as_current_span("experiment_service.get") as span:
        span.set_attribute("exp_id", str(exp_id))
        row = await experiment_repo.get(session, exp_id)
        return _row_to_detail(row) if row else None


async def update_experiment(
    session: AsyncSession, exp_id: uuid.UUID, body: ExperimentUpdate
) -> ExperimentDetail | None:
    with tracer.start_as_current_span("experiment_service.update") as span:
        span.set_attribute("exp_id", str(exp_id))

        existing = await experiment_repo.get(session, exp_id)
        if existing is None:
            return None

        state = {**existing.state, "snapshot": body.state}

        row = await experiment_repo.update(session, exp_id, state)
        await session.commit()
        return _row_to_detail(row)


async def delete_experiment(session: AsyncSession, exp_id: uuid.UUID) -> bool:
    with tracer.start_as_current_span("experiment_service.delete") as span:
        span.set_attribute("exp_id", str(exp_id))
        deleted = await experiment_repo.delete(session, exp_id)
        if deleted:
            await session.commit()
        return deleted
