"""Application entry point for the Experiment Manager API.

Configures the FastAPI instance with CORS middleware, database initialisation,
and all routers.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import setup
from app.routers import forms


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Runs ``setup()`` on startup to ensure required database tables exist before
    the first request is served.
    """
    setup()
    yield


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Attaches CORS middleware restricted to the origin defined in settings, then
    mounts all API routers.

    Returns:
        A fully configured :class:`fastapi.FastAPI` instance ready to serve
        requests.
    """
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(forms.router)
    return app


app = create_app()
