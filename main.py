"""Application entry point for the Experiment Manager API."""

import asyncio
from collections.abc import AsyncGenerator
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import r2_settings, report_worker_settings, settings
from app.database import async_session_factory
from app.observability.telemetry import setup_telemetry
from app.report_worker import report_worker
from app.routers import experiments, samples


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    queue: asyncio.Queue = asyncio.Queue(maxsize=report_worker_settings.queue_max_size)
    executor = ProcessPoolExecutor(max_workers=report_worker_settings.max_threads)
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


def create_app() -> FastAPI:
    app = FastAPI(title="Experiment Manager", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_telemetry(
        app, service_name="experiment-manager", otlp_endpoint=settings.otel_endpoint
    )

    app.include_router(samples.router)
    app.include_router(experiments.router)
    return app


app = create_app()
