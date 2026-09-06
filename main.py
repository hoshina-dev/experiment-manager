"""Application entry point for the Experiment Manager API."""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.config import r2_settings, report_worker_settings, settings
from app.database import async_session_factory, engine
from app.observability.telemetry import setup_telemetry, shutdown_telemetry
from app.pdf.fonts import register_fonts
from app.pdf.r2_client import check_connection
from app.report_worker import ReportJob, report_worker
from app.repositories import experiment_repository as experiment_repo
from app.routers import calculations, experiments, health, reports, samples

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    register_fonts()
    try:
        check_connection(r2_settings)
    except Exception as exc:
        raise RuntimeError(
            f"R2/S3 is unreachable — server will not start. "
            f"Check S3_ENDPOINT and S3_BUCKET. Error: {exc}"
        ) from None
    queue: asyncio.Queue = asyncio.Queue(maxsize=report_worker_settings.queue_max_size)
    executor = ProcessPoolExecutor(
        max_workers=report_worker_settings.max_threads, initializer=register_fonts
    )

    async with async_session_factory() as session:
        orphaned = await experiment_repo.list_orphaned_reports(session)
        for exp in orphaned:
            components = await experiment_repo.get_pdf_components(
                session, uuid.UUID(exp.state["template_id"])
            )
            try:
                queue.put_nowait(
                    ReportJob(
                        exp_id=exp.id,
                        experiment_data=exp.state,
                        pdf_components=components,
                        template_name=exp.state["name"],
                    )
                )
                await experiment_repo.update_report_status(session, exp.id, "pending")
                logger.info(
                    "Requeued orphaned report job for exp_id=%s (was: %s)",
                    exp.id,
                    exp.report_status,
                )
            except asyncio.QueueFull:
                logger.warning(
                    "Queue full at recovery — marking exp_id=%s as failed", exp.id
                )
                await experiment_repo.update_report_failure(
                    session,
                    exp.id,
                    "Lost during server restart — queue full at recovery",
                )
        await session.commit()
    worker_task = asyncio.create_task(
        report_worker(queue, executor, async_session_factory, r2_settings)
    )
    _app.state.report_queue = queue
    try:
        yield
    finally:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task
        executor.shutdown(wait=False)
        try:
            shutdown_telemetry(getattr(_app.state, "otel_providers", None))
        except Exception:
            logger.exception("opentelemetry shutdown error")


def create_app() -> FastAPI:
    app = FastAPI(title="Experiment Manager", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.state.otel_providers = setup_telemetry(
        app,
        enabled=settings.otel_enabled,
        service_name=settings.otel_service_name,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        sqlalchemy_engine=engine.sync_engine,
    )

    app.include_router(samples.router)
    app.include_router(experiments.router)
    app.include_router(calculations.router)
    app.include_router(reports.router)
    app.include_router(health.router)

    @app.get("/scalar", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=app.title,
        )

    return app


app = create_app()
