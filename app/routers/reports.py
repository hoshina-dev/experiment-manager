"""Report generation and download endpoints, nested under /api/experiments."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.experiment_service as service
from app.config import r2_settings
from app.database import get_db
from app.models import ReportDownloadResponse, ReportStatusResponse

router = APIRouter(prefix="/api/experiments", tags=["reports"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("/{exp_id}/report/generate", response_model=ReportStatusResponse, status_code=202)
async def generate_report(
    exp_id: uuid.UUID,
    request: Request,
    db: DbDep,
) -> ReportStatusResponse:
    queue = request.app.state.report_queue
    await service.request_report(db, exp_id, queue)
    return ReportStatusResponse(status="pending")


@router.get("/{exp_id}/report/download", response_model=ReportDownloadResponse)
async def download_report(
    exp_id: uuid.UUID,
    db: DbDep,
) -> ReportDownloadResponse:
    return await service.get_report_download_url(db, exp_id, r2_settings)
