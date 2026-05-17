"""Business logic for samples and analysis templates, with OTEL spans on every operation."""

import app.repositories.sample_repository as repo
from app.models import AnalysesListResponse, AnalysisSummary, AnalysisTemplate, FormResponse, SamplesListResponse
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


def build_form(sample_id: str, requested_analyses: list[str]) -> FormResponse | None:
    with tracer.start_as_current_span("sample_service.build_form") as span:
        span.set_attribute("sample.id", sample_id)
        span.set_attribute("requested_analyses", ",".join(requested_analyses))

        if repo.get_sample(sample_id) is None:
            return None

        selected: list[AnalysisTemplate] = []
        for analysis_id in requested_analyses:
            template = repo.get_analysis(sample_id, analysis_id)
            if template is not None:
                selected.append(template)

        span.set_attribute("resolved_analyses", ",".join(a.id for a in selected))
        return FormResponse(sample_id=sample_id, analyses=selected)
