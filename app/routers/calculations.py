"""Stateless calculation router, mounted at /api/calculations."""

from fastapi import APIRouter

import app.services.calculation_service as calc_service
from app.models import CalculationDryRunRequest, CalculationDryRunResponse

router = APIRouter(prefix="/api/calculations", tags=["calculations"])


@router.post("/evaluate")
async def evaluate_calculations(
    body: CalculationDryRunRequest,
) -> CalculationDryRunResponse:
    return calc_service.dry_run(body)
