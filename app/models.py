"""Pydantic models for request validation and response serialisation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------


class SampleSummary(BaseModel):
    id: UUID
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
    id: UUID
    label: str
    description: str | None = None


class AnalysesListResponse(BaseModel):
    sample_id: UUID
    analyses: list[AnalysisSummary]


class AnalysisTemplate(BaseModel):
    id: UUID
    label: str
    description: str | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


# ---------------------------------------------------------------------------
# Experiment (create / read)
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    exp_id: UUID
    sample_id: UUID
    requested_analyses: list[UUID]


class ExperimentUpdate(BaseModel):
    sample_id: UUID
    requested_analyses: list[UUID]


class ExperimentSummary(BaseModel):
    exp_id: UUID
    sample_id: UUID
    requested_analyses: list[UUID]
    created_at: datetime


class ExperimentDetail(BaseModel):
    exp_id: UUID
    sample_id: UUID
    requested_analyses: list[UUID]
    form: list[AnalysisTemplate]
    created_at: datetime


class ExperimentsListResponse(BaseModel):
    experiments: list[ExperimentSummary]


class ExperimentFormResponse(BaseModel):
    form: list[AnalysisTemplate]
