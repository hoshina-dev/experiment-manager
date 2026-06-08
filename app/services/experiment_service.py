"""Business logic for experiments, with OTEL spans on every operation."""

import asyncio
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
                        ExperimentUpdate, ReportDownloadResponse)
from app.pdf.r2_client import presign_download
from app.report_worker import ReportJob

tracer = trace.get_tracer(__name__)


def _build_state(
    exp_id: uuid.UUID,
    sample_id: uuid.UUID,
    t: ExperimentTemplate,
) -> dict:
    return {
        "id": str(exp_id),
        "sample_id": str(sample_id),
        "template_id": str(t.id),  # frozen specific version id
        "lineage_id": str(t.lineage_id),
        **t.template,
    }


def _row_to_summary(row) -> ExperimentSummary:
    return ExperimentSummary(
        id=row.state["id"],
        sample_id=row.state["sample_id"],
        template_id=row.state["template_id"],
        report_status=row.report_status,
        created_at=row.created_at,
    )


def _row_to_detail(row) -> ExperimentDetail:
    return ExperimentDetail(
        report_status=row.report_status,
        report_r2_key=row.report_r2_key,
        report_generated_at=row.report_generated_at,
        created_at=row.created_at,
        **row.state,
    )


async def create_experiment(
    session: AsyncSession, body: ExperimentCreate
) -> ExperimentDetail:
    with tracer.start_as_current_span("experiment_service.create") as span:
        span.set_attribute("exp_id", str(body.exp_id))
        span.set_attribute("sample.id", str(body.sample_id))

        sample = await sample_repo.get_sample_type(session, body.sample_id)
        if sample is None:
            raise HTTPException(
                status_code=404, detail=f'Sample "{body.sample_id}" not found'
            )

        template_row = await sample_repo.get_current_template_by_lineage(
            session, body.sample_id, body.lineage_id
        )
        if template_row is None:
            raise HTTPException(
                status_code=404,
                detail=f'Template lineage "{body.lineage_id}" not found for sample "{body.sample_id}"',
            )

        state = _build_state(body.exp_id, body.sample_id, template_row)

        try:
            row = await experiment_repo.create(session, body.exp_id, state)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409, detail=f'Experiment "{body.exp_id}" already exists'
            )

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

        state = {
            **existing.state,
            "userForm": body.userForm,
            "workerForm": body.workerForm.model_dump(),
            "calculations": body.calculations,
            "template": body.template,
        }

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


async def request_report(
    session: AsyncSession,
    exp_id: uuid.UUID,
    queue: asyncio.Queue,
) -> None:
    with tracer.start_as_current_span("experiment_service.request_report") as span:
        span.set_attribute("exp.id", str(exp_id))

        row = await experiment_repo.get(session, exp_id)
        if row is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')

        if row.report_status in ("pending", "processing"):
            raise HTTPException(409, f"Report is already {row.report_status}")

        pdf_components = await experiment_repo.get_pdf_components(
            session, uuid.UUID(row.state["template_id"])
        )
        if not pdf_components:
            raise HTTPException(
                422, "No PDF template defined for this experiment template"
            )

        job = ReportJob(
            exp_id=exp_id,
            experiment_data=row.state,
            pdf_components=pdf_components,
            template_name=row.state["title"],
        )

        try:
            queue.put_nowait(job)
        except asyncio.QueueFull:
            raise HTTPException(503, "Report queue is full — try again later")

        await experiment_repo.update_report_status(session, exp_id, "pending")
        await session.commit()


async def get_report_download_url(
    session: AsyncSession,
    exp_id: uuid.UUID,
    r2_cfg,
) -> ReportDownloadResponse:
    with tracer.start_as_current_span(
        "experiment_service.get_report_download_url"
    ) as span:
        span.set_attribute("exp.id", str(exp_id))

        row = await experiment_repo.get(session, exp_id)
        if row is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')

        if not row.report_r2_key:
            raise HTTPException(404, "Report not yet available")

        filename = f"{row.state['title']}.pdf"
        expires_in = 900

        url = presign_download(row.report_r2_key, r2_cfg, filename, expires_in)
        return ReportDownloadResponse(url=url, expires_in=expires_in)
