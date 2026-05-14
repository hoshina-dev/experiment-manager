from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import setup
from app.routers import forms

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup()
    yield

def create_app() -> FastAPI:
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