"""Application entry point for the Experiment Manager API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.observability.telemetry import setup_telemetry
from app.routers import samples


def create_app() -> FastAPI:
    app = FastAPI(title="Experiment Manager", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_telemetry(app, service_name="experiment-manager", otlp_endpoint=settings.otel_endpoint)

    app.include_router(samples.router)
    return app


app = create_app()
