"""Business logic for the sample catalogue, with OTEL spans on every operation."""

import app.repositories.sample_repository as repo
from app.models import AnalysesListResponse, AnalysisSummary, SamplesListResponse
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def get_samples() -> SamplesListResponse:
    with tracer.start_as_current_span("sample_service.get_samples"):
        return SamplesListResponse(samples=repo.list_samples())


def get_analyses(sample_id: str) -> AnalysesListResponse | None:
    with tracer.start_as_current_span("sample_service.get_analyses") as span:
        span.set_attribute("sample.id", sample_id)
        if repo.get_sample(sample_id) is None:
            return None
        analyses = repo.list_analyses(sample_id)
        summaries = [AnalysisSummary(id=a.id, label=a.label, description=a.description) for a in analyses]
        return AnalysesListResponse(sample_id=sample_id, analyses=summaries)
