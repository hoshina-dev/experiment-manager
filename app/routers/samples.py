"""Router for sample catalogue resources, mounted at /api/samples."""

from fastapi import APIRouter, HTTPException

import app.services.sample_service as service
from app.models import AnalysesListResponse, SamplesListResponse

router = APIRouter(prefix="/api/samples", tags=["samples"])


@router.get("", response_model=SamplesListResponse)
def list_samples() -> SamplesListResponse:
    """Return all available sample types."""
    return service.get_samples()


@router.get("/{sample_id}/analyses", response_model=AnalysesListResponse)
def list_analyses(sample_id: str) -> AnalysesListResponse:
    """Return the analyses available for a given sample type."""
    result = service.get_analyses(sample_id)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result
