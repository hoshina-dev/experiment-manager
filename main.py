"""Application entry point for the Experiment Manager API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import setup
from app.observability.telemetry import setup_telemetry
from app.routers import experiments, samples


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Experiment Manager", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_telemetry(app, service_name="experiment-manager", otlp_endpoint=settings.otel_endpoint)

    app.include_router(samples.router)
    app.include_router(experiments.router)
    return app


app = create_app()
