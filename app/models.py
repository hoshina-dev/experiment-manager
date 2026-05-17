"""Pydantic models for request validation and response serialisation."""

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------


class SampleSummary(BaseModel):
    id: str
    name: str
    description: str | None = None


class SamplesListResponse(BaseModel):
    samples: list[SampleSummary]


# ---------------------------------------------------------------------------
# Analysis template
# ---------------------------------------------------------------------------


class FormQuestion(BaseModel):
    id: str
    label: str
    description: str | None = None
    required: bool = False
    type: str
    options: list[dict[str, Any]] | None = None
    placeholder: str | None = None


class WorkerForm(BaseModel):
    title: str | None = None
    description: str | None = None
    questions: list[FormQuestion]


class AnalysisSummary(BaseModel):
    id: str
    label: str
    description: str | None = None


class AnalysesListResponse(BaseModel):
    sample_id: str
    analyses: list[AnalysisSummary]


class AnalysisTemplate(BaseModel):
    id: str
    label: str
    description: str | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


# ---------------------------------------------------------------------------
# Form request / response
# ---------------------------------------------------------------------------


class FormRequest(BaseModel):
    requested_analyses: list[str]


class FormResponse(BaseModel):
    sample_id: str
    analyses: list[AnalysisTemplate]
