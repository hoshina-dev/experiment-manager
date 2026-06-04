"""Pydantic models for request validation and response serialisation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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
# Experiment template
# ---------------------------------------------------------------------------


class FormQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

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


class ExperimentTemplateSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class ExperimentTemplatesResponse(BaseModel):
    sample_id: UUID
    experiments: list[ExperimentTemplateSummary]


class ExperimentTemplateDetail(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    userForm: WorkerForm | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


# ---------------------------------------------------------------------------
# Sample (create / update)
# ---------------------------------------------------------------------------


class SampleCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Coal",
                "description": "Raw coal samples for proximate and calorific analysis",
            }
        }
    )

    name: str
    description: str | None = None


class SampleUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Coal",
                "description": "Raw coal samples for proximate and calorific analysis",
            }
        }
    )

    name: str
    description: str | None = None


# ---------------------------------------------------------------------------
# Analysis template (create / update)
# ---------------------------------------------------------------------------


_CALORIFIC_EXAMPLE: dict[str, Any] = {
    "name": "Calorific Value (GCV)",
    "description": "Determine gross calorific value by bomb calorimetry",
    "workerForm": {
        "title": "Calorific Value Form",
        "description": "Record bomb calorimeter readings.",
        "questions": [
            {
                "id": "sample_mass",
                "type": "number",
                "label": "Sample mass (g)",
                "required": True,
                "min": 0,
                "max": 10,
                "step": 0.001,
                "default": 1.0,
            },
            {
                "id": "water_equivalent",
                "type": "number",
                "label": "Water equivalent of calorimeter (cal/°C)",
                "required": True,
                "min": 1000,
                "max": 5000,
                "step": 0.1,
                "default": 2426.0,
            },
            {
                "id": "temp_rise",
                "type": "number",
                "label": "Temperature rise (°C)",
                "required": True,
                "min": 0,
                "max": 10,
                "step": 0.001,
                "default": 2.5,
            },
            {
                "id": "fuse_correction",
                "type": "number",
                "label": "Fuse wire correction (cal)",
                "required": False,
                "min": 0,
                "max": 100,
                "step": 0.1,
                "default": 2.0,
            },
        ],
    },
    "calculations": {
        "fuse_corr": "fuse_correction || 0",
        "gcv_cal_g": "Math.round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
        "gcv_kj_kg": "Math.round(gcv_cal_g * 4.1868)",
    },
    "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)",
}


class ExperimentTemplateCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _CALORIFIC_EXAMPLE})

    name: str
    description: str | None = None
    userForm: WorkerForm | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


class ExperimentTemplateUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _CALORIFIC_EXAMPLE})

    name: str
    description: str | None = None
    userForm: WorkerForm | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str


# ---------------------------------------------------------------------------
# Experiment (create / read)
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exp_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "sample_id": "a1b2c3d4-0002-0002-0002-000000000002",
                "template_id": "d59a46b2-28a5-4243-b894-c6ecf6309d02",
            }
        }
    )

    exp_id: UUID
    sample_id: UUID
    template_id: UUID


_EXPERIMENT_UPDATE_EXAMPLE: dict[str, Any] = {
    "example": {
        "state": {
            "id": "d59a46b2-28a5-4243-b894-c6ecf6309d02",
            "name": "Calorific Value (GCV)",
            "description": "Determine gross calorific value by bomb calorimetry",
            "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)",
            "workerForm": {
                "title": "Calorific Value Form",
                "description": "Record bomb calorimeter readings.",
                "questions": [
                    {
                        "id": "sample_mass",
                        "type": "number",
                        "label": "Sample mass (g)",
                        "required": True,
                        "min": 0,
                        "max": 10,
                        "step": 0.001,
                        "default": 1.0,
                        "value": 1.023,
                    },
                    {
                        "id": "water_equivalent",
                        "type": "number",
                        "label": "Water equivalent of calorimeter (cal/°C)",
                        "required": True,
                        "min": 1000,
                        "max": 5000,
                        "step": 0.1,
                        "default": 2426.0,
                        "value": 2426.0,
                    },
                    {
                        "id": "temp_rise",
                        "type": "number",
                        "label": "Temperature rise (°C)",
                        "required": True,
                        "min": 0,
                        "max": 10,
                        "step": 0.001,
                        "default": 2.5,
                        "value": 3.142,
                    },
                    {
                        "id": "fuse_correction",
                        "type": "number",
                        "label": "Fuse wire correction (cal)",
                        "required": False,
                        "min": 0,
                        "max": 100,
                        "step": 0.1,
                        "default": 2.0,
                        "value": 1.8,
                    },
                ],
            },
            "calculations": {
                "fuse_corr": "fuse_correction || 0",
                "gcv_cal_g": "Math.round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
                "gcv_kj_kg": "Math.round(gcv_cal_g * 4.1868)",
            },
        }
    }
}


class ExperimentUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra=_EXPERIMENT_UPDATE_EXAMPLE)

    state: dict


class ExperimentSummary(BaseModel):
    id: UUID
    sample_id: UUID
    template_id: UUID
    created_at: datetime


class ExperimentDetail(BaseModel):
    id: UUID
    sample_id: UUID
    template_id: UUID
    title: str
    description: str | None = None
    userForm: WorkerForm | None = None
    workerForm: WorkerForm
    calculations: dict[str, str]
    template: str
    report_status: str | None = None
    report_r2_key: str | None = None
    report_generated_at: datetime | None = None
    created_at: datetime


class ExperimentsListResponse(BaseModel):
    experiments: list[ExperimentSummary]
