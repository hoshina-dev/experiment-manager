"""Router for sample and analysis-form resources, mounted at /api/samples."""

from fastapi import APIRouter, HTTPException

import app.services.sample_service as service
from app.models import AnalysesListResponse, FormRequest, FormResponse, SamplesListResponse

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


@router.post("/{sample_id}/analyses/form", response_model=FormResponse)
def get_form(sample_id: str, body: FormRequest) -> FormResponse:
    """Return composed analysis templates for the requested analyses.

    The client POSTs a list of analysis IDs; the response contains one
    AnalysisTemplate per recognised ID (unknown IDs are silently ignored).
    """
    result = service.build_form(sample_id, body.requested_analyses)
    if result is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return result
