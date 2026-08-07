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
from app.models import (Calculation, ExperimentCalculationsUpdate,
                        ExperimentCreate, ExperimentDetail,
                        ExperimentsListResponse, ExperimentSummary,
                        ExperimentUpdate, FormDoc, ReportDownloadResponse)
from app.pdf.r2_client import presign_download
from app.report_worker import ReportJob
from app.validation import FormSchemaError, validate_form

tracer = trace.get_tracer(__name__)


def _build_state(
    exp_id: uuid.UUID,
    sample_id: uuid.UUID,
    t: ExperimentTemplate,
) -> dict:
    return {
        "id": str(exp_id),
        "sample_id": str(sample_id),
        "template_id": str(t.id),
        "lineage_id": str(t.lineage_id),
        "name": t.name,
        "description": t.description,
        **t.template,
        "values": {},
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
            session, body.sample_id, body.lineage_id, lock=True
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


async def get_experiment(session: AsyncSession, exp_id: uuid.UUID) -> ExperimentDetail:
    with tracer.start_as_current_span("experiment_service.get") as span:
        span.set_attribute("exp_id", str(exp_id))
        row = await experiment_repo.get(session, exp_id)
        if row is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')
        return _row_to_detail(row)


def _assert_no_template_drift(body: ExperimentUpdate, template: dict) -> None:
    """clientForm/labForm/calculations are owned by the template, not the
    client — reject a PUT if they no longer match (frontend bug or tamper),
    rather than silently persisting whatever was sent. `result` is excluded
    from the calculations comparison since only `/calculate` may write it.
    """
    canonical_client = FormDoc(**template["clientForm"]).model_dump(exclude_none=True)
    canonical_lab = FormDoc(**template["labForm"]).model_dump(exclude_none=True)
    canonical_calc = {
        name: Calculation(**calc).model_dump(exclude_none=True, exclude={"result"})
        for name, calc in template["calculations"].items()
    }

    submitted_client = body.clientForm.model_dump(exclude_none=True)
    submitted_lab = body.labForm.model_dump(exclude_none=True)
    submitted_calc = {
        name: calc.model_dump(exclude_none=True, exclude={"result"})
        for name, calc in body.calculations.items()
    }

    drift: list[str] = []
    if submitted_client != canonical_client:
        drift.append("clientForm")
    if submitted_lab != canonical_lab:
        drift.append("labForm")
    for name in sorted(set(canonical_calc) | set(submitted_calc)):
        if submitted_calc.get(name) != canonical_calc.get(name):
            drift.append(f"calculations.{name}")

    if drift:
        raise HTTPException(
            422,
            {
                "message": "Submitted clientForm/labForm/calculations no "
                "longer match this experiment's template. Only 'values' "
                "can be updated via this endpoint — re-fetch the "
                "experiment to get the canonical form.",
                "drift": drift,
            },
        )


async def update_experiment(
    session: AsyncSession, exp_id: uuid.UUID, body: ExperimentUpdate
) -> ExperimentDetail:
    with tracer.start_as_current_span("experiment_service.update") as span:
        span.set_attribute("exp_id", str(exp_id))
        existing = await experiment_repo.get(session, exp_id)
        if existing is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')

        template_row = await sample_repo.get_template(
            session,
            uuid.UUID(existing.state["sample_id"]),
            uuid.UUID(existing.state["template_id"]),
        )
        if template_row is None:
            raise HTTPException(
                404,
                f'Experiment template "{existing.state["template_id"]}" backing this experiment no longer exists',
            )

        _assert_no_template_drift(body, template_row.template)

        context = {
            **existing.state,
            "clientForm": template_row.template["clientForm"],
            "labForm": template_row.template["labForm"],
            "calculations": template_row.template["calculations"],
            "values": body.values,
        }
        try:
            validate_form(context)
        except FormSchemaError as exc:
            raise HTTPException(
                422,
                {
                    "message": "Experiment context violates schema",
                    "errors": exc.errors,
                },
            )
        row = await experiment_repo.update(session, exp_id, context)
        await session.commit()
        return _row_to_detail(row)


async def update_experiment_calculations(
    session: AsyncSession, exp_id: uuid.UUID, body: ExperimentCalculationsUpdate
) -> ExperimentDetail:
    """Replace this experiment's own calculation formulas, e.g. to fix a
    formula bug on an experiment already stuck on an old template version.
    Scoped to this experiment only — does not touch template_id/version and
    does not affect any other experiment on the same lineage. Results are
    reset to "" (unevaluated); call /calculate afterward to recompute them.
    """
    with tracer.start_as_current_span(
        "experiment_service.update_calculations"
    ) as span:
        span.set_attribute("exp_id", str(exp_id))
        existing = await experiment_repo.get(session, exp_id)
        if existing is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')

        calculations = {
            name: {
                **calc.model_dump(exclude_none=True, exclude={"result"}),
                "result": "",
            }
            for name, calc in body.calculations.items()
        }

        context = {**existing.state, "calculations": calculations}
        try:
            validate_form(context)
        except FormSchemaError as exc:
            raise HTTPException(
                422,
                {
                    "message": "Experiment calculations violate schema",
                    "errors": exc.errors,
                },
            )

        row = await experiment_repo.update(session, exp_id, context)
        await session.commit()
        return _row_to_detail(row)


async def delete_experiment(session: AsyncSession, exp_id: uuid.UUID) -> None:
    with tracer.start_as_current_span("experiment_service.delete") as span:
        span.set_attribute("exp_id", str(exp_id))
        if not await experiment_repo.delete(session, exp_id):
            raise HTTPException(404, f'Experiment "{exp_id}" not found')
        await session.commit()


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
            template_name=row.state["name"],
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

        filename = f"{row.state['name']}.pdf"
        expires_in = 900

        url = presign_download(row.report_r2_key, r2_cfg, filename, expires_in)
        return ReportDownloadResponse(url=url, expires_in=expires_in)
